#!/usr/bin/env python3
"""
Art Module - GHOST REALM (มิติผี)
ภาพ pixel art ตอนสำคัญ วาดด้วยโค้ดแล้วพิมพ์ด้วยตัว ▀ (1 ตัวอักษร = 2 พิกเซล บน/ล่าง) สี truecolor
Pixel-art scenes drawn in code and printed with half-block characters.
"""

import math
import random


def blend(base, top, alpha: float):
    """ผสมสี top ลงบน base ตามความทึบ alpha (base เป็น None = พื้นหลัง Terminal)"""
    if base is None:
        base = (0, 0, 0)
    return tuple(round(b + (t - b) * alpha) for b, t in zip(base, top))


def lerp(a, b, t: float):
    """ไล่สีจาก a ไป b"""
    t = max(0.0, min(1.0, t))
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def canvas(width: int, height: int, fill=None) -> list:
    """สร้างผืนผ้าใบพิกเซล (None = โปร่งใส)"""
    return [[fill] * width for _ in range(height)]


def render(pixels: list) -> list:
    """แปลงพิกเซลเป็นบรรทัดข้อความ (2 แถวพิกเซลต่อ 1 บรรทัด)"""
    lines = []
    for y in range(0, len(pixels), 2):
        top_row = pixels[y]
        bottom_row = pixels[y + 1] if y + 1 < len(pixels) else [None] * len(top_row)
        line = ""
        for top, bottom in zip(top_row, bottom_row):
            if top is None and bottom is None:
                line += "\033[0m "
            elif top is None:
                line += "\033[0m\033[38;2;%d;%d;%dm▄" % bottom
            elif bottom is None:
                line += "\033[0m\033[38;2;%d;%d;%dm▀" % top
            else:
                line += "\033[38;2;%d;%d;%d;48;2;%d;%d;%dm▀" % (top + bottom)
        lines.append(line + "\033[0m")
    return lines


def glow(pixels: list, cx: float, cy: float, radius: float, color, strength: float) -> None:
    """แสงเรืองรอบจุด (cx, cy)"""
    for y, row in enumerate(pixels):
        for x, base in enumerate(row):
            distance = math.hypot(x - cx, y - cy)
            if distance < radius:
                row[x] = blend(base, color, strength * (1 - distance / radius) ** 2)


def sprinkle_stars(pixels: list, rng: random.Random, count: int, max_y: int) -> None:
    """โรยดาวบนท้องฟ้า"""
    width = len(pixels[0])
    for _ in range(count):
        x, y = rng.randrange(width), rng.randrange(max_y)
        pixels[y][x] = blend(pixels[y][x], (255, 250, 225), rng.uniform(0.4, 1.0))


# ---------- ฉากกลางคืน: พระจันทร์ ศาลา และผี ----------

def night_scene() -> list:
    width, height = 60, 26
    horizon = 21
    rng = random.Random(7)
    pixels = [[lerp((8, 6, 24), (70, 24, 78), y / horizon) for _ in range(width)] for y in range(height)]
    sprinkle_stars(pixels, rng, 32, horizon - 4)

    # พระจันทร์เสี้ยว + แสงเรือง
    glow(pixels, 11, 7, 11, (255, 230, 170), 0.35)
    for y in range(height):
        for x in range(width):
            if math.hypot(x - 11, y - 7) <= 5 and math.hypot(x - 14, y - 5.5) > 4.4:
                pixels[y][x] = lerp((255, 246, 200), (230, 190, 120), (x - 6) / 8)

    # ศาลาไทย (เงาดำ) หลังคาซ้อนสองชั้น ช่อฟ้าปลายงอน และตะเกียงข้างใน
    silhouette = (14, 6, 20)
    center = 40
    lamp = (center, 17)
    glow(pixels, lamp[0], lamp[1], 9, (255, 150, 60), 0.55)
    for y in range(6, 15):
        half = 2 + (y - 6) * 1.6 if y < 11 else 4 + (y - 9) * 2.2
        for x in range(round(center - half), round(center + half) + 1):
            pixels[y][x] = silhouette
    for side in (-1, 1):
        tip = round(center + side * (4 + 5 * 2.2))
        pixels[13][tip + side] = silhouette
        pixels[12][tip + side * 2] = silhouette
        pixels[9][round(center + side * 7)] = silhouette
    pixels[4][center] = pixels[5][center] = silhouette
    for x in (center - 9, center - 8, center + 8, center + 9):
        for y in range(15, horizon):
            pixels[y][x] = silhouette
    for x in range(center - 12, center + 13):
        pixels[horizon - 1][x] = silhouette
    pixels[lamp[1]][lamp[0]] = (255, 214, 120)
    pixels[lamp[1] - 1][lamp[0]] = (110, 60, 30)

    # ผีลอย (โปร่งแสงนิดๆ) ชายผ้าเป็นคลื่น
    ghost_x, ghost_y = 21, 11
    glow(pixels, ghost_x, ghost_y + 3, 8, (170, 220, 255), 0.25)
    for y in range(ghost_y - 3, ghost_y + 8):
        for x in range(ghost_x - 4, ghost_x + 5):
            dx, dy = x - ghost_x, y - ghost_y
            inside = math.hypot(dx, dy) <= 4 if dy < 0 else abs(dx) <= 4
            if dy >= 6 and (x + y) % 3 == 0:
                inside = False
            if dy == 7 and (x + y) % 3 != 1:
                inside = False
            if inside:
                shade = lerp((240, 248, 255), (170, 200, 240), (dx + 4) / 8)
                pixels[y][x] = blend(pixels[y][x], shade, 0.9)
    for eye in (ghost_x - 2, ghost_x + 1):
        pixels[ghost_y][eye] = (20, 10, 30)
        pixels[ghost_y + 1][eye] = (20, 10, 30)
    pixels[ghost_y + 3][ghost_x - 1] = pixels[ghost_y + 3][ghost_x] = (60, 30, 70)

    # พื้นดิน + หมอก
    for y in range(horizon, height):
        for x in range(width):
            pixels[y][x] = lerp((26, 12, 30), (10, 4, 12), (y - horizon) / (height - horizon))
            if y == horizon and rng.random() < 0.5:
                pixels[y - 1][x] = blend(pixels[y - 1][x], (30, 60, 40), 0.8)
    for y in range(horizon - 3, height):
        for x in range(width):
            mist = 0.18 * (1 + math.sin(x * 0.35 + y * 0.9)) * (1 - abs(y - horizon) / 5)
            if mist > 0:
                pixels[y][x] = blend(pixels[y][x], (150, 140, 190), mist)
    return pixels


