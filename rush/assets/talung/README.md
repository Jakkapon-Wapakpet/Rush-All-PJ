# Nang Talung game artwork

Generated using the built-in image generation tool in this chat on 2026-10-28.

- `survivors.png`: six RGBA sprites. Top: Ken/man, Prae/woman, Big. Bottom:
  bob-haired girl, elder with cane, unidentified hooded newcomer. Reference:
  `../concept/talung-survivors-v1.png`.
- `ghosts.png`: wandering spirit, Krasue, Preta, Phi Pop and Saming, left to
  right. Reference: `../concept/talung-ghosts-v1.png`.
- `stage.png`: empty monochrome puppet-stage plate. Reference:
  `../concept/talung-scene-gray-red-v2.png`. People and ghosts are removed
  so the game can render the actual roster and available ghost tiers.

Generation briefs: simplified flat Nang Talung silhouettes, sparse off-white
cutout contours, no realistic rendering, modest ordinary Thai survivors,
distinct profiles. Ghosts alone have tiny dried-crimson accents. The stage is
neutral gray cloth with a small rural pavilion, dark ground and framing trees.

Atlas spacing is recorded in `../../talung_ui/art.py`; it is not a perfectly
uniform grid. Alpha channels are preserved. Runtime scaling and cell extraction
use Pillow. Existing resource/building icons are reused with muted semantic colors.

`gui-desktop.png` and `gui-small.png` are real Windows window captures from
synthetic integration-test state, not the user's save. The small capture stresses
six people, possession, a newcomer and the final day. Captures are evidence,
not game artwork.

## Current colored direction

The later user-approved direction replaces grayscale throughout with a dark
indigo management interface, colored clothes and props, amber actions and
moss-green jobs. The original monochrome plates remain as earlier concepts.

- `survivors-color.png`: 1536×1024 RGBA atlas, three columns by two rows,
  ordered man, woman, big / girl, elder, concealed stranger.
- `stage-color.png`: colored night village plate used for menu, story and
  portrait backgrounds.
- `stage-game.png`: edited plate with a smaller pavilion for the game panorama.
- `logo.png`: transparent title “มิติผี” with GHOST REALM underneath.

Exact generation instructions are preserved beside each image as
`<asset-name>.prompt.txt`. These images were generated/edited with ImageGen
in this chat on 2026-10-28. Runtime crops, scales and composites these assets;
all interface text and buttons are live Tkinter controls.

`gui-desktop.png` and `gui-small.png` show the current colored implementation.
The gameplay camera and people share one scale and ground coordinate; the
panorama grows from 210 to 320 pixels to retain the pavilion roof on wide views.
