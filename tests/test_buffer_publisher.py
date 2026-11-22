from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from finance_campus.buffer_publisher import (
    _graphql_string,
    monitor_publications,
    schedule_package,
    validate_publish_package,
)


class FakeBufferClient:
    def __init__(self, channels: list[dict[str, Any]]):
        self.channels = channels
        self.created: list[dict[str, Any]] = []

    def list_channels(self, organization_id: str) -> list[dict[str, Any]]:
        assert organization_id == "org-1"
        return self.channels

    def list_existing_posts(self, organization_id: str, channel_id: str) -> list[dict[str, Any]]:
        return []

    def create_video_post(self, **kwargs: Any) -> dict[str, Any]:
        self.created.append(kwargs)
        return {
            "id": f"post-{len(self.created)}",
            "status": "scheduled",
            "dueAt": "2026-11-23T06:00:00Z",
        }


def _package(root: Path, *, video_format: str = "short") -> Path:
    root.mkdir(parents=True, exist_ok=True)
    thumbnail = root / "thumbnail-youtube.jpg"
    thumbnail.write_bytes(b"\xff\xd8" + b"x" * 2048)
    stages = {
        "script_validated": True,
        "script_approved": True,
        "kokoro_narration_generated": True,
        "captions_validated": True,
        "video_rendered": True,
        "media_streams_verified": True,
        "final_video_qc_passed": True,
    }
    manifest = {
        "video_id": "fc-test-video",
        "title": "A Practical Finance Lesson",
        "status": "quality_approved",
        "technical_quality_approved": True,
        "human_visual_review_passed": True,
        "publication_approved": True,
        "video_format": video_format,
        "stages": stages,
        "artifacts": {"thumbnail": "thumbnail-youtube.jpg"},
        "public_media": {
            "video_url": "https://media.example.test/finance-campus-video.mp4",
            "thumbnail_frame_embedded": True,
            "thumbnail_offset_ms": 600,
        },
    }
    metadata = {
        "title": manifest["title"],
        "platforms": {
            "youtube": {"description": "YouTube educational description and disclaimer."},
            "tiktok": {"caption": "TikTok educational caption and disclaimer."},
        },
        "validation": {
            "youtube_disclaimer_present": True,
            "tiktok_disclaimer_present": True,
            "platform_copy_is_distinct": True,
        },
    }
    (root / "production-manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    (root / "post-metadata.json").write_text(
        json.dumps(metadata), encoding="utf-8"
    )
    return root


def _channels() -> list[dict[str, Any]]:
    return [
        {
            "id": "youtube-1",
            "name": "The Finance Campus YouTube",
            "service": "youtube",
            "isDisconnected": False,
            "isQueuePaused": False,
            "isLocked": False,
        },
        {
            "id": "tiktok-1",
            "name": "The Finance Campus TikTok",
            "service": "tiktok",
            "isDisconnected": False,
            "isQueuePaused": False,
            "isLocked": False,
        },
    ]


def test_graphql_string_escapes_quotes_and_newlines() -> None:
    assert _graphql_string('A "quoted" title\\nnext') == 'A \\"quoted\\" title\\\\nnext'


def test_package_rejects_missing_public_video_url(tmp_path: Path) -> None:
    root = _package(tmp_path / "package")
    manifest_path = root / "production-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["public_media"].pop("video_url")
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="stable public HTTPS video_url"):
        validate_publish_package(root)


def test_short_package_dry_run_targets_both_platforms(tmp_path: Path) -> None:
    package = _package(tmp_path / "package")
    client = FakeBufferClient(_channels())

    result = schedule_package(
        package,
        client=client,  # type: ignore[arg-type]
        organization_id="org-1",
        youtube_channel_id="youtube-1",
        tiktok_channel_id="tiktok-1",
        ledger_path=tmp_path / "ledger.json",
        live=False,
    )

    assert result["mode"] == "dry_run"
    assert [item["platform"] for item in result["results"]] == ["youtube", "tiktok"]
    assert all(item["status"] == "dry_run_validated" for item in result["results"])
    assert client.created == []
    assert not (tmp_path / "ledger.json").exists()


def test_long_form_package_only_targets_youtube(tmp_path: Path) -> None:
    package = _package(tmp_path / "package", video_format="long")
    client = FakeBufferClient(_channels())

    result = schedule_package(
        package,
        client=client,  # type: ignore[arg-type]
        organization_id="org-1",
        youtube_channel_id="youtube-1",
        tiktok_channel_id=None,
        ledger_path=tmp_path / "ledger.json",
        live=False,
    )

    assert [item["platform"] for item in result["results"]] == ["youtube"]


def test_existing_ledger_prevents_duplicate_scheduling(tmp_path: Path) -> None:
    package = _package(tmp_path / "package")
    ledger = tmp_path / "ledger.json"
    ledger.write_text(
        json.dumps({
            "version": 1,
            "posts": {
                "fc-test-video:youtube:youtube-1": {
                    "buffer_post_id": "existing-post",
                    "status": "scheduled",
                }
            },
        }),
        encoding="utf-8",
    )
    client = FakeBufferClient(_channels())

    result = schedule_package(
        package,
        client=client,  # type: ignore[arg-type]
        organization_id="org-1",
        youtube_channel_id="youtube-1",
        tiktok_channel_id="tiktok-1",
        ledger_path=ledger,
        live=False,
    )

    assert result["results"][0]["status"] == "already_recorded"
    assert result["results"][0]["buffer_post_id"] == "existing-post"
    assert result["results"][1]["status"] == "dry_run_validated"



def test_monitor_marks_sent_post_only_after_public_url_verification(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import finance_campus.buffer_publisher as publisher

    monkeypatch.setattr(publisher, "verify_public_post_url", lambda url: url.startswith("https://www.youtube.com/"))

    ledger = tmp_path / "ledger.json"
    ledger.write_text(
        json.dumps({
            "version": 1,
            "posts": {
                "fc-video:youtube:youtube-1": {
                    "buffer_post_id": "sent-post",
                    "status": "scheduled",
                },
                "fc-video:tiktok:tiktok-1": {
                    "buffer_post_id": "queued-post",
                    "status": "scheduled",
                },
            },
        }),
        encoding="utf-8",
    )

    class MonitorClient(FakeBufferClient):
        def list_existing_posts(self, organization_id: str, channel_id: str) -> list[dict[str, Any]]:
            if channel_id == "youtube-1":
                return [{
                    "id": "sent-post",
                    "status": "sent",
                    "sentAt": "2026-11-22T12:00:00Z",
                    "externalLink": "https://www.youtube.com/watch?v=public123",
                }]
            return [{
                "id": "queued-post",
                "status": "scheduled",
                "externalLink": None,
            }]

    result = monitor_publications(
        client=MonitorClient(_channels()),  # type: ignore[arg-type]
        organization_id="org-1",
        channel_ids=["youtube-1", "tiktok-1"],
        ledger_path=ledger,
    )

    saved = json.loads(ledger.read_text(encoding="utf-8"))
    assert saved["posts"]["fc-video:youtube:youtube-1"]["status"] == "publicly_accessible_verified"
    assert saved["posts"]["fc-video:youtube:youtube-1"]["public_availability_verified"] is True
    assert saved["posts"]["fc-video:tiktok:tiktok-1"]["status"] == "scheduled"
    assert result["tracked_posts"] == 2
