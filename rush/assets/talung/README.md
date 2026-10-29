# Nang Talung game artwork

Generated and edited with ImageGen on 2026-10-28. Runtime crops, scales and
composites these assets with Pillow (`../../talung_ui/art.py`); all interface
text and buttons are live Tkinter controls.

- `survivors-color.png`: 1536×1024 RGBA atlas, three columns by two rows,
  ordered man, woman, big / girl, elder, concealed stranger.
- `ghosts.png`: wandering spirit, Krasue, Preta, Phi Pop and Saming, left to
  right. Atlas spacing is recorded in `art.py`; it is not a uniform grid.
- `stage-color.png`: colored night village plate used for menu, story and
  portrait backgrounds.
- `stage-game.png`: edited plate with a smaller pavilion for the game panorama.
- `logo.png`: transparent title “มิติผี” with GHOST REALM underneath.

Resource and building icons (`../<name>_40.png`, `../<name>_64.png`) are
silhouettes tinted at runtime with muted semantic colors.

The gameplay camera and people share one scale and ground coordinate; the
panorama grows from 210 to 320 pixels to retain the pavilion roof on wide views.
