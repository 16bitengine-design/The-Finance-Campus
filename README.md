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
