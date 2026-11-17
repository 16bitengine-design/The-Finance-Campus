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

## Development status
This repository is being initialized. Publishing remains disabled until the production pipeline and platform integrations pass end-to-end quality checks.

## Planned architecture
Python orchestration; Kokoro TTS; SVG/custom whiteboard renderer; Manim for suitable mathematical scenes; Remotion for advanced motion graphics; FFmpeg for media processing; PostgreSQL with JSON topic exports; GitHub Actions for repository-native automation; YouTube Data API and TikTok Content Posting API.

## Local setup
See `docs/DEVELOPMENT.md` for the staged development plan. Copy `.env.example` to `.env` for local configuration. Never commit secrets.