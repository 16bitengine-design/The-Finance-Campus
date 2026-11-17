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

The progressive whiteboard video renderer and Kokoro narration synthesis are implemented. Real-model CPU synthesis and end-to-end narrated video rendering still require the dedicated smoke test and artifact review. Rendered-image computer-vision checks, research automation, and platform publishing are not implemented yet.


## Kokoro narration integration

Kokoro is the project's only approved narration engine. The integration supports four English voice profiles: female voices `af_heart` and `bf_emma`, and male voices `am_michael` and `bm_george`. Synthesis runs locally on CPU by default when explicitly selected; CUDA is optional. No paid speech API or API key is used.

### Install

1. Install FFmpeg and `espeak-ng` (the latter provides pronunciation fallback for unfamiliar English words).
2. Install the CPU build of PyTorch, suitable for machines without a supported GPU:

   `python -m pip install torch --index-url https://download.pytorch.org/whl/cpu`

3. Install the project with the Kokoro extra:

   `python -m pip install -e ".[dev,tts]"`

3. The first synthesis downloads the open-weight Kokoro model and selected voice pack from Hugging Face. The model is cached for later runs. The first run therefore needs an internet connection and enough disk space; inference can then run locally.

### Generate scene-aligned narration

```bash
python -m finance_campus.cli synthesize-narration \
  examples/illustrated-savings-short.json production/kokoro \
  --voice af_heart --device cpu --speed 1.0 \
  --transition-seconds 0.25 --draw-fps 24
```

The command creates:
- `narration.wav`: assembled mono PCM narration at 24 kHz.
- `captions.srt`: caption cues aligned to synthesized narration chunks.
- `storyboard_with_audio_timing.json`: storyboard with scene durations recalculated from the generated speech, plus a short drawing hold and transition silence.

Then render the video using those exact generated assets and the same transition/drawing frame settings:

```bash
python -m finance_campus.cli render-video \
  production/kokoro/storyboard_with_audio_timing.json production/kokoro/finance-campus.mp4 \
  --format short --fps 30 --draw-fps 24 \
  --audio production/kokoro/narration.wav \
  --captions production/kokoro/captions.srt \
  --transition-seconds 0.25
```

Available voice choices: `af_heart`, `am_michael`, `bf_emma`, `bm_george`. Use `--device cpu` on machines without a supported GPU. Keep `--draw-fps` and `--transition-seconds` identical in both commands so the speech, scene holds and cross-dissolves stay aligned.

The synthesis step checks for empty/non-finite audio, silence, peak level and output WAV integrity, and applies consistent loudness normalization with a peak ceiling. It fails rather than silently substituting another TTS provider.

### Real-model verification

The manually triggered GitHub Actions workflow `Kokoro end-to-end production test` installs Kokoro and `espeak-ng`, downloads the actual model, synthesizes the sample storyboard on CPU, renders the MP4 with narration and captions, and uploads the resulting files for review. The normal lightweight test suite uses a mocked Kokoro pipeline so it does not download model weights on every commit.


## End-to-end narrated video production

The automated production entry point starts from an approved structured script and creates the complete illustrated video package:

1. Validate the six required editorial sections, prohibited claims and source links.
2. Build six illustrated whiteboard scenes using a deterministic financial-visual mapping (people, wallets, bank buildings, money notes, coins, savings jars and connecting arrows).
3. Add the spoken disclaimer and a visible disclaimer scene held for at least six seconds.
4. Synthesize every scene with Kokoro, using the selected voice and actual generated speech duration.
5. Generate synchronized SRT captions and insert silent holds for scene transitions.
6. Render the progressive whiteboard animation with smooth cross-dissolves, narration and burned-in captions.
7. Verify the MP4 dimensions and audio/video streams, append the description disclaimer, and run the fail-closed quality gate.
8. Save a production manifest. The pipeline does not upload or publish videos.

The storyboard mapper is deliberately deterministic: it selects suitable financial illustrations from the approved narration. It is not yet a generative visual-understanding system, so the storyboard should still be reviewed during production-quality development.

### One-command production

Use an approved script package with at least one reputable source URL (see examples/script-package.example.json):

```bash
python -m finance_campus.cli produce-video \
  examples/script-package.example.json production/emergency-fund-short \
  --format short --voice af_heart --device cpu \
  --fps 30 --draw-fps 24 --transition-seconds 0.25
```

For a YouTube long-form video, use --format long. Available voice IDs are af_heart, am_michael, bf_emma, and bm_george.

A successful run writes approved_script.json, storyboard.json, storyboard_with_audio_timing.json, narration.wav, captions.srt, finance-campus-video.mp4, description.txt, and production-manifest.json. The manifest records generated, rendered, and quality-approved states separately from upload and public availability. Publishing remains disabled.

The real-model Kokoro end-to-end production test remains a separate manual GitHub Actions workflow. It downloads the model and performs actual CPU synthesis; mocked unit tests do not count as proof of real voice quality.

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

Storyboards map each spoken scene to a duration and a sequence of visual elements. A scene containing only text is rejected. Supported visual elements include geometric primitives plus line-art people, banks, wallets, houses, coins, banknotes and savings jars. Set the storyboard canvas to 1000×1778 for native portrait composition or 1000×562 for landscape composition.

Validate a storyboard:

`python -m finance_campus.cli validate-storyboard examples/storyboard.example.json`

Render each scene to a standalone animated SVG whiteboard frame:

`python -m finance_campus.cli render-storyboard examples/storyboard.example.json production/storyboards/debt-example`

The SVG renderer produces scene assets at the storyboard canvas aspect ratio. The MP4 renderer in `src/finance_campus/video_renderer.py` progressively reveals the line-art illustrations into raster frames with Pillow, then encodes and validates a playable H.264 MP4 with FFmpeg. It supports vertical 1080×1920 Shorts and horizontal 1920×1080 long-form layouts, preserving the composition rather than stretching it. The built-in person and financial-object drawings are intentionally simple reusable line-art assets; richer custom character artwork remains a visual-quality upgrade.

Render an MP4:

`python -m finance_campus.cli render-video examples/illustrated-savings-short.json production/renders/example.mp4 --format short`

Use `--format long` for 16:9. FFmpeg and Pillow are required. Narration audio and SRT captions can be supplied to the same render command and will be muxed/burned into the MP4:

`python -m finance_campus.cli render-video storyboard.json output.mp4 --format short --audio narration.wav --captions captions.srt`

The renderer validates the requested audio stream and the final MP4 playback. Drawing defaults to 24 progressive frames per second, with 30 fps output; tune it using `--draw-fps` and `--fps`. Tune scene fades using `--transition-seconds`. Kokoro narration generation is available as a separate command and is also integrated into the end-to-end `produce-video` command. Captions are generated from the synthesized narration and burned into the rendered video. A gentle whiteboard cross-dissolve is applied at scene boundaries and can be tuned with `--transition-seconds`. More advanced hand-drawn character animation and broader audiovisual quality checks remain outstanding. CI renders and stores a sample illustrated portrait video as a workflow artifact.
