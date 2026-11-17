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
