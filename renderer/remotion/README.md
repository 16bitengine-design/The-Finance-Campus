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
