# Implementation status and release boundaries

Last reviewed: 2026-11-17

This document distinguishes working repository capabilities from intended architecture. A workflow file or configuration flag is not proof that an external integration has been tested.

## Working and repository-tested

| Capability | Current status | Evidence / limitation |
|---|---|---|
| Brand, disclaimer and operating configuration | Implemented | CLI validation checks all three configurations. |
| Mindset-first topic catalogue | Implemented | 66 unique evergreen blueprints are present in `src/finance_campus/mindset_topics.py`. |
| Weekly topic refresh | Implemented | `.github/workflows/weekly-topic-refresh.yml`; live publisher reachability and mapped-keyword checks run during refresh. |
| Source-domain safeguards | Implemented | Production accepts HTTPS sources only from the explicit publisher allowlist; redirects in topic refresh must remain on the approved publisher domain. |
| Script candidate drafting | Implemented, deterministic | `script_generator.py` creates structured candidates from topic briefs. It does not use an LLM and does not claim factual verification. |
| Candidate script workflow | Implemented | Repository workflow generates candidates after a successful topic refresh or manual dispatch. |
| Script structure and editorial phrase checks | Implemented | This is not semantic fact-checking. |
| Script duration telemetry | Implemented | Word count and estimated narration duration use a 145 words/minute planning assumption. Long-form candidates that fall short are visibly marked under target. |
| Storyboard and whiteboard rendering | Implemented, deterministic | Narration maps to a limited reusable illustration vocabulary. Character poses, prop-directed interactions, eased reaching gestures and a basic time-based walking gait are rendered per frame. Full object handling (gripping, lifting, opening, exchanging) and semantic illustration generation remain future work. |
| Kokoro integration | Implemented in code | The dedicated manual CPU smoke workflow is available. A successful run and human review of its actual artifacts are still required before calling the full Kokoro path production-validated. |
| MP4 technical QC | Implemented | FFmpeg/ffprobe, dimensions, encoding, stream, decode and audio-level checks. |
| Caption timing and visual review evidence | Implemented | SRT validation and contact-sheet extraction are available. A contact sheet is not semantic visual approval. |
| Automated quality CI | Passing on the latest reviewed commits | Quality workflow tests, lint and illustrated sample render/artifact upload have passed. |

## Not yet operational

| Capability | Why it is not considered operational |
|---|---|
| Claim-level financial fact-checking | Source URL reachability and keyword matches do not prove that a source supports each claim. |
| AI-assisted research synthesis | Current script drafting is deterministic and does not retrieve/compare source passages for each claim. |
| Fully semantic visual QC | The system cannot yet reliably determine whether every illustration accurately explains the narration or whether the full video is aesthetically acceptable. Human visual review remains mandatory. |
| Scheduled daily video production | No complete daily production schedule is active. |
| YouTube upload and public verification | No tested upload adapter, account authorization, upload ledger or public-availability verifier is implemented. |
| TikTok upload and public verification | No tested Content Posting API adapter, app approval/authorization flow or public-availability verifier is implemented. |
| Duplicate-safe publishing and recovery | No persistent publication state machine or verified retry/reconciliation process is implemented. |
| Operational notifications and monitoring | No tested failure notification integration is configured. |

## Release controls

- YouTube and TikTok remain disabled.
- `production.publishing_enabled` must remain false.
- Automatic publishing and automatic public-verification settings must remain false until the adapters, authorization, idempotency, quota handling, and public verification tests pass.
- Human visual review remains required until semantic visual quality controls are demonstrated to be reliable.
- No paid service or paid API may be introduced without explicit approval.
- Kokoro remains the only approved narration engine.
- Topic refresh and script-candidate generation do not start rendering or publishing.

## Next engineering sequence

1. Complete and review the real Kokoro CPU end-to-end smoke test.
2. Improve storyboard semantics and expand the original illustration library.
3. Add explicit claim-review evidence and stronger research records.
4. Implement a durable local/repository production ledger and resumable stage tracking.
5. Implement platform adapters, authorization validation, duplicate protection and public verification.
6. Add quota-aware schedules, bounded retries, monitoring and failure notifications.
7. Validate complete production runs and only then consider enabling unattended publishing.

A feature is promoted from planned to operational only after tests exercise the real integration and the evidence is retained.
