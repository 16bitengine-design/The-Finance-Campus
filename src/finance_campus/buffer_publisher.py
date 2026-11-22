"""Safe Buffer GraphQL publisher for approved Finance Campus video packages.

The adapter schedules one post per Buffer channel. It never uploads media: video
files must already have stable, public HTTPS URLs in the production manifest.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


BUFFER_API_URL = "https://api.buffer.com"
SUPPORTED_FORMATS = {"short", "long"}


class BufferAPIError(RuntimeError):
    """Raised when Buffer rejects a request or returns an invalid response."""


class BufferClient:
    def __init__(self, api_key: str, *, timeout: int = 30) -> None:
        if not api_key.strip():
            raise ValueError("Buffer API key is required")
        self.api_key = api_key.strip()
        self.timeout = timeout

    def execute(self, query: str) -> dict[str, Any]:
        payload = json.dumps({"query": query}).encode("utf-8")
        request = urllib.request.Request(
            BUFFER_API_URL,
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "The-Finance-Campus/1.0",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:1000]
            raise BufferAPIError(f"Buffer HTTP {exc.code}: {detail}") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise BufferAPIError(f"Buffer request failed: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise BufferAPIError("Buffer returned invalid JSON") from exc

        if not isinstance(data, dict):
            raise BufferAPIError("Buffer returned an unexpected response")
        if data.get("errors"):
            messages = [
                str(item.get("message", "GraphQL error"))
                for item in data["errors"] if isinstance(item, dict)
            ]
            raise BufferAPIError("; ".join(messages) or "Buffer GraphQL request failed")
        return data.get("data") or {}

    def list_organizations(self) -> list[dict[str, Any]]:
        query = """
        query FinanceCampusOrganizations {
          account {
            organizations { id name }
          }
        }
        """
        result = self.execute(query)
        account = result.get("account") or {}
        organizations = account.get("organizations")
        if not isinstance(organizations, list):
            raise BufferAPIError("Buffer did not return an organization list")
        return organizations

    def list_channels(self, organization_id: str) -> list[dict[str, Any]]:
        query = f"""
        query FinanceCampusChannels {{
          channels(input: {{ organizationId: "{_graphql_string(organization_id)}" }}) {{
            id
            name
            service
            isDisconnected
            isQueuePaused
            isLocked
          }}
        }}
        """
        result = self.execute(query)
        channels = result.get("channels")
        if not isinstance(channels, list):
            raise BufferAPIError("Buffer did not return a channel list")
        return channels

    def list_existing_posts(self, organization_id: str, channel_id: str) -> list[dict[str, Any]]:
        query = f"""
        query FinanceCampusExistingPosts {{
          posts(first: 100, input: {{
            organizationId: "{_graphql_string(organization_id)}"
            filter: {{ status: [scheduled, sending, sent, error], channelIds: ["{_graphql_string(channel_id)}"] }}
          }}) {{
            edges {{
              node {{
                id
                text
                channelId
                status
                dueAt
                sentAt
                externalLink
                assets {{ source }}
              }}
            }}
          }}
        }}
        """
        result = self.execute(query)
        connection = result.get("posts") or {}
        edges = connection.get("edges") or []
        return [
            edge.get("node", {}) for edge in edges
            if isinstance(edge, dict) and isinstance(edge.get("node"), dict)
        ]

    def create_video_post(
        self,
        *,
        channel_id: str,
        text: str,
        video_url: str,
        platform: str,
        title: str,
        thumbnail_offset_ms: int | None = None,
    ) -> dict[str, Any]:
        metadata = ""
        asset_metadata = ""
        if platform == "youtube":
            metadata = (
                'metadata: { youtube: { title: "' + _graphql_string(title)
                + '", categoryId: "27", privacy: public, madeForKids: false, '
                "notifySubscribers: true } }"
            )
        elif platform == "tiktok" and thumbnail_offset_ms is not None:
            asset_metadata = f"metadata: {{ thumbnailOffset: {int(thumbnail_offset_ms)} }}"
        asset_meta_fragment = f", {asset_metadata}" if asset_metadata else ""
        metadata_fragment = f", {metadata}" if metadata else ""
        query = f"""
        mutation FinanceCampusCreatePost {{
          createPost(input: {{
            text: "{_graphql_string(text)}"
            channelId: "{_graphql_string(channel_id)}"
            schedulingType: automatic
            mode: addToQueue
            assets: [{{ video: {{ url: "{_graphql_string(video_url)}"{asset_meta_fragment} }} }}]
            {metadata_fragment}
          }}) {{
            ... on PostActionSuccess {{
              post {{ id status dueAt channelId text }}
            }}
            ... on MutationError {{ message }}
          }}
        }}
        """
        result = self.execute(query)
        outcome = result.get("createPost")
        if not isinstance(outcome, dict):
            raise BufferAPIError("Buffer returned no createPost result")
        if outcome.get("message"):
            raise BufferAPIError(str(outcome["message"]))
        post = outcome.get("post")
        if not isinstance(post, dict) or not post.get("id"):
            raise BufferAPIError("Buffer did not confirm that the post was created")
        return post


def verify_public_video_url(url: str, *, timeout: int = 20) -> None:
    """Confirm Buffer can fetch a direct public MP4 URL without credentials."""
    request = urllib.request.Request(
        url,
        headers={"Range": "bytes=0-0", "User-Agent": "The-Finance-Campus/1.0"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = getattr(response, "status", 200)
            content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().casefold()
            if status not in {200, 206}:
                raise ValueError(f"Public video host returned HTTP {status}")
            if content_type not in {"video/mp4", "application/octet-stream", "binary/octet-stream"}:
                raise ValueError(f"Public video URL has unexpected content type: {content_type or 'missing'}")
            if response.headers.get("Content-Length") == "0":
                raise ValueError("Public video URL points to an empty file")
    except urllib.error.HTTPError as exc:
        raise ValueError(f"Buffer cannot fetch public video URL (HTTP {exc.code})") from exc
    except urllib.error.URLError as exc:
        raise ValueError(f"Buffer cannot reach public video URL: {exc}") from exc



def verify_public_post_url(url: str, *, timeout: int = 20) -> bool:
    """Verify a public YouTube/TikTok post URL without using authenticated APIs."""
    from urllib.parse import urlparse

    parsed = urlparse(url)
    host = (parsed.hostname or "").casefold()
    allowed_hosts = {
        "youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be",
        "tiktok.com", "www.tiktok.com", "vm.tiktok.com",
    }
    if parsed.scheme != "https" or host not in allowed_hosts:
        return False
    request = urllib.request.Request(
        url,
        headers={"Range": "bytes=0-0", "User-Agent": "Mozilla/5.0 The-Finance-Campus/1.0"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return 200 <= getattr(response, "status", 200) < 400
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        return False


def monitor_publications(
    *,
    client: BufferClient,
    organization_id: str,
    channel_ids: list[str],
    ledger_path: str | Path,
) -> dict[str, Any]:
    """Reconcile Buffer post states and verify public destination URLs for sent posts."""
    from datetime import datetime, timezone

    ledger = _load_ledger(ledger_path)
    indexed: dict[str, dict[str, Any]] = {}
    for channel_id in channel_ids:
        for post in client.list_existing_posts(organization_id, channel_id):
            post_id = post.get("id")
            if post_id:
                indexed[str(post_id)] = post

    results: list[dict[str, Any]] = []
    checked_at = datetime.now(timezone.utc).isoformat()
    for ledger_key, record in ledger["posts"].items():
        post_id = record.get("buffer_post_id")
        if not post_id:
            continue
        post = indexed.get(str(post_id))
        if not post:
            results.append({"ledger_key": ledger_key, "status": "not_returned_by_buffer"})
            continue
        buffer_status = str(post.get("status", "unknown")).casefold()
        record["buffer_status"] = buffer_status
        record["last_checked_at"] = checked_at
        if buffer_status == "sent":
            external_url = post.get("externalLink")
            record["sent_at"] = post.get("sentAt")
            record["external_url"] = external_url
            if isinstance(external_url, str) and verify_public_post_url(external_url):
                record["status"] = "publicly_accessible_verified"
                record["public_availability_verified"] = True
                results.append({
                    "ledger_key": ledger_key,
                    "status": "publicly_accessible_verified",
                    "external_url": external_url,
                })
            else:
                record["status"] = "sent_awaiting_public_verification"
                record["public_availability_verified"] = False
                results.append({
                    "ledger_key": ledger_key,
                    "status": "sent_awaiting_public_verification",
                })
        elif buffer_status == "error":
            record["status"] = "failed"
            record["public_availability_verified"] = False
            results.append({"ledger_key": ledger_key, "status": "failed"})
        else:
            record["status"] = buffer_status
            results.append({"ledger_key": ledger_key, "status": buffer_status})

    _save_ledger(ledger_path, ledger)
    return {
        "mode": "monitor",
        "checked_at": checked_at,
        "tracked_posts": len(ledger["posts"]),
        "results": results,
        "ledger_path": str(ledger_path),
    }


def _graphql_string(value: str) -> str:
    return json.dumps(str(value), ensure_ascii=False)[1:-1]


def _load_json(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"Expected a JSON object in {path}")
    return payload


def validate_publish_package(package_dir: str | Path) -> dict[str, Any]:
    """Fail closed unless a package has passed all editorial and visual gates."""
    root = Path(package_dir)
    manifest = _load_json(root / "production-manifest.json")
    metadata = _load_json(root / "post-metadata.json")

    if manifest.get("status") != "quality_approved":
        raise ValueError("Package is not quality_approved")
    if manifest.get("technical_quality_approved") is not True:
        raise ValueError("Technical quality approval is missing")
    if manifest.get("human_visual_review_passed") is not True:
        raise ValueError("Human visual review has not passed")
    if manifest.get("publication_approved") is not True:
        raise ValueError("Publication approval is missing")
    if manifest.get("video_format") not in SUPPORTED_FORMATS:
        raise ValueError("Manifest has an unsupported video format")

    stages = manifest.get("stages")
    if not isinstance(stages, dict):
        raise TypeError("Manifest stages must be an object")
    required_stages = (
        "script_validated", "script_approved", "kokoro_narration_generated",
        "captions_validated", "video_rendered", "media_streams_verified",
        "final_video_qc_passed",
    )
    missing = [stage for stage in required_stages if stages.get(stage) is not True]
    if missing:
        raise ValueError("Required production stages did not pass: " + ", ".join(missing))

    artifacts = manifest.get("artifacts") or {}
    thumbnail_path = artifacts.get("thumbnail")
    if not isinstance(thumbnail_path, str):
        raise TypeError("Manifest artifacts.thumbnail must be a file path")
    thumbnail = Path(thumbnail_path)
    if not thumbnail.is_absolute():
        thumbnail = root / thumbnail
    if not thumbnail.is_file() or thumbnail.stat().st_size < 1024:
        raise ValueError("Branded thumbnail is missing or implausibly small")

    public_media = manifest.get("public_media") or {}
    video_url = public_media.get("video_url")
    if not isinstance(video_url, str) or not video_url.startswith("https://"):
        raise ValueError("A stable public HTTPS video_url is required in manifest.public_media")
    if public_media.get("thumbnail_frame_embedded") is not True:
        raise ValueError(
            "A branded thumbnail frame must be embedded in the video for Buffer's "
            "TikTok thumbnail-frame selection"
        )
    thumbnail_offset_ms = public_media.get("thumbnail_offset_ms")
    if manifest["video_format"] == "short" and (
        not isinstance(thumbnail_offset_ms, int) or thumbnail_offset_ms < 0
    ):
        raise ValueError("Short-form packages require a valid thumbnail_offset_ms")

    platforms = metadata.get("platforms") or {}
    youtube = platforms.get("youtube") or {}
    if not isinstance(youtube.get("description"), str) or not youtube["description"].strip():
        raise ValueError("YouTube description is missing")
    validation = metadata.get("validation") or {}
    if validation.get("youtube_disclaimer_present") is not True:
        raise ValueError("YouTube description disclaimer validation failed")
    if metadata.get("title") != manifest.get("title"):
        raise ValueError("Metadata title does not match the production manifest")

    tiktok = platforms.get("tiktok")
    if manifest["video_format"] == "short":
        if not isinstance(tiktok, dict) or not isinstance(tiktok.get("caption"), str):
            raise ValueError("TikTok caption is missing for a short-form package")
        if validation.get("tiktok_disclaimer_present") is not True:
            raise ValueError("TikTok caption disclaimer validation failed")
        if validation.get("platform_copy_is_distinct") is not True:
            raise ValueError("Platform-specific copy must be distinct")
    return {
        "manifest": manifest,
        "metadata": metadata,
        "video_url": video_url,
        "thumbnail_offset_ms": thumbnail_offset_ms,
        "thumbnail_path": str(thumbnail),
    }


def _load_ledger(path: str | Path) -> dict[str, Any]:
    target = Path(path)
    if not target.exists():
        return {"version": 1, "posts": {}}
    payload = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("posts"), dict):
        raise TypeError("Publishing ledger must contain an object with a posts object")
    return payload


def _save_ledger(path: str | Path, ledger: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(target)


def schedule_package(
    package_dir: str | Path,
    *,
    client: BufferClient,
    organization_id: str,
    youtube_channel_id: str,
    tiktok_channel_id: str | None,
    ledger_path: str | Path,
    live: bool = False,
) -> dict[str, Any]:
    """Validate and queue one approved package; dry-run is the default."""
    package = validate_publish_package(package_dir)
    manifest = package["manifest"]
    metadata = package["metadata"]
    video_format = manifest["video_format"]
    destinations = [("youtube", youtube_channel_id)]
    if video_format == "short":
        if not tiktok_channel_id:
            raise ValueError("TikTok channel ID is required for short-form publishing")
        destinations.append(("tiktok", tiktok_channel_id))

    ledger = _load_ledger(ledger_path)
    video_key = str(manifest.get("video_id") or manifest.get("title"))
    if not video_key.strip():
        raise ValueError("A stable video_id or title is required")
    results: list[dict[str, Any]] = []

    if live:
        verify_public_video_url(package["video_url"])

    channels = client.list_channels(organization_id)
    channel_by_id = {
        item.get("id"): item for item in channels if isinstance(item, dict)
    }
    for platform, channel_id in destinations:
        channel = channel_by_id.get(channel_id)
        if not channel:
            raise ValueError(f"Configured Buffer {platform} channel was not found")
        if channel.get("isDisconnected") is True:
            raise ValueError(f"Configured Buffer {platform} channel is disconnected")
        if channel.get("isQueuePaused") is True:
            raise ValueError(f"Configured Buffer {platform} queue is paused")
        if channel.get("isLocked") is True:
            raise ValueError(f"Configured Buffer {platform} channel is locked")
        if str(channel.get("service", "")).casefold() != platform:
            raise ValueError(
                f"Configured {platform} channel points to Buffer service "
                f"{channel.get('service')!r}"
            )
        ledger_key = f"{video_key}:{platform}:{channel_id}"
        if ledger_key in ledger["posts"]:
            results.append({
                "platform": platform,
                "status": "already_recorded",
                "buffer_post_id": ledger["posts"][ledger_key].get("buffer_post_id"),
            })
            continue

        copy = metadata["platforms"][platform]
        text = copy["description"] if platform == "youtube" else copy["caption"]
        # Detect a prior successful API write if the runner lost its ledger update.
        duplicate = next((
            post for post in client.list_existing_posts(organization_id, channel_id)
            if post.get("status") in {"scheduled", "sending", "sent"}
            and post.get("text") == text
            and any(asset.get("source") == package["video_url"] for asset in post.get("assets", []))
        ), None)
        if duplicate:
            public_media = manifest.get("public_media") or {}
            record = {
                "buffer_post_id": duplicate.get("id"),
                "status": str(duplicate.get("status", "scheduled")),
                "due_at": duplicate.get("dueAt"),
                "recovered_existing_post": True,
                "video_id": video_key,
                "title": manifest.get("title"),
                "platform": platform,
                "thumbnail_url": public_media.get("thumbnail_url"),
            }
            ledger["posts"][ledger_key] = record
            _save_ledger(ledger_path, ledger)
            results.append({**record, "platform": platform, "status": "already_in_buffer"})
            continue

        if not live:
            results.append({
                "platform": platform,
                "status": "dry_run_validated",
                "channel_name": channel.get("name"),
                "title": manifest["title"],
                "video_url": package["video_url"],
            })
            continue

        post = client.create_video_post(
            channel_id=channel_id,
            text=text,
            video_url=package["video_url"],
            platform=platform,
            title=manifest["title"],
            thumbnail_offset_ms=(
                package["thumbnail_offset_ms"] if platform == "tiktok" else None
            ),
        )
        public_media = manifest.get("public_media") or {}
        record = {
            "buffer_post_id": post["id"],
            "status": post.get("status", "scheduled"),
            "due_at": post.get("dueAt"),
            "recovered_existing_post": False,
            "video_id": video_key,
            "title": manifest.get("title"),
            "platform": platform,
            "thumbnail_url": public_media.get("thumbnail_url"),
        }
        ledger["posts"][ledger_key] = record
        _save_ledger(ledger_path, ledger)
        results.append({**record, "platform": platform, "status": "scheduled_in_buffer", "buffer_status": record["status"]})

    return {
        "video_id": video_key,
        "title": manifest["title"],
        "mode": "live" if live else "dry_run",
        "results": results,
        "ledger_path": str(ledger_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate or schedule a Finance Campus package in Buffer")
    parser.add_argument(
        "package_dir", nargs="?",
        help="Directory containing production manifest and post metadata",
    )
    parser.add_argument(
        "--list-account", action="store_true",
        help="List Buffer organizations and connected channel IDs",
    )
    parser.add_argument("--live", action="store_true", help="Actually create scheduled Buffer posts")
    parser.add_argument("--monitor", action="store_true", help="Reconcile Buffer post states and verify public post URLs")
    parser.add_argument("--ledger", default="production/buffer-publishing-ledger.json")
    args = parser.parse_args()

    try:
        api_key = os.environ.get("BUFFER_API_KEY", "")
        client = BufferClient(api_key)
        if args.list_account:
            organizations = client.list_organizations()
            result = []
            for organization in organizations:
                org_id = organization.get("id")
                channels = client.list_channels(org_id) if org_id else []
                result.append({
                    "organization": organization,
                    "channels": channels,
                })
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        if args.monitor:
            organization_id = os.environ.get("BUFFER_ORGANIZATION_ID", "")
            channel_ids = [
                value for value in (
                    os.environ.get("BUFFER_YOUTUBE_CHANNEL_ID", ""),
                    os.environ.get("BUFFER_TIKTOK_CHANNEL_ID", ""),
                ) if value
            ]
            if not organization_id or not channel_ids:
                raise ValueError("BUFFER_ORGANIZATION_ID and at least one Buffer channel ID are required")
            result = monitor_publications(
                client=client,
                organization_id=organization_id,
                channel_ids=channel_ids,
                ledger_path=args.ledger,
            )
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        if not args.package_dir:
            parser.error("package_dir is required unless --list-account is used")
        organization_id = os.environ.get("BUFFER_ORGANIZATION_ID", "")
        youtube_channel_id = os.environ.get("BUFFER_YOUTUBE_CHANNEL_ID", "")
        tiktok_channel_id = os.environ.get("BUFFER_TIKTOK_CHANNEL_ID")
        if not organization_id or not youtube_channel_id:
            raise ValueError("BUFFER_ORGANIZATION_ID and BUFFER_YOUTUBE_CHANNEL_ID are required")
        if args.live and os.environ.get("BUFFER_PUBLISH_ENABLED", "").casefold() != "true":
            raise ValueError("Live scheduling is locked; set BUFFER_PUBLISH_ENABLED=true only after approval")
        result = schedule_package(
            args.package_dir,
            client=client,
            organization_id=organization_id,
            youtube_channel_id=youtube_channel_id,
            tiktok_channel_id=tiktok_channel_id,
            ledger_path=args.ledger,
            live=args.live,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"BUFFER PUBLISHING REJECTED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
