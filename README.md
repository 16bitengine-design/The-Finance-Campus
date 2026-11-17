# The Finance Campus

Automated financial education media production for YouTube and TikTok.

## Mission
Make personal finance understandable through accurate, engaging, professionally illustrated educational videos for global audiences, including Uganda and East Africa.

## Brand
- Name: The Finance Campus
- Tagline: Your classroom for smarter money decisions.
- Slogan: Learn. Apply. Grow.
- Palette: navy, green, gold, white
- Visual language: premium whiteboard illustration and modern motion graphics. No graduation imagery.
- Narration: Kokoro TTS only.

## Safety and publishing policy
Every video must include a spoken disclaimer, a readable on-screen disclaimer, and a description disclaimer. Financial claims require reputable sources; calculations must be independently computed and tested. No personalized financial advice or guaranteed returns. Failed quality checks block publishing. A video is only counted as published after public availability is verified.

## Current implementation
- Central YAML brand, project, and disclaimer configuration.
- Configuration validation and CLI checks.
- Shared brand-token and asset-metadata validation helpers.
- Canonical disclaimer helpers.
- JSON topic-library utilities with duplicate protection.
- Fail-closed video-package quality gate, including mandatory script editorial validation.
- Structured script validator and atomic fail-closed approval handoff.
- GitHub Actions test/lint workflow.

Rendered-image computer-vision checks, media rendering, Kokoro integration, research automation, and platform publishing are not implemented yet.

## Development status
Publishing remains disabled until the production pipeline and platform integrations pass end-to-end quality checks.

## Planned architecture
Python orchestration; Kokoro TTS; SVG/custom whiteboard renderer; Manim for suitable mathematical scenes; Remotion for advanced motion graphics; FFmpeg for media processing; PostgreSQL with JSON topic exports; GitHub Actions for repository-native automation; YouTube Data API and TikTok Content Posting API.

## Local setup
1. Use Python 3.11 or newer.
2. Create a virtual environment: `python -m venv .venv`.
3. Activate it and install: `python -m pip install -e ".[dev]"`.
4. Run tests: `python -m pytest -q`.
5. Validate configuration: `python -m finance_campus.cli validate-config`.
6. Copy `.env.example` to `.env` only when local secrets are needed. Never commit secrets.

## Zero-cost requirement
The complete system is designed for zero monetary cost from ideation through publishing. Paid AI APIs, paid subscriptions, paid media assets, paid hosting/compute, and paid publishing intermediaries are not permitted. Prefer free/open-source software, locally runnable tools, and direct platform APIs. See config/cost-policy.md.

Zero monetary cost does not mean unlimited free cloud compute or guaranteed platform API access. GitHub Actions and social-platform APIs have quotas, eligibility/review requirements, and terms that can change. The system must use quota guards and stop rather than silently incur charges if a zero-cost route is unavailable. Local/self-hosted execution is the fallback where practical.

The actual rendering engine, Kokoro integration, research automation, and platform publishing are still under development; publishing remains disabled until end-to-end tests pass.

## Publishing cadence target
- Two distinct short videos are produced each day.
- Each of the two videos is cross-published to YouTube Shorts and TikTok, resulting in two posts per day on each platform (four platform posts total).
- The configured target slots remain 09:00 and 18:00 Africa/Kampala time.
- Publishing is still disabled until the full pipeline, account access, quality gates, and public-verification checks are tested.

## Unattended operation
After one-time setup and platform authorization, the target system runs end to end without routine human intervention: research, topic selection, scriptwriting, illustration, Kokoro narration, rendering, quality control, scheduled publishing, and public-post verification. It retries recoverable failures safely, prevents duplicate uploads, resumes from recorded state, and reports blocking failures.

Publishing remains disabled until end-to-end tests pass and platform authorization is configured. Initial account authorization and any platform-mandated app review cannot be skipped or guaranteed by code.
## Editorial promise: urgency that leads to hope and action

