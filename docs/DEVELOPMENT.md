# Development plan

## Non-negotiable gates
1. Research sources and claims are traceable.
2. Financial calculations are computed in code and covered by tests.
3. Spoken, on-screen, and description disclaimers are mandatory.
4. Brand configuration is injected into every visual workflow; graduation imagery is prohibited.
5. Kokoro is the only approved narration engine.
6. Failed quality checks block publishing.
7. Public availability must be verified before a post is recorded as published.
8. Publishing stays disabled until end-to-end tests and account authorization are complete.

## Implementation sequence
1. Repository foundation and configuration validation.
2. Topic library, research records, duplicate detection, and weekly refresh workflow.
3. Script schema, source/claim validation, and calculation utilities.
4. Storyboard schema and reusable whiteboard illustration/animation components.
5. Kokoro narration, mixing, caption synchronization, and audio validation.
6. FFmpeg rendering and video integrity checks.
7. Brand, disclaimer, originality, and visual quality gates.
8. YouTube/TikTok upload adapters, safe retries, and public verification.
9. Repository-native scheduling, monitoring, recovery, and analytics.

## Local setup
- Python 3.11 or newer is recommended.
- Install project dependencies with `python -m pip install -e .[dev]` after the package scaffold is added.
- Copy `.env.example` to `.env` and populate only the credentials required for the stage being tested.
- Never enable publishing for test runs or before the quality gates pass.

## Workflow policy
Prefer GitHub Actions for tasks that can run reliably inside this repository. Do not create duplicate external schedules for repository-native workflows. Topic refresh must never trigger video production or publishing.