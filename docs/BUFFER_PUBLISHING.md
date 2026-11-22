# Buffer scheduling and publishing

## Design

Buffer is the scheduling and publishing layer for The Finance Campus. GitHub Actions and the Python production pipeline prepare validated media packages; the Buffer GraphQL API creates one scheduled post per connected channel.

The integration uses Buffer's current GraphQL API at `https://api.buffer.com`, authenticated with a personal API key in the `Authorization: Bearer` header. Do not use the retired Buffer REST API.

## Current safety state

Publishing is deliberately locked until the visual production standard is approved and the media-hosting and Buffer account configuration are verified.

The publisher fails closed unless all of the following are true:

- Manifest status is `quality_approved`.
- Technical QC passed.
- Human visual review passed.
- Explicit publication approval is present.
- Script, narration, captions, rendered video and final video QC stages passed.
- A branded thumbnail file exists.
- The video is hosted at a stable public HTTPS URL.
- A branded thumbnail frame is embedded in the video for TikTok's thumbnail-frame selection.
- Platform-specific descriptions/captions exist and disclaimer validation passed.
- The correct Buffer channel IDs are configured.

The CLI defaults to dry-run. Actual scheduling requires `--live` and `BUFFER_PUBLISH_ENABLED=true`. Do not set that variable until the owner approves the final sample and end-to-end checks have passed.

## Integration status and remaining prerequisites

The guarded Buffer adapter and scheduling workflow are implemented for both YouTube and TikTok. The production workflow is not yet connected to scheduling, and no Buffer account has been connected or live post tested.

A separate workflow, `.github/workflows/buffer-media-hosting.yml`, now provides a guarded GitHub Releases media-hosting stage. It downloads a production artifact, requires an explicit manual approval for public hosting, checks technical QC and visual-review evidence, creates a unique public GitHub Release, verifies the public assets, writes their stable URLs into the manifest, and uploads a hosted package artifact for a later Buffer dry-run.

The media-hosting workflow is intentionally not a publishing approval. It marks human visual review as passed only after the explicit `approve_public_hosting` selection. It does not set `publication_approved`; the Buffer publisher therefore remains blocked from live scheduling until a separate publishing approval is explicitly recorded.

The current production renderer does not yet generate the required branded thumbnail artifact or embed the TikTok cover frame. It also does not yet emit a production-package artifact in the exact structure required by the hosting workflow. Consequently, the new hosting workflow is a guarded component, not yet an end-to-end tested path. It must reject packages missing those assets or approval evidence.

The stable video URL format is:
`https://github.com/OWNER/REPOSITORY/releases/download/RELEASE_TAG/finance-campus-video.mp4`

GitHub Releases are suitable only while the repository is public and the asset size remains within GitHub's release-asset limits. The workflow checks repository visibility and anonymous URL retrieval before recording the URLs. GitHub Actions artifacts remain temporary and are used only to pass packages between jobs, never as public Buffer media URLs.

## Buffer API requirements

Create a personal API key in Buffer Settings → API and store it only in GitHub Actions Secrets as `BUFFER_API_KEY`.

Then run the **Buffer scheduling** GitHub Actions workflow with mode `discover`. It will print your Buffer organization and connected channel IDs without creating any posts. Copy the correct organization ID and the YouTube/TikTok channel IDs into the matching repository secrets below.

Configure these repository secrets:

- `BUFFER_API_KEY`
- `BUFFER_ORGANIZATION_ID`
- `BUFFER_YOUTUBE_CHANNEL_ID`
- `BUFFER_TIKTOK_CHANNEL_ID`
- `BUFFER_PUBLISH_ENABLED` — keep unset or false until launch is approved.

After configuring the IDs, run the workflow in `dry_run` mode with a valid approved package. Only enable the publishing flag after the visual sample, thumbnail handling, public media hosting and end-to-end scheduling checks are approved.

Channel IDs must be retrieved from the authenticated Buffer account; never guess them. The publisher checks that the configured IDs belong to the expected YouTube and TikTok services.

Buffer's current API supports `addToQueue` and exact UTC scheduling. The initial adapter uses `addToQueue`, so set each channel's posting schedule and timezone in Buffer to the approved East Africa Time slots. The intended Shorts slots are 09:00 and 18:00 EAT. Do not configure these as UTC times by mistake.

## Media hosting and thumbnails

Buffer's API has no native media-upload endpoint. The approved media-hosting workflow uses GitHub Releases to host the MP4 and the separate branded YouTube thumbnail as public release assets. It verifies that the repository is public and that both asset URLs can be fetched without authentication. GitHub Actions artifacts are temporary/private and must never be used as Buffer media URLs.

The hosted production manifest receives:
```json
{
  "public_media": {
    "video_url": "https://github.com/OWNER/REPOSITORY/releases/download/RELEASE_TAG/finance-campus-video.mp4",
    "thumbnail_url": "https://github.com/OWNER/REPOSITORY/releases/download/RELEASE_TAG/thumbnail-youtube.jpg",
    "hosting_provider": "github_releases",
    "release_tag": "RELEASE_TAG",
    "publicly_accessible": true
  }
}
```

