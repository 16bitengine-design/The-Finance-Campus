# Finance Campus hybrid animation renderer

## Goal
Build a coordinated animation studio for authored financial storytelling—not a text-animation template. Visual scenes must communicate the narration through directed artwork, stable characters, timed actions, object interactions and visible consequences.

## Renderer responsibilities
- **Remotion:** final frame-accurate composition, scene timing, transitions, typography, captions, narration/music placement and delivery formats.
- **Rough.js:** hand-drawn treatment for selected SVG illustrations, charts, arrows and explanatory diagrams.
- **SVG stroke-dash:** progressive whiteboard line reveals with deterministic frame timing.
- **Canvas 2D:** deterministic moving objects, particles, compositing and camera-like transforms in frame-indexed scenes.
- **Manim:** specialist mathematical and financial explainers—compound interest, amortization, inflation, percentages and data-driven diagrams.
- **Blender:** genuine 3D environments, objects, lighting, camera movement and spatial interactions.
- **Python + FFmpeg:** orchestration, asset validation, Kokoro narration, audio finishing, caption checks, final encoding and QC.

These tools are not interchangeable. Remotion coordinates the final edit; specialist backends produce the visual material best suited to each scene. All animation must be deterministic by frame number so renders can be resumed and reproduced.

## Remotion starter
The initial Remotion project is in `renderer/remotion`. It includes a frame-driven demo composition, Rough.js SVG illustration, normalized SVG stroke reveal and a Canvas 2D motion layer.

From the repository root:

```bash
cd renderer/remotion
npm install
npm run typecheck
npm run compositions
npm run studio
npm run render:demo
```

Node.js 20+ is required. The included demo is an integration smoke-test, not a production-quality sample or approved final visual. Its basic illustration must not be mistaken for the final art direction.

## Manim
Install the optional Python extra in a worker with the required system dependencies:

```bash
python -m pip install -e ".[manim]"
```

Manim should be used only for scenes that benefit from precise mathematical layout and animation. It should export scene assets/video segments for the shared timeline, not take over the whole production.

## Existing Python renderers
- The layered 2D timeline streams authored transparent PNG layers to FFmpeg.
- The character rig provides bilateral pose animation, props and audio-envelope mouth movement.
- The Blender backend renders authored `.blend` projects.
- These backends are not yet connected to Remotion through one production timeline. The next integration step is a validated scene interchange format with explicit dimensions, frame rate, duration, asset paths, z-order, timing and audio/caption references.

## Production gates
- Final videos must be at least **150 seconds**.
- Vertical: 1080×1920; horizontal: 1920×1080; final delivery at 30 FPS.
- Kokoro remains the required narration engine.
- Spoken, readable on-screen and description disclaimers remain mandatory.
- Keep source references, financial calculations and geographic scope attached to scripts.
- Human visual approval remains mandatory. A passing renderer test does not prove visual quality.
- The existing production pipeline remains active until the hybrid renderer passes end-to-end validation and is visually approved.
- No paid assets, APIs or compute without explicit approval.
- YouTube and TikTok publishing remain disabled.

## Current limitations
The Remotion starter is not yet wired to Kokoro, the Python production manifest, Manim or Blender. Canvas is currently a frame-driven demo layer, not the complete multi-character compositor. Rough.js uses authored vector paths and is not an automatic illustration generator. The 2D character rig is not a full IK/face rig. Do not claim production readiness until these integration gaps are closed and the resulting videos pass human review.

## Multi-character scene composition

The Python compositor now supports a scene package with a `scene` object and a
`character_specs` dictionary keyed by persistent character ID. Each scene
character entry declares its ID, z-order, and independently sampled keyframes
(`at`, `x`, `y`, optional `scale`, optional `opacity`). Characters are
rendered as transparent RGBA layers and composited from lower to higher z-order.
Track positions and opacity are interpolated deterministically from scene time.

Validate and render frame sequences with:

```bash
python -m finance_campus.cli validate-multi-character-scene examples/multi-character-scene.example.json
python -m finance_campus.cli render-multi-character examples/multi-character-scene.example.json build/multi-character-frames
```

This is an explicit composition layer, not yet a complete interaction system:
props are still authored within each character rig, and cross-character handoffs,
collision-aware blocking, camera transforms, and Remotion manifest export remain
follow-on integration work. The current compositor expects the character rig
canvas to fit the scene canvas after its declared scale and position; off-canvas
placements are clipped by the output canvas.