Our videos are designed to move viewers to act. We may directly address poverty, debt, inflation, unemployment, financial insecurity, fear, and other difficult money realities. We should not soften genuine problems until they lose their urgency. Use honest escalation to show how financial pressures can compound and why timely decisions matter.

The required story arc is: relatable financial problem → escalating real-world stakes → clear explanation → hopeful and realistic possibility → practical action → empowering close.

Urgency must be evidence-based, not manufactured. Never shame people facing hardship, present risks as certainties, exploit fear, or promise guaranteed wealth or investment returns. Every video should leave viewers with a realistic next step and a sense that improvement is possible.

See `config/editorial-policy.md`. The policy describes the target editorial standard; automated script-level enforcement is implemented as a deterministic first-line gate; deeper semantic and source-support verification remains outstanding.

## Script editorial quality gate

Structured scripts are checked before production with:

`python -m finance_campus.cli validate-script path/to/script.json`

The JSON package must include all six editorial story sections, a claims list (which may be empty), and explicit labels for hypothetical examples. Every listed factual claim must have at least one valid HTTP(S) source URL. The gate rejects a defined set of guaranteed-wealth promises and shaming phrases. It intentionally permits honest discussion of poverty, fear, debt, inflation, unemployment, and financial insecurity.

This is a deterministic first-line gate. It checks required structure, source metadata, and known prohibited phrases; it does not prove that a source supports a claim or reliably understand every possible manipulative statement. Independent research verification and deeper semantic review remain necessary before publishing.

### Prepare a script for production

A script generator or researcher must first produce a JSON package following `examples/script-package.example.json`. The production handoff validates the complete package and writes it to the approved location only if every deterministic editorial check passes:

`python -m finance_campus.cli prepare-script candidate.json production/approved/script.json`

An invalid candidate exits with an error and does not create or overwrite the approved output. To run the checks without writing an approved copy:

`python -m finance_campus.cli validate-script candidate.json`

The handoff is ready for a future generator to call. It does not itself generate scripts or call an AI service; no script-generation provider has been integrated. All production stages must consume only approved script packages.


## Financial calculation library

The first calculation layer is implemented in `src/finance_campus/calculations.py`:
- Compound growth with configurable periodic compounding.
- Fixed-payment amortizing loan estimates.
- Inflation-adjusted purchasing-power estimates.
- Monthly savings deposits for a target under an explicitly assumed return.

Run its automated checks with `python -m pytest -q`. Inputs are validated and invalid or non-finite values are rejected. Loan estimates use nominal APR divided by 12; savings deposits are assumed to occur at month-end and the annual return is converted to an equivalent monthly rate. These are educational mathematical models, not quotes or forecasts. Actual fees, taxes, variable rates, deposit timing, and product terms may change outcomes. Any assumed return must be clearly labelled hypothetical and never presented as guaranteed.

## Illustrated whiteboard storyboard pipeline

Storyboards map each spoken scene to a duration and a sequence of visual elements. A scene containing only text is rejected; it must include at least one illustration such as a shape, line, or arrow.

Validate a storyboard:

`python -m finance_campus.cli validate-storyboard examples/storyboard.example.json`

Render each scene to a standalone animated SVG whiteboard frame:

`python -m finance_campus.cli render-storyboard examples/storyboard.example.json production/storyboards/debt-example`

The SVG renderer produces scene assets. The MP4 renderer in `src/finance_campus/video_renderer.py` draws storyboard elements progressively into raster frames with Pillow, then encodes and validates a playable H.264 MP4 with FFmpeg. It supports vertical 1080×1920 Shorts and horizontal 1920×1080 long-form layouts. The first renderer animates geometric illustration primitives (circles, rectangles, lines, arrows and labels); complex character artwork is a later upgrade.

Render an MP4:

`python -m finance_campus.cli render-video examples/storyboard.example.json production/renders/example.mp4 --format short`

Use `--format long` for 16:9. FFmpeg and Pillow are required. Kokoro narration, audio mixing, synchronized captions, transitions, and full audiovisual quality checks remain separate stages.
