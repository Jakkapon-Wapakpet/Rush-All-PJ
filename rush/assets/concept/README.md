# Atmospheric Thai horror art trial

Run from `rush`: `python gui_art_preview.py` (requires Pillow).
Run the bounded layout and gameplay check: `python gui_art_preview.py --check`.

This trial reuses the existing Tkinter UI and rules. It shows one environment
and one sample character, Ken, at 150 px tall in a 360 px scene. Other portraits,
ghosts and UI assets remain the original artwork. Ken in the scene is a fixed
art sample, not a representation of the current survivor roster.

The trial starts a new game each time and writes only `preview-save.json` and
`preview-history.json` here. The normal game's save files are not loaded or changed.
The normal entry points `gui.py` and `main.py` are unchanged.

## Image generation

Both PNG files were made using the built-in image generation tool.
`pavilion-night-v1.png` is an environment concept, not a layered final game scene.
`ken-v1.png` is an RGBA character cutout; its soft lighting edges are preserved.

Character prompt:

> Use case: stylized-concept. Asset type: single transparent full-body character sprite for a Thai atmospheric horror survival management game. Subject: Ken, an ordinary Thai young adult man, short black hair, faded muted olive overshirt over dark shirt, worn dark trousers and practical shoes, a small canvas crossbody scavenging bag. Slightly tense, watchful expression, grounded natural proportions, standing still in a relaxed three-quarter front view with both feet visible, hands visible and empty. Semi-realistic digital painting with visible soft brush strokes, restrained details and strong readable silhouette suitable for display only 120 pixels tall. Warm amber candlelight gently illuminates his face and one shoulder against cool muted forest shadows, coherent with an old Thai forest pavilion at night. Single isolated person centered, full body including shoes within frame, generous transparent margins. Genuine transparent background, no scenery, no ground plane, no cast shadow, no props outside the person, no writing, no border, no gore, no weapons, no photorealistic photograph. This is one character asset, not a character sheet or multiple poses.

Environment direction: semi-realistic painterly old Thai wooden pavilion in a
misty forest at night, sacred white threads and amber candles, muted forest
greens and blue-black shadows, atmospheric dread without gore, people or text.

Verification: images load in Tkinter; scene scales at 1360x860, 1220x760 and
1600x960; assignment and one seeded end-day complete with isolated saves.
Desktop screenshot inspection was unavailable in this session.
