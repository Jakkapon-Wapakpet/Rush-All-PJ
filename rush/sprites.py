#!/usr/bin/env python3
"""
Sprites Module - LAST SHELTER (Bonus, GUI)
ภาพพิกเซลอาร์ตของผู้รอดชีวิต ซอมบี้ สิ่งก่อสร้าง และทรัพยากร วาดจากตารางตัวอักษรในโค้ด (ไม่ต้องใช้ไฟล์รูป)
Pixel-art sprites drawn from text grids, rendered with tkinter.PhotoImage.

วิธีอ่านตาราง: ตัวอักษร 1 ตัว = 1 พิกเซล, '.' = โปร่งใส, ตัวอื่นดูสีจาก PALETTE
"""

import tkinter as tk

PALETTE = {
    "K": "#141614",  # เส้นขอบ
    "W": "#f1efe6",  # ขาว
    "L": "#a9ada8",  # เทา (ผ้าคลุม)
    "G": "#9aa3a8",  # เหล็ก
    "g": "#5c6469",  # เหล็กเข้ม
    "S": "#e8b98f",  # ผิว
    "s": "#c28d63",  # ผิวเงา
    "E": "#141614",  # ตา
    "H": "#8a5a32",  # ไม้
    "h": "#4f3220",  # ไม้เข้ม / ผม
    "R": "#c9433a",  # แดง
    "r": "#7f2620",  # แดงเข้ม
    "B": "#4a78c8",  # น้ำเงิน
    "b": "#2b4a80",  # น้ำเงินเข้ม
    "Y": "#e8c04a",  # เหลือง / ทอง
    "N": "#6f8f3a",  # เขียวทหาร
    "n": "#43592a",  # เขียวทหารเข้ม
    "O": "#e88a3a",  # ส้ม
    "o": "#a9561e",  # ส้มเข้ม
    "Z": "#8fbf6a",  # ผิวซอมบี้
    "z": "#5b8a45",  # ผิวซอมบี้เข้ม
    "T": "#c8f55a",  # พิษ
    "M": "#7d6a55",  # ผ้าขาดๆ
    "m": "#4d4034",  # ผ้าเข้ม
    "P": "#7d5cc9",  # ม่วง
    "p": "#4d3589",  # ม่วงเข้ม
    "C": "#8fd3f0",  # ฟ้า / น้ำ
    "c": "#3f8fc0",  # ฟ้าเข้ม
}

