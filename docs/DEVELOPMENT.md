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
## Zero-cost development gate
- No paid APIs, subscriptions, media assets, hosting, compute, or publishing intermediaries.
- Prefer free/open-source and locally runnable tools; guard free-tier quotas and stop rather than incur charges.
- Kokoro TTS remains the only approved narration engine.
- Produce original whiteboard illustrations and animations in code; do not substitute text-only motion.
- Use direct YouTube/TikTok APIs only where access is granted; do not assume quotas or eligibility are unlimited.
- If a required step has no viable zero-cost path, stop and explain the constraint rather than activating a paid service.

See config/cost-policy.md.
## Unattended operating requirement
The intended production mode is fully unattended after one-time setup and platform authorization. No routine human approval is required for topic selection, research, scripting, storyboarding, illustration, Kokoro narration, rendering, quality checks, scheduled publishing, or publication verification.

Automation must:
- Run the complete scheduled pipeline without waiting for a person between stages.
- Enforce every financial accuracy, source, disclaimer, originality, audio, visual, and media-integrity gate automatically.
- Publish automatically only when every required gate passes and platform authorization is valid.
- Retry transient failures with bounded backoff; never loop indefinitely or duplicate a post.
- Record each stage and retain evidence for upload acceptance and public availability.
- Notify the operator about blocking failures, expired credentials, quota limits, or platform restrictions; do not bypass safeguards.
- Resume safely from recorded state after interruptions.

One-time setup still requires valid platform account authorization and any platform-mandated app review or permissions. These external requirements cannot be automated away. The current implementation is not yet fully operational; keep publishing disabled until end-to-end tests pass.
## Script production handoff

The current script stage exposes two commands:

- `python -m finance_campus.cli validate-script candidate.json` checks a structured candidate without writing output.
- `python -m finance_campus.cli prepare-script candidate.json production/approved/script.json` writes an approved package only after the editorial validator passes.

The expected JSON structure is illustrated in `examples/script-package.example.json`. All six editorial story sections are mandatory. Every item in `claims` must include text and at least one syntactically valid HTTP(S) source URL. Hypothetical examples must be explicitly labelled. Known guaranteed-wealth promises and shaming phrases are rejected. Urgent discussion of poverty, debt, inflation, unemployment, and financial insecurity is permitted.

The approval handoff writes atomically and leaves an existing approved file untouched when a candidate fails. Future script generators must submit their output to this handoff and downstream storyboard/audio/rendering stages must read only approved files.

This does not yet implement AI script generation, source retrieval, claim-to-source verification, or robust semantic review. The URL check confirms syntax only; it does not prove source authority or claim support. Do not treat this gate alone as financial fact-checking.
