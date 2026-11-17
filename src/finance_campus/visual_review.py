"""Generate a human-review contact sheet from the actual final encoded MP4."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw


def create_visual_review_sheet(
    video_path: str | Path,
    output_path: str | Path,
    *,
    ffmpeg: str = "ffmpeg",
    sample_count: int = 8,
) -> dict[str, object]:
    """Extract evenly spaced frames and assemble a readable review sheet.

    The sheet is evidence for human inspection, not an automatic semantic pass.
    """
    source, destination = Path(video_path), Path(output_path)
    executable = shutil.which(ffmpeg)
    if not executable:
        raise RuntimeError("FFmpeg is required to create the visual review sheet")
    if not source.is_file() or sample_count < 4:
        raise ValueError("A valid video and at least four review samples are required")

    probe = subprocess.run(
        [
            shutil.which("ffprobe") or "ffprobe", "-v", "error",
            "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
            str(source),
        ],
        capture_output=True, text=True, check=False,
    )
    if probe.returncode:
        raise RuntimeError("Could not determine video duration for visual review")
    duration = float(probe.stdout.strip())
    if duration <= 0:
        raise RuntimeError("Video duration must be positive")

    scratch = destination.parent / (destination.stem + "_frames")
    scratch.mkdir(parents=True, exist_ok=True)
    frames: list[Path] = []
    try:
        for index in range(sample_count):
            # Avoid the first/last encoded frame and sample the complete timeline.
            timestamp = duration * (index + 0.5) / sample_count
            frame = scratch / f"review_{index + 1:02d}.jpg"
            result = subprocess.run(
                [
                    executable, "-hide_banner", "-loglevel", "error", "-y",
                    "-ss", f"{timestamp:.3f}", "-i", str(source),
                    "-frames:v", "1", "-q:v", "3", str(frame),
                ],
                capture_output=True, text=True, check=False,
            )
            if result.returncode or not frame.is_file():
                raise RuntimeError(f"Could not extract visual review frame {index + 1}")
            frames.append(frame)

        columns = 2 if sample_count <= 6 else 3
        rows = (sample_count + columns - 1) // columns
        tile_width, tile_height = 360, 640
        sheet = Image.new("RGB", (columns * tile_width, rows * (tile_height + 28)), "white")
        draw = ImageDraw.Draw(sheet)
        for index, frame_path in enumerate(frames):
            with Image.open(frame_path) as source_image:
                image = source_image.convert("RGB")
                image.thumbnail((tile_width - 12, tile_height - 12))
            tile = Image.new("RGB", (tile_width, tile_height), "white")
            tile.paste(image, ((tile_width - image.width) // 2, (tile_height - image.height) // 2))
            x, y = (index % columns) * tile_width, (index // columns) * (tile_height + 28)
            sheet.paste(tile, (x, y))
            draw.text((x + 8, y + tile_height + 5), f"Sample {index + 1} — {duration * (index + 0.5) / sample_count:.1f}s", fill="#102B55")
        destination.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(destination, quality=92)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    if not destination.is_file() or destination.stat().st_size < 5_000:
        raise RuntimeError("Visual review contact sheet was not created correctly")
    return {
        "path": str(destination),
        "sample_count": sample_count,
        "duration_seconds": round(duration, 3),
        "human_review_required": True,
    }