SPRITES = {
    # ---------------- ผู้รอดชีวิต (ตามพลังพิเศษ) ----------------
    "scout": [
        "................",
        ".....KKKKKK.....",
        "....KNNNNNNK....",
        "...KNNNNNNNNK...",
        "...KNSSSSSSNK...",
        "...KNSESSESNK...",
        "...KNSSSSSSNK...",
        "....KKSssSKK....",
        "...KMKNNNNKMK...",
        "..KMMKNNNNKMMK..",
        "..KMMKNYYNKMMK..",
        "..KSKKNNNNKKSK..",
        "....KnnnnnnK....",
        "....KmmKKmmK....",
        "....KhK..KhK....",
        "....KK....KK....",
    ],
    "scientist": [
        "................",
        ".....KKKKKK.....",
        "....KhhhhhhK....",
        "...KhhhhhhhhK...",
        "...KhSSSSSShK...",
        "...KhKCKKCKhK...",
        "...KhSSSSSShK...",
        "....KKSssSKK....",
        "...KWWKRRKWWK...",
        "..KWWWWKKWWWWK..",
        "..KWWBWWWWWWWK..",
        "..KSKWWWWWWKSK..",
        "...KKWWWWWWKK...",
        "....KbbKKbbK....",
        "....KbK..KbK....",
        "....KK....KK....",
    ],
    "marksman": [
        "................",
        ".....KKKKKK.....",
        "....KnnnnnnK....",
        "...KnNNNNNNnK...",
        "..KnnnnnnnnnnK..",
        "...KSSSSSSSSK...",
        "...KSESSSSESK...",
        "...KSSSssSSSK...",
        "....KKSSSSKK....",
        "..KNNNNNNNNNNK..",
        ".KgggggggggggggK",
        "..KSNNNNNNNNSK..",
        "...KnnnnnnnnK...",
        "....KnnKKnnK....",
        "....KhK..KhK....",
        "....KK....KK....",
    ],
    "immune": [
        "................",
        ".....KKKKKK.....",
        "....KhhhhhhK....",
        "...KRRRRRRRRK...",
        "...KSSSSSSSSKR..",
        "...KSESSSSESKR..",
        "...KSSSSSSSSK...",
        "....KSSssSSK....",
        "...KKKSSSSKKK...",
        "..KSSKWWWWKSSK..",
        "..KSSKWWWWKSSK..",
        "..KSKKWWWWKKSK..",
        "....KbbbbbbK....",
        "....KbbKKbbK....",
        "....KhK..KhK....",
        "....KK....KK....",
    ],
    "mechanic": [
        "................",
        ".....KKKKKK.....",
        "....KOOOOOOK....",
        "...KOOOOOOOOKK..",
        "...KSSSSSSSSK...",
        "...KSESSSSESK...",
        "...KSSShhSSSK...",
        "....KKSSSSKK....",
        "...KOKKOOKKOK...",
        "..KOOOKOOKOOOK..",
        "..KSKOOOOOOKSKG.",
        "....KOOOOOOK.GG.",
        "....KooooooK.G..",
        "....KooKKooK....",
        "....KhK..KhK....",
        "....KK....KK....",
    ],
    "stranger": [
        "................",
        ".....KKKKKK.....",
        "....KLLLLLLK....",
        "...KLLLLLLLLK...",
        "...KLKKKKKKLK...",
        "...KLKWKKWKLK...",
        "...KLKKKKKKLK...",
        "....KLLKKLLK....",
        "...KLLLLLLLLK...",
        "..KLLLLLLLLLLK..",
        "..KLLLgLLgLLLK..",
        "..KgKLLLLLLKgK..",
        "...KLLLLLLLLK...",
        "....KggKKggK....",
        "....KhK..KhK....",
        "....KK....KK....",
    ],
    # ---------------- ซอมบี้ 5 เลเวล ----------------
    "walker": [
        "................",
        ".....KKKKKK.....",
        "....KzZZZZzK....",
        "...KZZZZZZZZK...",
        "...KZKRZZRKZK...",
        "...KZZZZZZZZK...",
        "...KZZKWKWKZK...",
        "....KKZZZZKK....",
        "KZZKMMMMMMMMKZZK",
        "KZZKMmMMMMmMKZZK",
        ".KKKMMMRMMMMKKK.",
        "....KMMMMMMK....",
        "....KmmmmmmK....",
        "....KbbKKbbK....",
        "....KZK..KbK....",
        "....KK....KK....",
    ],
    "runner": [
        "................",
        "......KKKKKK....",
        ".....KZZZZZZK...",
        "....KZZZZZZZZK..",
        "....KZKRZZRKZK..",
        "....KZZZZZZZZK..",
        "....KZKWWWWKZK..",
        ".....KKZZZZKK...",
        "...KKRRRRRRK....",
        "..KZKRrRRRRKKZK.",
        ".KZK.KRRRRRK.KK.",
        "....KbbbbbK.....",
        "...KbbK.KbbK....",
        "..KbbK...KbK....",
        "..KZK.....KZK...",
        "..KK.......KK...",
    ],
    "brute": [
        "................",
        "....KKKKKKKK....",
        "...KzZZZZZZzK...",
        "..KZZKRZZRKZZK..",
        "..KZZZZZZZZZZK..",
        "..KZKWKWKWKWZK..",
        "...KKZZZZZZKK...",
        ".KKZZZZZZZZZZKK.",
        "KZZKMMMMMMMMKZZK",
        "KZZKMMMMMMMMKZZK",
        "KZZKmMMMMMMmKZZK",
        "KZZKMMMMMMMMKZZK",
        ".KKKmmmmmmmmKKK.",
        "...KZZZKKZZZK...",
        "...KZZZK.KZZZK..",
        "...KKKKK.KKKKK..",
    ],
    "spitter": [
        "................",
        "......KKKK......",
        ".....KZZZZK.....",
        "....KZRZZRZK....",
        "....KZZZZZZK....",
        "....KZKTTKZK....",
        ".....KKTTKK.....",
        "...KKZZTZZZKK...",
        "..KZZZZZZZZZZK..",
        ".KZZTZZZZZZTZZK.",
        ".KZZZZZZZZZZZZK.",
        ".KZZZZTZZZZZZZK.",
        "..KZZZZZZZZZZK..",
        "...KKzzzzzzKK...",
        "....KzK..KzK..T.",
        "....KK....KK....",
    ],
    "king": [
        "....Y..YY..Y....",
        "....YYYYYYYY....",
        "....YRYYYYRY....",
        "...KZZZZZZZZK...",
        "...KZRRZZRRZK...",
        "...KZZZZZZZZK...",
        "...KZKWKKWKZK...",
        "..KPKKZZZZKKPK..",
        ".KPPPPKYYKPPPPK.",
        "KPPPPPPYYPPPPPPK",
        "KZPPPPPPPPPPPPZK",
        "KZKPPPPPPPPPPKZK",
        "..KppppppppppK..",
        "..KpppKKKKpppK..",
        "..KKKK....KKKK..",
        "................",
    ],
    # ---------------- สิ่งก่อสร้าง ----------------
    "barricade": [
        "................",
        "..K...K...K...K.",
        ".KGK.KGK.KGK.KGK",
        ".KGK.KGK.KGK.KGK",
        "KKKKKKKKKKKKKKKK",
        "KYYKKYYKKYYKKYYK",
        "KKYYKKYYKKYYKKYK",
        "KYYKKYYKKYYKKYYK",
        "KKKKKKKKKKKKKKKK",
        "KHHHHHHHHHHHHHHK",
        "KhhhhhhhhhhhhhhK",
        "KKKKKKKKKKKKKKKK",
        ".KGK.KGK.KGK.KGK",
        ".KGK.KGK.KGK.KGK",
        ".KgK.KgK.KgK.KgK",
        "nnnnnnnnnnnnnnnn",
    ],
    "garden": [
        "................",
        "................",
        "...N.....N....N.",
        "..NNN...NNN..NNN",
        ".NNnNN.NNnNN.NnN",
        "..NnN...NnN...n.",
        "...n.....n....n.",
        "...n..R..n..R.n.",
        "KKKKKKKKKKKKKKKK",
        "KHHHHHHHHHHHHHHK",
        "KHhHHHHhHHHHHhHK",
        "KHHHHHHHHHHHHHHK",
        "KhhhhhhhhhhhhhhK",
        "KKKKKKKKKKKKKKKK",
        "................",
        "................",
    ],
    "collector": [
        "................",
        "..KKKKKKKKKKKK..",
        "..KCCCCCCCCCCK..",
        "...KCCCCCCCCK...",
        "....KKKCCKKK....",
        "......KCCK......",
        "....KKKKKKKK....",
        "...KbBBBBBBbK...",
        "...KBBCBBBBBK...",
        "...KKKKKKKKKK...",
        "...KbBBBBBBbK...",
        "...KBBBBBBBBK...",
        "...KbBBBBBBbK...",
        "...KKKKKKKKKK...",
        "...KbBBBBBBbK...",
        "...KKKKKKKKKK...",
    ],
    "clinic": [
        "................",
        ".......KK.......",
        "......KWWK......",
        ".....KWWWWK.....",
        "....KWWWWWWK....",
        "...KWWWWWWWWK...",
        "..KWWWWWWWWWWK..",
        ".KKKKKKKKKKKKKK.",
        "..KWWWWRRWWWWK..",
        "..KWWWWRRWWWWK..",
        "..KWWRRRRRRWWK..",
        "..KWWRRRRRRWWK..",
        "..KWWWWRRWWWWK..",
        "..KWWWWRRWWWWK..",
        "..KLLLLLLLLLLK..",
        "..KKKKKKKKKKKK..",
    ],
    # ---------------- ทรัพยากร (10x10) ----------------
    "food": [
        "..KKKKKK..",
        ".KGGGGGGK.",
        ".KKKKKKKK.",
        ".KRRRRRRK.",
        ".KRWWWWRK.",
        ".KRWYYWRK.",
        ".KRWWWWRK.",
        ".KRRRRRRK.",
        ".KGGGGGGK.",
        "..KKKKKK..",
    ],
    "water": [
        "....KK....",
        "...KCCK...",
        "...KCCK...",
        "..KCCCCK..",
        ".KCWCCCCK.",
        ".KCWCCCCK.",
        ".KCCCCCcK.",
        ".KcCCCCcK.",
        "..KccccK..",
        "...KKKK...",
    ],
    "scrap": [
        "...KKKK...",
        "..KGGGGK..",
        ".KGGKKGGK.",
        "KGGK..KGGK",
        "KGK....KGK",
        "KGK....KGK",
        "KGGK..KGGK",
        ".KGGKKGGK.",
        "..KggggK..",
        "...KKKK...",
    ],
    "medicine": [
        "..........",
        "...KKKK...",
        "..KRRRRK..",
        ".KRWRRRRK.",
        ".KRRRRRRK.",
        ".KKKKKKKK.",
        ".KWWWWWWK.",
        ".KWWWWWLK.",
        "..KWWWWK..",
        "...KKKK...",
    ],
}

