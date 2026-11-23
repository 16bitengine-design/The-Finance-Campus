# Finance Campus Remotion renderer

This is the first web-rendering layer for the hybrid animation system.

## Included

- **Remotion:** deterministic frame-based composition and MP4 rendering.
- **Rough.js:** hand-drawn SVG illustration primitives for selected whiteboard artwork.
- **SVG stroke drawing:** progressive path reveals through normalized path length and animated dash offset.
- **Canvas 2D:** frame-indexed drawing for moving objects and scene effects. Animation is derived from the Remotion frame number, not wall-clock time.

## Setup

Requires Node.js 20 or newer.

```bash
cd renderer/remotion
npm install
npm run typecheck
npm run compositions
npm run render:demo
```

Open the interactive preview with `npm run studio`.

## Important limitations

The included composition is an integration smoke-test, not an approved production visual. The Rough.js example uses authored vector paths; production artwork must be art-directed scene by scene. Canvas drawing is currently a deterministic demo layer, not yet the multi-character compositor. No generic demo asset should be mistaken for final visual quality.

Remotion rendering is not yet connected to the Python production pipeline or Kokoro audio. The legacy renderer remains active until the hybrid renderer passes end-to-end tests and human visual review.


## Official visual art direction: cinematic 2D cartoon storytelling

The official style is minimalist 2D cinematic cartoon storytelling, using expressive rounded characters, bold dark outlines, distinctive silhouettes, warm brown/beige/cream/charcoal tones, and detailed atmospheric illustrated environments. Multi-character scenes are encouraged when the narrative calls for them. Characters must perform the narrated action and physically interact with story props.

The `FinanceCampusCinematicCartoon` composition is the direction-setting prototype. Preview it with:

```bash
npm run studio
npm run render:cinematic
```

A full-scene still at frame zero is not acceptable. Actions, expressions, prop movement and scene transitions must unfold over time and be aligned to the narration. The sample remains a visual prototype until the Python/Kokoro production pipeline is connected and the rendered result passes human review.
