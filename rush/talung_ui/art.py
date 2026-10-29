"""Nang Talung sprites and stage, fitted to game widgets at runtime."""
from pathlib import Path
from PIL import Image, ImageOps, ImageTk

ART_DIR = Path(__file__).resolve().parents[1] / "assets" / "talung"
PEOPLE = ("man", "woman", "big", "girl", "elder", "stranger")
GHOST_SPRITES = ("spirit", "krasue", "preta", "pop", "saming")
RESOURCE_ICONS = {"food", "water", "incense", "holy_water"}   # ไอคอนเล็ก (assets/<name>_40.png) นอกนั้น 64 px
_sources = {}
_images = {}
LANCZOS = getattr(Image, "Resampling", Image).LANCZOS  # Pillow < 9.1 has no Image.Resampling


def source(name):
    if name not in _sources:
        if name in PEOPLE:
            index = PEOPLE.index(name)
            with Image.open(ART_DIR / "survivors-color.png") as atlas:
                column, row = index % 3, index // 3
                top, bottom = (0, 512) if row == 0 else (512, atlas.height)
                image = atlas.crop((column * 512, top, (column + 1) * 512, bottom)).convert("RGBA")
        elif name in GHOST_SPRITES:
            index = GHOST_SPRITES.index(name)
            with Image.open(ART_DIR / "ghosts.png") as atlas:
                edges = (0, 340, 682, 1060, 1435, atlas.width)
                image = atlas.crop((edges[index], 0, edges[index + 1], atlas.height)).convert("RGBA")
        else:
            icon_size = 40 if name in RESOURCE_ICONS else 64
            with Image.open(ART_DIR.parent / f"{name}_{icon_size}.png") as icon:
                image = icon.convert("RGBA")
            colors = {"food": "#9da968", "water": "#6facc7", "incense": "#edb15f",
                      "holy_water": "#9fcac5", "vegetable_patch": "#889d61", "rain_barrel": "#6d9aa5"}
            alpha = image.getchannel("A")
            image = Image.new("RGBA", image.size, colors.get(name, "#ba9569"))
            image.putalpha(alpha)
        bounds = image.getchannel("A").point(lambda value: 255 if value > 64 else 0).getbbox()
        _sources[name] = image.crop(bounds) if bounds else image
    return _sources[name]


def sprite(name, scale=4, shadow=False):
    """Existing sprite API, including hidden/unseen ghost silhouettes."""
    key = (name, scale, shadow)
    if key not in _images:
        size = (10 if name in RESOURCE_ICONS else 16) * scale
        image = ImageOps.contain(source(name), (size, size), LANCZOS)
        if shadow:
            alpha = image.getchannel("A").point(lambda value: round(value * 0.42))
            image = Image.new("RGBA", image.size, "#333333")
            image.putalpha(alpha)
        _images[key] = ImageTk.PhotoImage(image)
    return _images[key]


class Stage:
    def __init__(self, filename="stage-game.png"):
        with Image.open(ART_DIR / filename) as image:
            self.source = image.convert("RGB")
        self.size = None
        self.image = None
        self.game_camera = filename == "stage-game.png"
        self.scale = 1
        self.offset = (0, 0)

    def fit(self, width, height):
        if self.size != (width, height):
            self.scale = max(width / self.source.width, height / self.source.height)
            scaled = self.source.resize((round(self.source.width * self.scale), round(self.source.height * self.scale)), LANCZOS)
            left = (scaled.width - width) // 2
            # Keep the pavilion roof and the yard in view. Actors use this same camera.
            top = round(self.source.height * .79 * self.scale - height * .90) if self.game_camera else scaled.height - height
            top = max(0, min(scaled.height - height, top))
            self.offset = (left, top)
            image = scaled.crop((left, top, left + width, top + height))
            self.image = ImageTk.PhotoImage(image)
            self.size = (width, height)
        return self.image

    def point(self, x, y):
        """Normalized plate coordinates, transformed into the current viewport."""
        return (x * self.source.width * self.scale - self.offset[0],
                y * self.source.height * self.scale - self.offset[1])


def logo(width, height):
    key = ("logo", width, height)
    if key not in _images:
        with Image.open(ART_DIR / "logo.png") as image:
            image = image.convert("RGBA")
            bounds = image.getchannel("A").point(lambda v: 255 if v > 64 else 0).getbbox()
            image = ImageOps.contain(image.crop(bounds), (width, height), LANCZOS)
        _images[key] = ImageTk.PhotoImage(image)
    return _images[key]


def portrait(name, width, height, shadow=False):
    """Compose game art at widget size; no text is baked into the artwork."""
    key = ("portrait", name, width, height, shadow)
    if key not in _images:
        with Image.open(ART_DIR / "stage-color.png") as image:
            forest = image.crop((0, 0, round(image.width * 0.31), image.height))
            background = ImageOps.fit(forest, (width, height), LANCZOS).convert("RGBA")
        background.alpha_composite(Image.new("RGBA", background.size, (6, 20, 29, 95)))
        figure = ImageOps.contain(source(name), (round(width * 0.82), height - 14), LANCZOS)
        if shadow:
            alpha = figure.getchannel("A").point(lambda v: round(v * 0.6))
            figure = Image.new("RGBA", figure.size, "#0c151c")
            figure.putalpha(alpha)
        background.alpha_composite(figure, ((width - figure.width) // 2, height - figure.height - 6))
        _images[key] = ImageTk.PhotoImage(background)
    return _images[key]
