"""Headless Blender backend for authored 3D Finance Campus scenes."""
from __future__ import annotations
import shutil
import subprocess
from pathlib import Path
from typing import Any

class BlenderRenderError(RuntimeError):
    """Raised when a Blender project cannot be rendered."""

def render_blender_project(project_path: str | Path, output_path: str | Path, *,
    width: int = 1080, height: int = 1920, fps: int = 30, blender: str = "blender",
    engine: str = "BLENDER_EEVEE_NEXT") -> dict[str, Any]:
    """Render an authored Blender animation in background mode to MP4."""
    project = Path(project_path).resolve()
    destination = Path(output_path).resolve()
    if not project.is_file() or project.suffix.lower() != ".blend":
        raise BlenderRenderError("project_path must point to an existing .blend file")
    executable = shutil.which(blender)
    if not executable:
        raise BlenderRenderError("Blender was not found. Install Blender or configure its executable; 3D will not fall back to 2D.")
    if min(width, height, fps) <= 0:
        raise ValueError("width, height and fps must be positive integers")
    destination.parent.mkdir(parents=True, exist_ok=True)
    settings_script = destination.parent / f".{destination.stem}_finance_campus_blender.py"
    settings_script.write_text(
        "import bpy\nscene = bpy.context.scene\n"
        f"scene.render.resolution_x = {int(width)}\nscene.render.resolution_y = {int(height)}\n"
        "scene.render.resolution_percentage = 100\n"
        f"scene.render.fps = {int(fps)}\nscene.render.engine = {engine!r}\n"
        "scene.render.image_settings.file_format = 'FFMPEG'\n"
        "scene.render.ffmpeg.format = 'MPEG4'\nscene.render.ffmpeg.codec = 'H264'\n"
        "scene.render.ffmpeg.constant_rate_factor = 'HIGH'\n"
        f"scene.render.filepath = {str(destination)!r}\n"
        "bpy.ops.render.render(animation=True)\n", encoding="utf-8")
    result = subprocess.run([executable, "-b", str(project), "--python", str(settings_script)],
        capture_output=True, text=True, check=False)
    settings_script.unlink(missing_ok=True)
    if result.returncode != 0 or not destination.is_file() or destination.stat().st_size == 0:
        raise BlenderRenderError("Blender render failed: " + (result.stderr or result.stdout)[-4000:])
    return {"passed": True, "renderer": "blender_3d", "width": width, "height": height,
        "fps": fps, "engine": engine, "output": str(destination)}
