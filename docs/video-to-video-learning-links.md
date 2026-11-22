# Video-to-video learning links

The Finance Campus should help viewers move from a brief mention to a deeper lesson without making every video repeat the full explanation.

## How it works

1. Every script carries `related_concepts`, using explicit topic concepts or the researched topic keywords as a fallback.
2. Production checks `production/published-video-library.json` for a previously published lesson sharing those concepts.
3. Only records marked `publicly_accessible_verified` with a valid HTTPS YouTube watch URL can be selected. Drafts, renders, uploads awaiting confirmation and scheduled posts are excluded.
4. The strongest exact concept overlap is selected. If there is no relevant verified lesson, no cross-promotion is added.
5. The chosen lesson is mentioned naturally in the final spoken section, and its direct URL is added to the YouTube description. TikTok copy points viewers to the lesson on the Finance Campus YouTube channel because external URLs in captions may not be clickable.
6. The selected video and matched concepts are recorded in the production manifest for traceability.

## Library record format

Add a record only after independently verifying that the video is publicly accessible:

```json
[
  {
    "video_id": "stable-internal-id",
    "title": "What Are Stocks and How Do They Work?",
    "url": "https://www.youtube.com/watch?v=YOUR_VERIFIED_VIDEO_ID",
    "concepts": ["stocks", "shares", "ownership", "investing"],
    "status": "publicly_accessible_verified"
  }
]
```

Replace the example URL with the actual public video URL. Never add a placeholder or infer a URL. Keep concepts specific enough to avoid irrelevant recommendations.

## Editorial rules

- Our own voice, not the source video's wording or tone.
- A natural spoken invitation, not a disruptive advertisement.
- At most one related lesson is selected for each video.
- Never recommend an unpublished, inaccessible or unverified video.
- Never invent a related video when no match exists.
- Related links are supplemental; the current lesson must remain understandable on its own.
- This feature does not publish videos or change the publishing approval gate.

## Current state

The registry is initialized at `production/published-video-library.json` and is empty until the first public video is independently verified. The matching and production handoff are implemented, but recommendations will begin only after verified public video records are added.
