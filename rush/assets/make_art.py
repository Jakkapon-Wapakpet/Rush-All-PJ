#!/usr/bin/env python3
"""
สร้างภาพเงาหนังตะลุงทั้งหมดของเกม (PNG โปร่งใส) ลงในโฟลเดอร์ assets/
Generates every shadow-puppet silhouette PNG the GUI uses.

ใช้ตอนพัฒนาเท่านั้น (ต้องมี Pillow: pip install pillow) ตัวเกมเปิด PNG ด้วย tkinter อย่างเดียว
  python3 assets/make_art.py

- คน ปอบ เสือสมิง สิ่งก่อสร้าง และทรัพยากร: วาดด้วยรูปทรง (polygon / ellipse) แล้วเจาะรูลายฉลุ
- วิญญาณเร่ร่อน กระสือ เปรต: แปลงจากภาพหนังตะลุงพื้นขาวใน source/shadow/
"""

import math
import os

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "source")
INK = (26, 15, 12)            # สีเงา (น้ำตาลเกือบดำ เหมือนหนังวัวตัดลาย)
SHADOW = "#9c6a3e"            # เงาจาง (ผีที่ยังไม่โผล่ / ไม่มีใครที่ประตู) ต้องตรงกับ sprites.SHADOW
SCALES = [2, 3, 4, 5, 6, 8, 10]
SMALL = {"food", "water", "scrap", "medicine"}   # ภาพ 10 หน่วย นอกนั้น 16 หน่วย
N = 512                        # วาดใหญ่ก่อนแล้วย่อ ขอบจะเนียน


# ---------------- ตัวช่วยวาด ----------------

def canvas():
    mask = Image.new("L", (N, N), 0)
    return mask, ImageDraw.Draw(mask)


def mirror(points):
    return [(N - x, y) for x, y in points]


def leaf(cx, cy, length, angle, width):
    """ใบไม้/เปลวไฟรูปเลนส์ เริ่มที่ (cx, cy) ชี้ไปทางมุม angle (องศา, 0 = ขึ้น)"""
    rad = math.radians(angle)
    ux, uy = math.sin(rad), -math.cos(rad)
    px, py = -uy, ux
    points = []
    for i in range(21):
        t = i / 20
        w = math.sin(math.pi * t) * width
        points.append((cx + ux * length * t + px * w, cy + uy * length * t + py * w))
    for i in range(20, -1, -1):
        t = i / 20
        w = math.sin(math.pi * t) * width
        points.append((cx + ux * length * t - px * w, cy + uy * length * t - py * w))
    return points


def diamond(d, x, y, r):
    d.polygon([(x, y - r), (x + r, y), (x, y + r), (x - r, y)], fill=0)


def lace(d, xs, ys, r=9):
    """ลายฉลุรูปข้าวหลามตัดเรียงเป็นแถว"""
    for y in ys:
        for x in xs:
            diamond(d, x, y, r)


