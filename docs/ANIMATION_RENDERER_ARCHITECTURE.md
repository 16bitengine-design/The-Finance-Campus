# Finance Campus 2D/3D Animation Renderer

## Goal
A repository-owned renderer for authored 2D and 3D scenes. This is not a text-animation template. Scenes use directed artwork, stable character and prop assets, timed actions and visible consequences.

## Architecture
- Timeline contract: ordered scenes, shared canvas and frame rate.
- 2D backend: layered transparent artwork, z-order, keyframes, motion, opacity, rotation and whiteboard-style reveals. Frames stream to FFmpeg instead of accumulating in RAM.
- 3D backend: headless Blender rendering of authored .blend scenes, with explicit output dimensions, frame rate and render engine. No silent 2D fallback.
- Audio and finishing: Kokoro remains narration provider; FFmpeg remains final assembly tool; existing captions, disclaimer and final-video quality gates remain mandatory.
- Release: human visual approval is mandatory; publishing remains disabled.

## 2D timeline
The example manifest uses relative paths. Each scene points to a layered-scene JSON and a directory containing its authored transparent PNG layers. All scene canvases must match.

Render command:
python -m finance_campus.cli render-2d-timeline examples/animation-timeline.example.json build/preview.mp4

The example manifest is a contract only; referenced production artwork must exist. Missing assets fail closed.

## 3D workflow
Create and art-direct a Blender project with real models, materials, lights, cameras and keyframed actions. Render it headlessly:
python -m finance_campus.cli render-3d-project assets/3d/household-scene.blend build/household-scene.mp4 --width 1080 --height 1920 --fps 30

Install Blender on the worker and ensure its executable is on PATH. Blender is not installed by the Python package and is not assumed available on GitHub-hosted runners. Use a self-hosted worker with Blender installed for reproducible cloud renders. CPU rendering is supported but may be slow.

## Quality and safety
Keep the legacy renderer until the new renderer is tested end-to-end and visually approved. Do not add paid assets, APIs or compute without explicit approval. No generic primitive-character fallback when artwork is missing. The production minimum remains 150 seconds; final production QC enforces it even though isolated previews can be shorter. A technical render pass does not replace full-video visual inspection. YouTube and TikTok remain disabled.


## Reusable 2D character rigs

The first articulated character rig module is available at
`src/finance_campus/character_rig.py`. A character has a persistent identity,
skin/hair/clothing palette, accessory and a time-ordered joint pose track.
The renderer interpolates joints between poses and draws the character to
transparent RGBA frames. Expressions include worried, focused, relieved,
hopeful, joyful, surprised and others.

Validate and render the included sample:

```bash
python -m finance_campus.cli validate-character-rig examples/character-rig-parent.example.json
python -m finance_campus.cli render-character examples/character-rig-parent.example.json build/character-frames --fps 30
```

The output is an independent transparent character layer sequence. It can be
composited into a directed scene and animated separately from the background
and financial props. This is an initial puppet-rig system: advanced hand
articulation, separate finger controls, lip-sync, multi-character interaction,
inverse kinematics and rig authoring tools remain future milestones.
