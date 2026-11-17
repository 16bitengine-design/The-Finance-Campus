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

The progressive whiteboard video renderer and Kokoro narration integration are implemented. The quality workflow has passed its illustrated sample render and artifact upload. The dedicated real-model Kokoro CPU smoke test still needs a successful run and artifact review before the full narration path is production-validated. Claim-level automated fact-checking, semantic visual QC, daily production scheduling, YouTube/TikTok upload adapters, publication verification, persistent publishing ledger, and operational notifications are not yet operational. Topic discovery is mindset-first and evergreen: it selects recurring money beliefs, habits, emotional triggers and everyday decisions rather than chasing financial headlines. Official financial education sources are used to check relevance and principles, not to turn press releases into videos. All topic candidates remain unapproved until editorial and claim-level review.



## Books, quotations and public-speaker inspiration

Scripts may include carefully verified ideas from classical financial books and respected speakers. Modern copyrighted material is normally paraphrased in original language with attribution; direct quotations require documented permission, a compatible licence or verified public-domain status. Attribution alone does not make a quote free to use. The script generator enforces rights metadata and a conservative 15-word internal limit for direct quotes, but human rights review remains necessary. See `docs/BOOKS_QUOTES_AND_SPEAKER_INSPIRATION.md`.

## Mindset-first topic discovery

The weekly repository workflow selects evergreen topics about money beliefs, everyday habits, emotional spending, comparison, avoidance, patience, debt behaviour, financial boundaries and resilience. The editorial agenda is not driven by news volume, market movements or the latest institutional press release.

Authoritative sources are used as research checks for the underlying educational principles and relevant local rules. Statistics and technical details are included only when essential to the lesson. A source being reachable or containing mapped keywords does not prove every proposed claim; each candidate remains subject to editorial review and claim-level verification. Topic refresh does not generate, render or publish videos.

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

The actual rendering engine and Kokoro integration are still under end-to-end verification. First-generation topic research and script-candidate workflows are implemented but require a live run. Platform publishing remains disabled until all production and publication gates pass.

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


## Automated topic research and script drafting

The first zero-cost topic and script drafting modules are now implemented.

### Weekly topic refresh

GitHub Actions runs `.github/workflows/weekly-topic-refresh.yml` every Monday at 08:30 Africa/Kampala time. It can also be started manually from the Actions tab. The workflow:
- checks a curated catalogue of authoritative sources, including the Consumer Financial Protection Bureau, Bank of Uganda and the U.S. SEC's Investor.gov;
- creates distinct topic candidates from 20 editorially defined learning briefs;
- checks source reachability and mapped keyword relevance;
- rejects unavailable or irrelevant source pages;
- checks the persistent JSON library for duplicate IDs and normalized titles;
- saves new topics with category, audience, geographic relevance, source metadata and research/production/publication states.

The weekly target is 20 new topics. The workflow reports the actual number added; it does not invent replacements when sources are unavailable. Some sources, particularly PDFs, still need text extraction and manual relevance review. URL reachability and keyword presence are not proof that a source supports every claim. Topic records therefore remain marked for claim-level review.

### Generate a script candidate

After a topic has been added to `data/topics.json`, generate a short script candidate:

```bash
python -m finance_campus.cli generate-script data/topics.json production/script-candidates/emergency-fund.json --topic-id TFC-<TOPIC_ID> --duration short
```

Use `--duration long` for a 5–10 minute script candidate. Replace the example topic ID with an actual ID in the topic library.

The current generator is a deterministic editorial-template engine, not an LLM. It builds the six required story sections from the researched editorial brief and includes source metadata. It does not call a paid API, does not invent numerical statistics, and does not mark its output production-approved. Generated candidates are deliberately rejected by the production script validator until claim-level source verification and editorial approval are completed.

### Current limitations

- Research currently uses a curated source catalogue and editorial topic blueprints; it is not yet an open-ended web discovery or news-monitoring agent.
- Source checks verify HTTP reachability and keyword presence, not semantic claim support.
- Script drafts are structured and ready for editorial refinement, but are not yet fully original long-form narrative writing.
- No generated script is automatically sent to Kokoro or video production. Topic refresh and script drafting do not publish or produce videos.


## Implementation and release status

See [docs/IMPLEMENTATION_STATUS.md](docs/IMPLEMENTATION_STATUS.md) for the verified capability matrix, current limitations, release controls and engineering sequence. Configuration validation now rejects early publishing activation, non-Kokoro narration, paid-service settings and removal of the required human visual review gate.

Generated scripts now report their spoken word count and estimated narration duration using a 145 words/minute planning assumption. This helps identify drafts that cannot realistically fill their declared format; it does not replace pacing review.