# ---------- ประตูมิติ (ชนะ) ----------

def portal_scene() -> list:
    width, height = 44, 24
    cx, cy = width / 2 - 0.5, height / 2 - 0.5
    rng = random.Random(3)
    pixels = canvas(width, height)
    for y in range(height):
        for x in range(width):
            dx, dy = x - cx, (y - cy) * 1.15
            distance = math.hypot(dx, dy)
            if distance < 10.5:
                swirl = (math.sin(math.atan2(dy, dx) * 3 + distance * 0.75) + 1) / 2
                color = lerp((90, 20, 160), (60, 220, 255), swirl * (1 - distance / 14))
                color = lerp((255, 255, 255), color, min(1, distance / 4.5))
                if distance > 9.3:
                    color = lerp(color, (230, 200, 255), 0.7)
                pixels[y][x] = color
            elif distance < 14:
                pixels[y][x] = blend(None, (130, 70, 220), 0.5 * (1 - (distance - 10.5) / 3.5) ** 1.5)
    for _ in range(26):
        x, y = rng.randrange(width), rng.randrange(height)
        if math.hypot(x - cx, (y - cy) * 1.15) > 10.5:
            pixels[y][x] = rng.choice([(255, 240, 160), (200, 240, 255), (240, 190, 255)])
    return pixels


# ---------- หลุมศพ (แพ้) ----------

def grave_scene() -> list:
    width, height = 44, 24
    ground = 19
    rng = random.Random(11)
    pixels = canvas(width, height)
    for y in range(ground):
        for x in range(width):
            pixels[y][x] = lerp((6, 6, 12), (34, 30, 44), y / ground)
    sprinkle_stars(pixels, rng, 14, ground - 6)

    # ป้ายหลุมศพ ขอบโค้ง แสงจากซ้าย และกากบาทสลัก
    cx, top, half = 22, 4, 7
    for y in range(top, ground):
        for x in range(cx - half, cx + half + 1):
            arch_y = top + half
            if y < arch_y and math.hypot(x - cx, y - arch_y) > half:
                continue
            shade = lerp((190, 190, 205), (85, 85, 105), (x - cx + half) / (2 * half))
            if rng.random() < 0.06:
                shade = blend(shade, (70, 90, 70), 0.5)
            pixels[y][x] = shade
    engraved = (45, 42, 58)
    for y in range(top + 3, top + 11):
        pixels[y][cx] = engraved
    for x in range(cx - 2, cx + 3):
        pixels[top + 5][x] = engraved

    # เทียนสองข้าง
    for candle in (8, 36):
        glow(pixels, candle, 13, 7, (255, 170, 70), 0.5)
        for y in range(15, ground):
            pixels[y][candle] = (235, 225, 200)
        pixels[14][candle] = (255, 220, 110)
        pixels[13][candle] = (255, 130, 40)

    # ดินและหญ้า
    for y in range(ground, height):
        for x in range(width):
            pixels[y][x] = lerp((52, 36, 30), (20, 14, 12), (y - ground) / (height - ground))
    for x in range(width):
        if rng.random() < 0.6:
            pixels[ground - 1][x] = lerp((40, 90, 50), (20, 50, 30), rng.random())
    return pixels


NIGHT_PIXELS = render(night_scene())
PORTAL_PIXELS = render(portal_scene())
GRAVE_PIXELS = render(grave_scene())
