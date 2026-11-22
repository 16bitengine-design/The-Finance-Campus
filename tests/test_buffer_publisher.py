import json
from pathlib import Path

import pytest

from finance_campus.buffer_publisher import (
    BufferAPIError,
    schedule_package,
    validate_publish_package,
)


class FakeBuffer:
    def __init__(self):
        self.created = []
        self.existing = []

    def list_channels(self, organization_id):
        return [
            {"id": "yt-123", "name": "The Finance Campus YouTube", "service": "youtube"},
            {"id": "tt-456", "name": "The Finance Campus TikTok", "service": "tiktok"},
        ]

    def list_existing_posts(self, organization_id, channel_id):
        return [item for item in self.existing if item["channelId"] == channel_id]

    def create_video_post(self, **kwargs):
        post = {
            "id": f"post-{len(self.created) + 1}",
            "status": "scheduled",
            "dueAt": "2026-11-23T06:00:00Z",
            "channelId": kwargs["channel_id"],
        }
        self.created.append((kwargs, post))
        return post


def make_package(root: Path, *, status="quality_approved"):
    root.mkdir(parents=True, exist_ok=True)
    (root / "brand-thumbnail.jpg").write_bytes(b"x" * 2048)
    manifest = {
        "video_id": "TFC-TEST-001",
        "title": "How to Build an Emergency Fund",
        "status": status,
        "technical_quality_approved": True,
        "human_visual_review_passed": True,
        "publication_approved": True,
        "video_format": "short",
        "stages": {
            "script_validated": True,
            "script_approved": True,
            "kokoro_narration_generated": True,
            "captions_validated": True,
            "video_rendered": True,
            "media_streams_verified": True,
            "final_video_qc_passed": True,
        },
        "artifacts": {"thumbnail": "brand-thumbnail.jpg"},
        "public_media": {
            "video_url": "https://cdn.example.test/finance-campus/test.mp4",
            "thumbnail_frame_embedded": True,
            "thumbnail_offset_ms": 500,
        },
    }
    metadata = {
        "title": manifest["title"],
        "platforms": {
            "youtube": {"description": "Full YouTube description with educational disclaimer."},
            "tiktok": {"caption": "Distinct TikTok caption with educational disclaimer."},
        },
        "validation": {
            "youtube_disclaimer_present": True,
            "tiktok_disclaimer_present": True,
            "platform_copy_is_distinct": True,
        },
    }
    (root / "production-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (root / "post-metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    return root


def test_rejects_package_awaiting_visual_review(tmp_path):
    package = make_package(tmp_path / "package", status="awaiting_visual_review")
    with pytest.raises(ValueError, match="quality_approved"):
        validate_publish_package(package)


def test_dry_run_validates_both_destinations_without_creating_posts(tmp_path):
    package = make_package(tmp_path / "package")
    client = FakeBuffer()
    result = schedule_package(
        package,
        client=client,
        organization_id="org-1",
        youtube_channel_id="yt-123",
        tiktok_channel_id="tt-456",
        ledger_path=tmp_path / "ledger.json",
        live=False,
    )
    assert result["mode"] == "dry_run"
    assert [item["platform"] for item in result["results"]] == ["youtube", "tiktok"]
    assert all(item["status"] == "dry_run_validated" for item in result["results"])
    assert client.created == []


def test_live_scheduling_creates_one_post_per_platform_and_records_ledger(tmp_path):
    package = make_package(tmp_path / "package")
    ledger = tmp_path / "ledger.json"
    result = schedule_package(
        package,
        client=FakeBuffer(),
        organization_id="org-1",
        youtube_channel_id="yt-123",
        tiktok_channel_id="tt-456",
        ledger_path=ledger,
        live=True,
    )
    assert all(item["status"] == "scheduled_in_buffer" for item in result["results"])
    saved = json.loads(ledger.read_text(encoding="utf-8"))
    assert len(saved["posts"]) == 2


def test_ledger_prevents_duplicate_scheduling(tmp_path):
    package = make_package(tmp_path / "package")
    ledger = tmp_path / "ledger.json"
    first_client = FakeBuffer()
    schedule_package(
        package, client=first_client, organization_id="org-1",
        youtube_channel_id="yt-123", tiktok_channel_id="tt-456",
        ledger_path=ledger, live=True,
    )
    second_client = FakeBuffer()
    result = schedule_package(
        package, client=second_client, organization_id="org-1",
        youtube_channel_id="yt-123", tiktok_channel_id="tt-456",
        ledger_path=ledger, live=True,
    )
    assert all(item["status"] == "already_recorded" for item in result["results"])
    assert second_client.created == []


def test_wrong_channel_service_is_rejected(tmp_path):
    package = make_package(tmp_path / "package")

    class WrongService(FakeBuffer):
        def list_channels(self, organization_id):
            return [{"id": "yt-123", "name": "Wrong", "service": "tiktok"}]

    with pytest.raises(ValueError, match="service"):
        schedule_package(
            package, client=WrongService(), organization_id="org-1",
            youtube_channel_id="yt-123", tiktok_channel_id="tt-456",
            ledger_path=tmp_path / "ledger.json", live=False,
        )
