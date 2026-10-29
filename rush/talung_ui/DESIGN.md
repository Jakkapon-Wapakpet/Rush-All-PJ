---
name: มิติผี — Ghost Realm
description: A colorful Nang Talung shelter-management game for Windows desktop.
colors:
  bg: "#08141d"
  panel: "#10212b"
  card: "#142c35"
  card-hover: "#203d45"
  line: "#796448"
  text: "#f0e2c8"
  muted: "#c4b69f"
  accent: "#eab363"
  accent-dark: "#d09644"
  ink: "#171a15"
  red: "#e18b82"
  red-dark: "#733d39"
  blue: "#86b9c6"
  purple: "#b6a2c5"
  disabled: "#25353c"
  screen: "#152d36"
  screen-edge: "#0b202b"
  moon: "#eee1c5"
  puppet: "#0a1119"
  far: "#345563"
  green: "#a6bf80"
  job: "#354d33"
typography:
  dialog-title:
    fontFamily: "Leelawadee UI"
    fontSize: "20pt"
    fontWeight: 700
  person-name:
    fontFamily: "Leelawadee UI"
    fontSize: "16pt"
    fontWeight: 700
  body:
    fontFamily: "Leelawadee UI"
    fontSize: "11pt"
    fontWeight: 400
  label:
    fontFamily: "Leelawadee UI"
    fontSize: "10pt"
    fontWeight: 400
rounded:
  square: "0px"
spacing:
  body-horizontal: "18px"
  body-vertical: "10px"
  column-gap: "14px"
  card-horizontal-gap: "8px"
  card-vertical-gap: "9px"
components:
  button-default:
    backgroundColor: "{colors.card}"
    textColor: "{colors.text}"
    rounded: "{rounded.square}"
    padding: "7px 12px"
  button-default-hover:
    backgroundColor: "{colors.card-hover}"
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.ink}"
    rounded: "{rounded.square}"
  button-primary-hover:
    backgroundColor: "{colors.accent-dark}"
  button-job:
    backgroundColor: "{colors.job}"
    textColor: "{colors.text}"
    rounded: "{rounded.square}"
  survivor-card:
    backgroundColor: "{colors.card}"
    textColor: "{colors.text}"
    rounded: "{rounded.square}"
---

# Design System: มิติผี — Ghost Realm

## Overview

มิติผี is a native Python/Tkinter management game set around a lantern-lit Thai pavilion. Colored Nang Talung figures, indigo forest scenery, warm parchment lettering and amber actions establish the implemented world. People wear distinct green, coral, blue and ochre clothing; items and controls also retain color.

This records `main.py`, `screens.py`, `art.py` and the shared widgets in `../gui_theme.py`. `TalungApp` inherits rules, saves and remaining screens from `../gui.py`. `python gui.py` opens this interface. This document governs presentation, not game balance. The direction comes from the approved conversation and existing native implementation; there is no PRODUCT.md, recorded design-gate artifact or composition-reproduction measurement. Flat native button frames and the system-font gameplay header are actual adaptations; pixel-identical reproduction of the approved mockup is not established.

Key characteristics:

- A compact scene above three large survivor cards per row on the left.
- A separate visitor and management panel on the right.
- A fully visible roster and persistent daily actions; only the right management content scrolls.
- Nang Talung contours and colored materials throughout menus, portraits and reports.

## Colors

The midnight blue and indigo artwork sits inside dark blue-green native surfaces. The exact shared widget palette is in the frontmatter; its hyphenated names map to underscore names in Python. `amber` aliases `accent` in code.

### Primary

- **Lantern amber (`accent`, `accent-dark`):** primary decisions, the end-day action, selected language and active-tab text. Filled primary buttons use dark `ink` lettering; hover deepens the amber.

### Secondary

- **Moss (`job`):** job selectors, accepting a visitor, building and difficulty choices. **Leaf (`green`)** marks healthy HP, completed construction and food-chart data.
- **Water blue (`blue`):** water-chart data. Colored resource icons distinguish food, water, offerings and holy water before their labels are read.

### Tertiary

- **Danger coral (`red`):** infection labels and outlines, low HP, urgent food/water and loss information. **Dark red (`red-dark`)** marks the exile action. Danger is accompanied by words or a numerical value.
- **Lavender (`purple`):** retained shared theme role for inherited screens; it does not replace the colored clothing or action roles.

### Neutral

- `bg`, `panel`, `card` and `card-hover` separate the window, right panel, cards and pointer feedback. `line` provides warm fine boundaries. `text` and `muted` provide primary and supporting parchment lettering. `disabled` forms meter tracks.
- `screen`, `screen-edge`, `moon`, `puppet` and `far` remain shared scene roles. The main visible landscape is authored raster artwork, with its own richer palette.

**The Color Role Rule.** Preserve amber for primary decisions, moss for work and coral for danger while retaining the colors in clothing, items and landscape.

## Typography

Leelawadee UI serves Thai and English. Tk font sizes are points; geometric dimensions are pixels. Shared body copy is regular (11pt), small copy regular (10pt), and the `theme.font` helper supplies bold labels and headings. No custom web-font loading is involved.

The header title is bold (20pt in Thai, 15pt in English), resource values bold (17pt), survivor names bold (16pt, or 12pt in compact cards), visitor names bold (19pt), panel headings generally bold (17–18pt), and dialog headings bold (20pt). Job controls are bold (11pt, or 10pt in compact cards); tabs are bold (10pt). The main end-day action is bold (13pt). The title menu uses the authored logo image rather than reconstructing its lettering as a font.

**The Live Text Rule.** Keep names, status, numbers and controls as native text; portrait artwork contains no baked-in interface copy. The displayed Thai game name is มิติผี.

## Layout

