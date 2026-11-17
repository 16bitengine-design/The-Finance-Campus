# Professional whiteboard animation direction

## Purpose

The Finance Campus must produce authored visual stories, not generic slides with animated labels. The renderer is a production instrument; the storyboard is the director's plan.

The creative target is premium, hand-drawn whiteboard storytelling supported by restrained motion graphics. There is no on-screen presenter. Illustrated characters may appear as actors inside the story.

## Non-negotiable visual principles

1. **Narration-to-action translation**: convert each meaningful narration beat into a visible action, reaction, consequence, comparison, or transformation. Do not simply place nouns from the narration on screen.
2. **Character performance**: characters need readable posture, gesture, facial expression, gaze direction, and purposeful interaction with props. A character should not be a generic static stick figure when the story calls for emotion or decision-making.
3. **Compositional direction**: plan focal point, hierarchy, negative space, scale, visual balance, caption-safe area, and intended eye path for every shot.
4. **Sequential drawing**: reveal strokes in the order a skilled illustrator would draw them. The hand and marker should travel between strokes, lift when repositioning, and use the colour of the active stroke. Do not leave a hand attached to a completed illustration.
5. **Cause and effect**: show money moving, bills arriving, choices being made, balances changing, barriers appearing, and consequences unfolding. Arrows alone are not a substitute for action.
6. **Scene continuity**: use match cuts, object transformations, travelling lines, carried props, and motivated transitions. Avoid unrelated collections of objects appearing in a new layout at every scene.
7. **Visual variety**: select a visual concept for each video based on its actual story. Vary shot scale, angle, character staging, metaphor, diagram form, pacing, and visual rhythm. Deterministic retries must remain identical.
8. **Restraint and legibility**: avoid simultaneous competing animations, excessive labels, decorative clutter, tiny text, and captions that dominate the illustration.

## Required storyboard direction per scene

A directed scene should carry structured data for:

- story beat and intended viewer takeaway;
- visual metaphor or concrete situation;
- shot size and composition;
- character state, expression, pose, gaze, and action;
- prop state and interaction;
- ordered drawing/action beats with start time and duration;
- motion paths and easing where relevant;
- transition into the next scene;
- narration timing and caption-safe boundaries;
- a short rationale explaining why the visual communicates the idea.

All timing must be grounded in the narration/audio timeline. Never invent word-level synchronization when the TTS engine does not supply timestamps.

## Character and illustration direction

Use a consistent, reusable character design language within each video. Keep proportions, clothing, line weight, and visual identity stable. Change expressions and poses to communicate acting rather than changing character identity. Props should have coherent scale and remain spatially consistent when carried across shots.

The marker hand is an artist's drawing hand, not a cursor. Its nib should meet the active stroke tip; it should lift and reposition between disconnected strokes, rotate naturally with stroke direction, and never cover the focal detail for longer than necessary. The drawing hand should be hidden during pauses and after a drawing is complete.

## Production pipeline stages

1. Script beat analysis.
2. Visual concept and metaphor selection.
3. Scene direction and continuity planning.
4. Illustration construction and character posing.
5. Stroke ordering and hand choreography.
6. Motion and transition timing against narration.
7. Render and encode.
8. Technical quality checks.
9. Contact-sheet and full-video human visual review.

## Visual quality review rubric

Score each dimension from 1 to 5:

- narration is visibly explained;
- composition and focal hierarchy;
- character expression and acting;
- drawing-hand believability;
- motion purpose and timing;
- scene continuity and transitions;
- visual variety and originality;
- caption and typography restraint;
- brand consistency and accessibility.

A production is not visually approved merely because it renders or passes technical checks. Any score below 4 requires revision; semantic accuracy and caption/disclaimer legibility are mandatory pass/fail checks. Human review remains mandatory until a validated visual evaluator exists.

## Current implementation status

The current deterministic storyboard builder is an early prototype: it maps a small set of financial keywords to predetermined object compositions. Its script-specific offsets and active drawing hand are useful foundations, but they do not yet meet this professional direction standard.

Do not describe the current renderer as studio-grade. Implement the richer scene-direction schema incrementally, preserve deterministic rendering, add tests for every new behaviour, and inspect actual rendered samples before claiming visual improvement.
