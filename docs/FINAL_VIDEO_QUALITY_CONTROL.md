# Final video quality control

Every rendered MP4 must pass the automated final-video gate before its production manifest can be marked quality-approved.

## Automated checks

- MP4 exists and is not implausibly small.
- Both video and narration audio streams are present.
- Shorts are exactly 1080x1920; long-form is exactly 1920x1080.
- Video uses H.264 with yuv420p pixel format.
- Encoded average frame rate matches the requested rate (normally 30 fps).
- Narration uses AAC, 24 kHz, mono.
- Frame count and container duration agree when frame count metadata is available.
- FFmpeg decodes the entire output without errors.
- Audio mean level is not below -36 dBFS; peak is between -12 and -0.1 dBFS to reject inaudible or clipping narration.
- Existing production checks separately validate caption timing/coverage and audio/video duration alignment.

A failed check raises an error and prevents the production manifest from reaching `quality_approved`. The production pipeline still does not upload or publish videos.

## Human review still required

Automated stream checks cannot determine whether an illustration accurately explains the narration, whether a visual is attractive, whether text is readable on a phone, or whether captions are well positioned and synchronized perceptually. Review the rendered MP4 and its contact sheet before authorizing publication. Source URL presence also does not prove that a source is reachable or supports the claim; research verification remains a separate editorial gate.

## Human visual approval is mandatory

A technically valid render is now marked `awaiting_visual_review`, not fully approved. The production pipeline extracts eight evenly spaced frames from the final encoded MP4 and assembles `visual-review-contact-sheet.jpg`. The contact sheet is included with the production artifacts.

A reviewer must inspect the actual video and contact sheet for:
- Whether each illustration explains the narration rather than merely decorating it.
- Whether visual changes occur at the right spoken moments and scenes build a coherent story.
- Whether captions are readable on a phone, correctly placed and synchronized.
- Whether important words, diagrams and disclaimer text remain inside safe margins and are legible.
- Whether there are blank frames, visual glitches, abrupt transitions or distracting clutter.
- Whether the visual tone is respectful and hopeful without exaggerating hardship or creating panic.

The system deliberately does not mark human review as passed. A generated contact sheet is evidence for review, not proof of semantic or aesthetic quality. No publishing stage is enabled.