The default client area is 1440 × 900, with a minimum of 1180 × 780. The header combines title, day, four resource groups, menu and language controls. A thin divider precedes the body. Horizontal outer padding is 18 pixels; body and footer vertical padding is 10 pixels.

The expanding left side holds the landscape, survivor count/unassigned count and a non-scrolling three-column roster in an ordinary Tk frame. The right panel stays 350 pixels wide, separated by 14 pixels, and has its own scroll region. Six management destinations occupy a three-column tab grid: Gate, Build, Tonight, Shrine, Ghosts and Log. Advanced-only tabs remain subject to existing game rules. The selected tab changes the right panel; the gate presents the visitor there.

The scene height responds to its width: `round(width / 5.5)`, clamped to 210–320 pixels. The gameplay camera uses `stage-game.png`; its crop keeps the pavilion roof and yard in view. `Stage.fit` and `Stage.point` share the same scale and offset for scenery and actor placement. Survivors stand on the plate's normalized yard baseline (0.79), spread around horizontal 0.40; the visitor stands near 0.82. Actor size derives from the same camera scale, so people remain grounded as the scene resizes.

Roster columns have equal weight and retain three columns at the supported minimum size. Up to three people share one row; four to six occupy two equal-height rows, so the full roster remains visible. Card gaps are 8 pixels horizontally and 9 vertically. Portraits fit their available width and height on resize. With more than three people, each card places its portrait in the left 40% and information in the right 60%, with shortened jobs, numeric HP, a meter and any possession label visible. No mobile stacking breakpoint is implemented.

The footer remains visible below the body. Feedback and defense/threat appear on the left; automatic assignment and the amber end-day button sit on the right. Title and story overlays intentionally cover the management layout while open.

## Elevation & Depth

Native frames remain flat, with tonal layers and one-pixel outlines instead of drop shadows. Landscape depth comes from illustrated forest, buildings, lantern light and foreground foliage. Portraits composite a darkened forest crop with a colored figure. The title adds a horizontal lighting mask to protect menu readability. Hidden/unseen variants dim the figure itself; they are not elevation effects.

## Shapes

Panels, cards, meters and buttons use square corners. Thin warm outlines frame cards and the right panel; possessed cards switch to coral. HP is a horizontal seven-pixel meter. Fine threat tracks and rectangular portrait mounts keep the management surfaces clear, while pavilion rooflines, foliage and puppet cutouts provide the organic silhouettes.

## Components

- **Buttons:** flat native controls have a one-pixel boundary, amber focus highlight, hand cursor and immediate hover fill. Default padding is 12 pixels horizontally and 7 vertically; the footer primary uses 22 and 9. Disabled job controls retain muted text. Hover is not animated.
- **Survivor cards:** up to three people use tall cards with a portrait above their information. Four to six use compact landscape cards: portrait left, name, HP, meter and moss job dropdown right. Portraits resize to the available space. Compact controls use short job names; infection displays the concise ถูกผีสิง / Possessed label and coral outline, with inherited attention behavior. HP uses leaf at 70 or above, amber at 40–69 and coral below 40. The ellipsis opens full details, skills, rename and exile controls. Starting names are กล้า, พิกุล and สิงห์; generated people draw from the updated random-name pool. Loading migrates former built-in names while retaining other names.
- **Job menus:** native popup menus list assignable jobs, use moss selection feedback and disable jobs rejected by the existing game checks. Inspection or completed-game status disables the card selector.
- **Visitor panel:** a concealed stranger portrait, name, inspection status and three decisions occupy the gate tab. Check shadow is amber, accept is moss and reject uses the standard dark treatment. Details expand beneath the decisions. The no-visitor state supplies explanatory text and a dimmed portrait.
- **Tabs and scrolling:** active tabs have a brighter dark surface and amber text. Gate adds an exclamation mark when a visitor waits. The right panel resets to the top after switching tabs. The right management panel uses a ten-pixel vertical scrollbar and wheel routing; the roster has no scrollbar.
- **Title and story:** the title uses `stage-color.png`, the authored `logo.png`, a left menu and three colored figures in the yard. Start/continue is amber. The introduction places scenery and paginated text side by side, with next, skip, Enter and Escape controls.
- **Dialogs and reports:** person details, difficulty choice, help and night reports share dark panels and amber headings. Help and night logs scroll while their return actions remain visible; the night report can resize. Endings also appear in a banner above the roster.
- **Artwork:** `survivors-color.png` is a three-column, two-row atlas for man, woman, big, girl, elder and stranger; each column is 512 pixels. `ghosts.png` provides spirit, krasue, preta, pop and saming. Sprites trim their alpha bounds and preserve aspect ratio with Lanczos resizing. Resource/building icons reuse legacy alpha silhouettes with colored fills. Card portraits composite the figure over `stage-color.png`; the gameplay plate is separate.

## Do's and Don'ts

- **Do** preserve the colored Nang Talung world across management, title, narrative and dialogs.
- **Do** keep the scene above the three-column roster, the visitor/management panel on the right and daily actions in the persistent footer.
- **Do** use the shared stage camera for actor placement and sizing, keeping feet on the yard and the pavilion roof visible.
- **Do** preserve existing rule checks, state, saves and concealed information when changing presentation.
- **Do** show the selected campaign duration consistently: Easy 15, Normal 20, Nightmare 25 days. Difficulty cards display durations; header, continue action and graphs follow the current save. Ghost catalog arrival dates use the same schedule as raids and omens.
- **Don't** restore the obsolete grayscale direction or single-column roster from the previous design document.
- **Don't** rename the game by adding a prefix to มิติผี, or bake changing game copy into images.
- **Don't** interpret the three reference captures as proof of every dialog, English text state or platform. They evidence the Thai title menu, desktop gate and crowded late-day/infection view; implementation details above are also grounded in the source.