**YouTube thumbnail:** The project owner will upload `thumbnail-youtube.jpg` manually in YouTube Studio. No YouTube Data API OAuth integration is required for thumbnail uploads.

**TikTok cover:** Buffer can select a frame from the video using `metadata.thumbnailOffset`. The production renderer must embed the same branded cover artwork into the video and set `thumbnail_frame_embedded=true` plus a correct `thumbnail_offset_ms`. This renderer feature is not yet implemented, so short-form packages are not ready for live Buffer scheduling.

The hosting workflow does not approve publication. It records public media URLs and human visual review, but leaves `publication_approved` unset. The Buffer publisher fails closed until that separate approval is supplied.

## Post behavior

- Short videos create one YouTube post and one TikTok post, each with distinct platform-specific copy.
- Long-form videos create a YouTube post only.
- YouTube metadata uses the Education category (27), the script title and the generated description.
- TikTok uses the platform-native caption and the selected in-video branded thumbnail frame.
- Buffer queue times control actual publish times.
- A durable ledger at `production/buffer-publishing-ledger.json` stores Buffer post IDs and prevents repeat scheduling.
- The adapter also checks existing Buffer posts to recover from a lost local ledger update.
- Buffer's `scheduled` state means queued, not published. Only a Buffer `sent` state plus a verified public platform URL can update the project's publication ledger to publicly accessible.

## Publication monitoring

The workflow `.github/workflows/buffer-publication-monitor.yml` is scheduled every 30 minutes and can also be dispatched manually. It remains dormant until the repository Actions variable `BUFFER_MONITOR_ENABLED` is set to `true` after Buffer is connected. It reads Buffer post states for tracked post IDs, records `scheduled`, `sending`, `sent` and `error`, and checks Buffer's `externalLink` for sent posts.

A post is marked `publicly_accessible_verified` only when Buffer reports `sent`, provides a destination URL on an approved YouTube or TikTok domain, and an unauthenticated HTTPS request can reach that URL. A Buffer `sent` state alone is not enough. If the destination URL is absent or cannot be verified, the ledger remains `sent_awaiting_public_verification`. Failed Buffer posts are recorded as `failed`.

Buffer's GraphQL Post object exposes `status`, `sentAt` and `externalLink`; the API documents `sent` as published and `error` as a failed delivery. The monitor uses those fields rather than inferring publication from queue status. See the [Buffer API reference](https://developers.buffer.com/reference.html) and [Posts & Scheduling guide](https://developers.buffer.com/guides/posts-and-scheduling.html).

The monitor requires a read-capable Buffer personal API key. If Buffer returns a permission error for post retrieval, monitoring must be treated as failed—not as evidence of publication.

## GitHub Actions workflow

The workflow `.github/workflows/buffer-scheduling.yml` can be started manually with the completed production workflow run ID and artifact name, or called from a future production workflow using `workflow_call`. The artifact must contain `production-manifest.json`, `post-metadata.json`, the MP4 and the branded thumbnail at the package root/manifest paths. The reusable caller must pass Buffer secrets (for example, with `secrets: inherit`).

The workflow offers `discover`, `dry_run` and `schedule` modes. It defaults to `dry_run`. Use `discover` to retrieve organization/channel IDs. Select `schedule` only after the owner has approved the visual standard, the media host has been configured and the live-publishing lock has been intentionally enabled.

## Local validation

```bash
python -m finance_campus.buffer_publisher path/to/production-package
```

This performs a dry-run and checks Buffer channel configuration.

Live scheduling (locked until approved):

```bash
BUFFER_PUBLISH_ENABLED=true python -m finance_campus.buffer_publisher path/to/production-package --live
```

Never paste API keys into source files, workflow YAML, logs, issue comments or chat. Use GitHub Secrets.

## Important API references

- Buffer API introduction: https://developers.buffer.com/guides/introduction.html
- Posts and scheduling: https://developers.buffer.com/guides/posts-and-scheduling.html
- Create video post: https://developers.buffer.com/examples/create-video-post.html
- Hosting media: https://developers.buffer.com/guides/hosting-media.html
- YouTube metadata: https://developers.buffer.com/types/YoutubePostMetadataInput.html


## Downloading published thumbnails to your devices

The publication monitor now creates a downloadable GitHub Actions artifact for each thumbnail only after Buffer reports the post as sent and the public YouTube/TikTok URL has been independently verified. The thumbnail URL is carried into the publishing ledger when the post is scheduled, but no download is packaged while the post is merely queued or pending verification.

Each artifact contains the branded thumbnail image files and is retained for 90 days. Open the repository's **Actions** tab, select the latest successful **Buffer publication monitor** run, scroll to **Artifacts**, and download `finance-campus-published-thumbnails-...`. On Android, the ZIP can be opened from the Downloads folder; on a laptop, extract it like any other ZIP file. This is a tap-to-download workflow: GitHub Actions cannot silently write files into a phone or laptop's local storage.

No Google Drive API, Google account authorization, or additional paid service is required. This download feature does not enable or approve publishing; it only packages thumbnails for posts already verified as publicly available.
