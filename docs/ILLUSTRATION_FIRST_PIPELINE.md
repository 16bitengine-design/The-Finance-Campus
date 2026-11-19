# Illustration-first production pipeline

## Visual target

Every Finance Campus video is a directed illustrated story. Characters have stable identities, believable expressions, gestures, clothing and prop interactions. Financial actions must visibly happen: cash changes hands, bills arrive, decisions are made, savings accumulate, balances change and charts develop. Captions support the story; they are never the main visual.

The whiteboard is an entrance into the story, not a visual ceiling. Ordered marker reveals establish selected linework and focal details; completed illustrations then move into layered motion graphics with character acting, prop animation, camera movement and transitions.

## Required scene architecture

A scene is authored in semantic layers, not as a flat list of primitive shapes:

1. **Background:** location, architecture, atmosphere and environmental details.
2. **Midground:** characters, furniture and large story props.
3. **Foreground:** hands, money, bills, devices and other focal objects.
4. **Motion graphics:** charts, labels, timelines and explanatory overlays.
5. **Captions:** a reserved safe area that never obscures faces, hands or important actions.

The visual_direction contract in finance_campus.visual_direction defines the director's brief: setting, takeaway, shot composition, depth layers, character identity and performance, ordered action beats with visible results, scene continuity and caption-safe boundaries.

## Character bible and continuity

Character IDs are stable within a production. Their identity description and clothing remain consistent between scenes. Expressions, gaze, posture and gestures change to perform the story. A character must interact with a named prop or part of the environment; a posed character beside floating icons is not sufficient.

Asset production must retain reusable character turnarounds, expression/pose references and separated layers. Each scene must identify which character and prop assets it uses. Missing assets must fail the scene build rather than silently fall back to generic stick figures.

## Animation rules

- Every meaningful narration beat maps to a visible action, reaction, decision or consequence.
- Action beats are ordered against the actual narration timeline.
- Objects have state: position, owner, visibility and relevant financial value/state.
- Money and props move with a visible origin and destination; savings and charts change over time rather than appearing as unexplained finished graphics.
- Transitions preserve a continuity anchor (carried object, camera movement, drawn line or morph).
- Whiteboard reveals are choreographed as drawing actions, then hand off to full-colour motion graphics.
- No fabricated word timings. Use timing supplied by Kokoro or verified audio analysis.

## Render architecture

script beats -> visual direction -> character/prop asset plan -> layered illustration assets -> whiteboard reveal -> motion-graphics animation -> Kokoro narration/caption sync -> FFmpeg master -> technical QC -> human visual review

Keep Kokoro as the narration engine and FFmpeg for final encoding. The current Pillow renderer may remain as a legacy fallback for old storyboards during migration, but it is not the quality target and must not be used to claim the new visual standard has been achieved.

No paid image APIs, paid assets or paid compute may be introduced under the current zero-cost policy without explicit user approval. If an open-source path cannot deliver the required asset quality within available compute, stop and explain the constraint rather than disguising primitive artwork as professional illustration.

## Release gate

A technical pass is not a visual pass. The contact sheet and complete video must be inspected. Human review remains mandatory; any visual rubric score below 4/5 requires revision. Captions and disclaimers must be readable and must not overlap key action. Publishing remains disabled until the user explicitly approves the visual quality.

## Layered animation preview commands

The first executable compositor is `finance_campus.layered_animation`. It consumes transparent PNG artwork authored as separate background, character and prop layers, then interpolates position, scale, rotation, opacity and reveal progress at the requested frame time. Layers are composited by z-order. Supported reveals are directional wipes that can serve as a whiteboard-style introduction before the full-colour artwork is fully visible.

Validate a scene manifest:

`python -m finance_campus.cli validate-layered-scene examples/layered-kitchen-scene.example.json`

Render a PNG frame sequence (the asset directory must contain the named scene-specific artwork):

`python -m finance_campus.cli render-layered-scene examples/layered-kitchen-scene.example.json build/layered-preview --asset-root assets/scenes/payday-kitchen --fps 30`

The example manifest deliberately references a character pose, kitchen environment, bill and savings envelope as independent assets. It is an animation specification, not a claim that those production artwork files have already been created. Missing assets fail closed; there is no generic-character fallback.

Current milestone boundary: the compositor and preview command are implemented, but the legacy end-to-end MP4 production pipeline has not yet been switched to this compositor. That integration requires a complete, reviewed layered artwork pack and narration/action timing alignment. Until then, the old renderer remains legacy-only and cannot be treated as meeting the new visual target.
