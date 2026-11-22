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

## Buffer API requirements

Create a personal API key in Buffer settings and store it only in GitHub Actions Secrets as `BUFFER_API_KEY`. Configure these repository secrets:

- `BUFFER_API_KEY`
- `BUFFER_ORGANIZATION_ID`
- `BUFFER_YOUTUBE_CHANNEL_ID`
- `BUFFER_TIKTOK_CHANNEL_ID`
- `BUFFER_PUBLISH_ENABLED` — keep unset or false until launch is approved.

Channel IDs must be retrieved from the authenticated Buffer account; never guess them. The publisher checks that the configured IDs belong to the expected YouTube and TikTok services.

Buffer's current API supports `addToQueue` and exact UTC scheduling. The initial adapter uses `addToQueue`, so set each channel's posting schedule and timezone in Buffer to the approved East Africa Time slots. The intended Shorts slots are 09:00 and 18:00 EAT. Do not configure these as UTC times by mistake.

## Media hosting and thumbnails

Buffer's API has no native media-upload endpoint. Each video asset must use a direct, publicly accessible, stable HTTPS URL that remains available until the scheduled post is published. GitHub Actions artifacts are temporary and private; they are not valid Buffer media URLs.

The production manifest must include:

```json
{
  "public_media": {
    "video_url": "https://public-host.example/video.mp4",
    "thumbnail_frame_embedded": true,
    "thumbnail_offset_ms": 500
  }
}
```

The publisher validates that these fields exist but does not upload media to a hosting provider. A durable public media host and its credentials must be configured before live scheduling can work.

A separate branded thumbnail image is required in `artifacts.thumbnail`. Buffer's current video-post API cannot upload a custom YouTube video thumbnail. For TikTok, Buffer can select a frame from the video using `metadata.thumbnailOffset`; therefore the branded cover design must also appear as a frame inside the video, and the offset must point to it. A future YouTube thumbnail setter can use the YouTube Data API after Buffer publishes the video; this requires a separate authorized YouTube integration and must not be represented as already implemented.

## Post behavior

- Short videos create one YouTube post and one TikTok post, each with distinct platform-specific copy.
- Long-form videos create a YouTube post only.
- YouTube metadata uses the Education category (27), the script title and the generated description.
- TikTok uses the platform-native caption and the selected in-video branded thumbnail frame.
- Buffer queue times control actual publish times.
- A durable ledger at `production/buffer-publishing-ledger.json` stores Buffer post IDs and prevents repeat scheduling.
- The adapter also checks existing Buffer posts to recover from a lost local ledger update.
- Buffer's `scheduled` state means queued, not published. Only a Buffer `sent` state plus a verified public platform URL can update the project's publication ledger to publicly accessible.

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