def eyes(d, y, gap=20, r=7, cx=N // 2):
    d.ellipse((cx - gap - r, y - r, cx - gap + r, y + r), fill=0)
    d.ellipse((cx + gap - r, y - r, cx + gap + r, y + r), fill=0)


# ---------------- คน ----------------

def draw_man():
    m, d = canvas()
    d.ellipse((204, 58, 308, 162), fill=255)
    d.polygon([(200, 100), (212, 42), (236, 62), (256, 28), (276, 60), (300, 40), (312, 100)], fill=255)
    d.rectangle((236, 150, 276, 190), fill=255)
    d.polygon([(178, 185), (334, 185), (318, 335), (194, 335)], fill=255)
    arm = [(182, 190), (150, 202), (118, 322), (146, 330), (180, 236)]
    d.polygon(arm, fill=255)
    d.polygon(mirror(arm), fill=255)
    d.polygon([(198, 330), (252, 330), (246, 478), (204, 478)], fill=255)
    d.polygon([(260, 330), (314, 330), (308, 478), (266, 478)], fill=255)
    d.ellipse((188, 466, 250, 492), fill=255)
    d.ellipse((262, 466, 324, 492), fill=255)
    eyes(d, 108)
    lace(d, (222, 256, 290), (225, 265, 305))
    return m


def draw_woman():
    m, d = canvas()
    d.polygon([(194, 104), (200, 44), (256, 26), (312, 44), (318, 104), (334, 236), (296, 220),
               (256, 176), (216, 220), (178, 236)], fill=255)
    d.ellipse((206, 60, 306, 160), fill=255)
    d.rectangle((238, 150, 274, 190), fill=255)
    d.polygon([(204, 186), (308, 186), (352, 420), (160, 420)], fill=255)
    arm = [(206, 192), (176, 206), (150, 318), (174, 324), (204, 238)]
    d.polygon(arm, fill=255)
    d.polygon(mirror(arm), fill=255)
    d.rectangle((214, 415, 238, 476), fill=255)
    d.rectangle((274, 415, 298, 476), fill=255)
    d.ellipse((200, 466, 248, 490), fill=255)
    d.ellipse((264, 466, 312, 490), fill=255)
    eyes(d, 108, gap=18, r=6)
    lace(d, (230, 256, 282), (250, 300))
    lace(d, (206, 240, 272, 306), (370,), r=11)
    return m


def draw_big():
    m, d = canvas()
    d.ellipse((210, 64, 302, 156), fill=255)
    d.rectangle((206, 60, 306, 92), fill=255)
    d.rectangle((228, 146, 284, 186), fill=255)
    d.polygon([(144, 180), (368, 180), (344, 345), (168, 345)], fill=255)
    arm = [(148, 186), (106, 204), (84, 334), (124, 344), (152, 250)]
    d.polygon(arm, fill=255)
    d.polygon(mirror(arm), fill=255)
    d.ellipse((76, 326, 132, 374), fill=255)
    d.ellipse((380, 326, 436, 374), fill=255)
    d.polygon([(176, 340), (250, 340), (244, 478), (184, 478)], fill=255)
    d.polygon([(262, 340), (336, 340), (328, 478), (268, 478)], fill=255)
    d.ellipse((168, 464, 252, 494), fill=255)
    d.ellipse((260, 464, 344, 494), fill=255)
    eyes(d, 112, gap=18, r=6)
    lace(d, (196, 236, 276, 316), (230, 280), r=11)
    return m


def draw_girl():
    m, d = canvas()
    d.ellipse((150, 120, 210, 210), fill=255)
    d.ellipse((302, 120, 362, 210), fill=255)
    d.ellipse((208, 100, 304, 196), fill=255)
    d.polygon([(204, 140), (214, 92), (256, 80), (298, 92), (308, 140)], fill=255)
    d.rectangle((240, 188, 272, 214), fill=255)
    d.polygon([(214, 210), (298, 210), (304, 320), (208, 320)], fill=255)
    d.polygon([(200, 312), (312, 312), (342, 400), (170, 400)], fill=255)
    arm = [(216, 216), (190, 228), (170, 320), (192, 326), (214, 260)]
    d.polygon(arm, fill=255)
    d.polygon(mirror(arm), fill=255)
    d.rectangle((222, 396, 244, 478), fill=255)
    d.rectangle((268, 396, 290, 478), fill=255)
    d.ellipse((208, 468, 252, 490), fill=255)
    d.ellipse((260, 468, 304, 490), fill=255)
    eyes(d, 148, gap=17, r=6)
    lace(d, (232, 256, 280), (250, 290), r=8)
    lace(d, (214, 256, 298), (360,), r=10)
    return m


def draw_elder():
    m, d = canvas()
    d.ellipse((262, 98, 352, 188), fill=255)
    d.polygon([(262, 150), (180, 168), (150, 250), (170, 340), (300, 340), (306, 250), (300, 190)], fill=255)
    d.polygon([(296, 200), (338, 236), (358, 300), (338, 306), (316, 256), (286, 236)], fill=255)
    d.rectangle((346, 290, 362, 486), fill=255)
    d.polygon([(174, 334), (228, 334), (222, 478), (182, 478)], fill=255)
    d.polygon([(240, 334), (296, 334), (290, 478), (248, 478)], fill=255)
    d.ellipse((166, 466, 230, 492), fill=255)
    d.ellipse((234, 466, 298, 492), fill=255)
    d.ellipse((318, 128, 332, 142), fill=0)
    lace(d, (200, 236, 272), (230, 280), r=10)
    return m


def draw_stranger():
    m, d = canvas()
    d.polygon([(256, 40), (330, 90), (350, 190), (330, 230), (410, 488), (102, 488), (182, 230),
               (162, 190), (182, 90)], fill=255)
    d.ellipse((210, 120, 302, 212), fill=0)
    d.ellipse((222, 132, 290, 200), fill=255)
    eyes(d, 164, gap=16, r=7)
    lace(d, (196, 236, 276, 316), (330, 390), r=11)
    lace(d, (176, 216, 256, 296, 336), (450,), r=9)
    return m


# ---------------- สิ่งก่อสร้าง ----------------

def draw_barricade():
    m, d = canvas()
    for x in (84, 242, 400):
        d.rectangle((x, 160, x + 28, 470), fill=255)
        d.polygon([(x - 4, 162), (x + 14, 112), (x + 32, 162)], fill=255)
    for y in (218, 300):
        d.line((70, y, 442, y + 14), fill=255, width=8)
    for x, y in ((156, 230), (320, 236)):
        d.line((x + 20, y - 6, x + 20, y + 20), fill=255, width=5)
        d.rectangle((x, y + 18, x + 40, y + 98), fill=255)
        lace(d, (x + 20,), (y + 40, y + 76), r=8)
    d.rectangle((40, 466, 472, 486), fill=255)
    return m


def draw_garden():
    m, d = canvas()
    d.chord((40, 380, 472, 560), 180, 360, fill=255)
    for cx in (130, 256, 382):
        d.line((cx, 470, cx, 230), fill=255, width=10)
        for i, (y, angle) in enumerate(((400, -55), (350, 55), (300, -50), (255, 45))):
            d.polygon(leaf(cx, y, 90 - i * 10, angle, 26), fill=255)
        d.polygon(leaf(cx, 240, 70, 0, 22), fill=255)
    lace(d, (120, 200, 312, 392), (440,), r=9)
    return m


def draw_collector():
    m, d = canvas()
    d.ellipse((104, 168, 408, 486), fill=255)
    d.rectangle((186, 124, 326, 186), fill=255)
    d.ellipse((164, 104, 348, 148), fill=255)
    d.ellipse((190, 112, 322, 140), fill=0)
    for x in range(156, 372, 34):
        d.ellipse((x - 9, 300 - 9, x + 9, 300 + 9), fill=0)
    lace(d, (186, 256, 326), (370,), r=12)
    for x, y in ((150, 40), (256, 20), (360, 46)):
        d.polygon([(x, y), (x - 14, y + 34), (x + 14, y + 34)], fill=255)
        d.ellipse((x - 14, y + 22, x + 14, y + 50), fill=255)
    return m


def draw_clinic():
    m, d = canvas()
    d.rectangle((236, 330, 276, 474), fill=255)
    d.rectangle((182, 466, 330, 490), fill=255)
    d.rectangle((146, 306, 366, 334), fill=255)
    d.rectangle((178, 196, 334, 310), fill=255)
    d.polygon([(140, 206), (256, 84), (372, 206)], fill=255)
    d.polygon([(140, 206), (112, 170), (126, 166), (152, 196)], fill=255)
    d.polygon(mirror([(140, 206), (112, 170), (126, 166), (152, 196)]), fill=255)
    d.rectangle((248, 40, 264, 90), fill=255)
    d.polygon([(240, 50), (256, 10), (272, 50)], fill=255)
    d.rectangle((234, 236, 278, 310), fill=0)
    d.pieslice((234, 214, 278, 258), 180, 360, fill=0)
    lace(d, (204, 308), (240, 280), r=10)
    lace(d, (216, 256, 296), (166,), r=9)
    return m


# ---------------- ทรัพยากร ----------------

def draw_food():
    m, d = canvas()
    d.chord((120, 180, 392, 440), 180, 360, fill=255)
    d.pieslice((80, 140, 432, 470), 0, 180, fill=255)
    d.rectangle((80, 296, 432, 312), fill=255)
    d.rectangle((196, 452, 316, 486), fill=255)
    lace(d, (150, 206, 256, 306, 362), (360,), r=13)
    for x, y in ((200, 260), (256, 230), (312, 262)):
        d.ellipse((x - 8, y - 12, x + 8, y + 12), fill=0)
    return m


def draw_water():
    m, d = canvas()
    d.ellipse((130, 200, 382, 452), fill=255)
    d.polygon([(256, 30), (138, 300), (374, 300)], fill=255)
    d.ellipse((186, 290, 226, 370), fill=0)
    return m


def draw_scrap():
    m, d = canvas()
    d.polygon(leaf(256, 210, 170, 0, 54), fill=255)
    d.polygon(leaf(256, 196, 90, 0, 20), fill=0)
    d.rectangle((204, 220, 308, 452), fill=255)
    d.rectangle((140, 446, 372, 486), fill=255)
    lace(d, (256,), (300, 370), r=14)
    return m


def draw_medicine():
    m, d = canvas()
    d.pieslice((90, 150, 422, 400), 0, 180, fill=255)
    d.rectangle((76, 262, 436, 290), fill=255)
    d.polygon([(214, 392), (298, 392), (334, 470), (178, 470)], fill=255)
    d.rectangle((160, 466, 352, 490), fill=255)
    lace(d, (166, 216, 256, 296, 346), (320,), r=12)
    for angle, length in ((-30, 170), (0, 200), (32, 160)):
        d.polygon(leaf(300, 264, length, angle, 30), fill=255)
    for x, y in ((150, 90), (110, 160), (200, 50)):
        d.ellipse((x - 10, y - 14, x + 10, y + 14), fill=255)
    return m


# ---------------- ผีที่วาดเอง ----------------

def draw_pop():
    m, d = canvas()
    for angle in range(-170, 171, 17):
        length = 70 + abs(angle) * 0.9 + (angle % 3) * 12
        d.polygon(leaf(232, 156, length, angle, 11), fill=255)
    d.ellipse((188, 108, 278, 202), fill=255)
    d.polygon([(204, 186), (150, 252), (136, 360), (160, 476), (334, 476), (322, 334), (292, 228)], fill=255)
    d.polygon([(276, 236), (382, 270), (390, 294), (284, 284)], fill=255)
    for angle in (55, 80, 105, 130):
        d.polygon(leaf(384, 282, 56, angle, 6), fill=255)
    for x in range(170, 330, 32):
        d.polygon([(x, 478), (x + 16, 440), (x + 32, 478)], fill=0)
    d.ellipse((228, 140, 244, 156), fill=0)
    d.ellipse((252, 140, 268, 156), fill=0)
    d.polygon([(232, 176), (256, 170), (264, 184), (240, 188)], fill=0)
    lace(d, (190, 230, 270), (300, 350, 400), r=10)
    return m


def draw_saming():
    m, d = canvas()
    d.ellipse((150, 228, 420, 350), fill=255)
    d.ellipse((318, 236, 436, 372), fill=255)
    d.ellipse((96, 206, 250, 346), fill=255)
    d.ellipse((26, 158, 174, 290), fill=255)
    d.polygon([(48, 182), (58, 120), (96, 172)], fill=255)
    d.polygon([(106, 168), (130, 112), (152, 176)], fill=255)
    d.polygon([(4, 236), (112, 250), (4, 292)], fill=0)
    for x in (30, 58):
        d.polygon([(x, 236), (x + 9, 262), (x + 18, 238)], fill=255)
        d.polygon([(x + 4, 292), (x + 13, 268), (x + 22, 292)], fill=255)
    d.polygon([(70, 196), (112, 186), (104, 208)], fill=0)
    legs = [[(124, 318), (162, 318), (146, 470), (104, 470)], [(196, 326), (228, 326), (224, 466), (190, 466)],
            [(338, 336), (374, 336), (384, 468), (350, 468)], [(392, 326), (422, 326), (434, 462), (402, 462)]]
    for leg in legs:
        d.polygon(leg, fill=255)
        x = (leg[2][0] + leg[3][0]) / 2
        d.ellipse((x - 30, leg[2][1] - 14, x + 26, leg[2][1] + 16), fill=255)
    tail = [(430 + 60 * math.sin(t / 10 * math.pi / 1.3), 280 - 190 * t / 10) for t in range(11)]
    d.line(tail, fill=255, width=20, joint="curve")
    for i, x in enumerate(range(196, 424, 30)):
        d.polygon(leaf(x, 230, 78 + (i % 2) * 18, 180 + (i % 3 - 1) * 10, 9), fill=0)
    for x in (70, 104, 138):
        d.polygon(leaf(x, 166, 36, 180, 6), fill=0)
    return m


# ---------------- ผี (แปลงจากภาพ) ----------------

def from_white(path):
    """ภาพหนังตะลุงพื้นขาว: ยิ่งมืดยิ่งทึบ"""
    gray = Image.open(path).convert("L").resize((N, N), Image.LANCZOS)
    return gray.point(lambda g: 255 if g < 70 else 0 if g > 190 else round(255 * (190 - g) / 120))


# ---------------- บันทึก ----------------

def fit(mask, size, color):
    box = mask.point(lambda a: 255 if a > 40 else 0).getbbox() or (0, 0, N, N)
    art = mask.crop(box)
    ratio = min(size / art.width, size / art.height)
    art = art.resize((max(1, round(art.width * ratio)), max(1, round(art.height * ratio))), Image.LANCZOS)
    alpha = Image.new("L", (size, size), 0)
    alpha.paste(art, ((size - art.width) // 2, size - art.height))
    image = Image.new("RGBA", (size, size), color + (255,))
    image.putalpha(alpha)
    return image


def save(name, mask):
    base = 10 if name in SMALL else 16
    shade = tuple(int(SHADOW[i:i + 2], 16) for i in (1, 3, 5))
    for scale in SCALES:
        size = base * scale
        fit(mask, size, INK).save(os.path.join(HERE, f"{name}_{size}.png"))
        fit(mask, size, shade).save(os.path.join(HERE, f"{name}_{size}_{SHADOW[1:]}.png"))
    print("saved", name)


def main():
    for old in os.listdir(HERE):
        if old.endswith(".png"):
            os.remove(os.path.join(HERE, old))
    drawn = {"man": draw_man, "woman": draw_woman, "big": draw_big, "girl": draw_girl, "elder": draw_elder,
             "stranger": draw_stranger, "barricade": draw_barricade, "garden": draw_garden,
             "collector": draw_collector, "clinic": draw_clinic, "food": draw_food, "water": draw_water,
             "scrap": draw_scrap, "medicine": draw_medicine,
             "pop": draw_pop, "saming": draw_saming}
    for name, draw in drawn.items():
        save(name, draw())
    for name in ("spirit", "krasue", "preta"):
        save(name, from_white(os.path.join(SOURCE, "shadow", f"{name}.png")))


if __name__ == "__main__":
    main()