# ภาพของซอมบี้แต่ละเลเวล (index 0 = Lv.1)
ZOMBIE_SPRITES = ["walker", "runner", "brute", "spitter", "king"]

SHADOW = "#262b28"  # สีเงาดำ สำหรับซอมบี้ที่ยังไม่โผล่

# ภาพที่สร้างแล้ว (ต้องเก็บไว้ ไม่งั้น Tk จะลบภาพทิ้ง)
_cache = {}


def sprite(name: str, scale: int = 4, shadow: bool = False) -> tk.PhotoImage:
    """สร้างภาพจากตารางใน SPRITES ขยาย scale เท่า (shadow = วาดเป็นเงาดำทั้งตัว)"""
    key = (name, scale, shadow)
    if key in _cache:
        return _cache[key]

    rows = SPRITES[name]
    image = tk.PhotoImage(width=len(rows[0]), height=len(rows))
    for y, row in enumerate(rows):
        colors = [SHADOW if shadow else PALETTE.get(char, "#000000") for char in row]
        image.put("{" + " ".join(colors) + "}", to=(0, y))
    # ตั้งพิกเซล '.' ให้โปร่งใส
    for y, row in enumerate(rows):
        for x, char in enumerate(row):
            if char == ".":
                image.transparency_set(x, y, True)

    image = image.zoom(scale)
    _cache[key] = image
    return image
