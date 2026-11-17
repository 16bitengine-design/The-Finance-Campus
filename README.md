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
- Fail-closed video-package quality gate.
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

See `config/editorial-policy.md`. The policy describes the target editorial standard; automated script-level enforcement is still to be implemented and tested.

## Script editorial quality gate

Structured scripts are checked before production with:

`python -m finance_campus.cli validate-script path/to/script.json`

The JSON package must include all six editorial story sections, a claims list (which may be empty), and explicit labels for hypothetical examples. Every listed factual claim must have at least one valid HTTP(S) source URL. The gate rejects a defined set of guaranteed-wealth promises and shaming phrases. It intentionally permits honest discussion of poverty, fear, debt, inflation, unemployment, and financial insecurity.

This is a deterministic first-line gate. It checks required structure, source metadata, and known prohibited phrases; it does not prove that a source supports a claim or reliably understand every possible manipulative statement. Independent research verification and deeper semantic review remain necessary before publishing.
