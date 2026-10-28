#!/usr/bin/env python3
"""
Sprites Module - DUNGEON RUSH (Bonus, GUI)
ภาพพิกเซลอาร์ตของฮีโร่ มอนสเตอร์ และไอเทม วาดจากตารางตัวอักษรในโค้ด (ไม่ต้องใช้ไฟล์รูป)
Pixel-art sprites drawn from text grids, rendered with tkinter.PhotoImage.

วิธีอ่านตาราง: ตัวอักษร 1 ตัว = 1 พิกเซล, '.' = โปร่งใส, ตัวอื่นดูสีจาก PALETTE
"""

import tkinter as tk

PALETTE = {
    "K": "#1a1820",  # เส้นขอบ
    "W": "#f4f1ea",  # ขาว
    "L": "#c9c4d6",  # เทาอ่อน
    "G": "#b4bcc8",  # เหล็ก
    "g": "#77808f",  # เหล็กเข้ม
    "S": "#f2c49b",  # ผิว
    "s": "#d39a70",  # ผิวเงา
    "E": "#1a1820",  # ตา
    "H": "#7a4a2a",  # ผม/ไม้
    "h": "#4f2e1a",  # ไม้เข้ม
    "R": "#d0453a",  # แดง
    "r": "#8f2a22",  # แดงเข้ม
    "B": "#4a7fd6",  # น้ำเงิน
    "b": "#2c4f8f",  # น้ำเงินเข้ม
    "P": "#7a5ad6",  # ม่วง
    "p": "#4d3591",  # ม่วงเข้ม
    "Y": "#f0c04a",  # ทอง
    "y": "#b0802a",  # ทองเข้ม
    "N": "#5cbf60",  # เขียว
    "n": "#2f7a45",  # เขียวเข้ม
    "O": "#f08a3c",  # ส้ม
    "o": "#b5521f",  # ส้มเข้ม
    "C": "#9fe0ff",  # ฟ้าน้ำแข็ง
    "c": "#4fa8d8",  # ฟ้าเข้ม
    "V": "#d8d0f0",  # ม่วงผี
    "v": "#9a8fc4",  # ม่วงผีเข้ม
    "D": "#5e4596",  # มังกร
    "d": "#3a2a63",  # มังกรเข้ม
}

SPRITES = {
    # ---------------- ฮีโร่ ----------------
    "warrior": [
        ".......RR.......",
        ".....KKRRKK.....",
        "....KGGGGGGK....",
        "...KGGGGGGGGK...",
        "...KgSSSSSSgK...",
        "...KgSESSESgK...",
        "...KgSSSSSSgK...",
        "....KKSssSKK.W..",
        "....KRRKKRRK.W..",
        "...KRGGGGGGRKWK.",
        "...KRGGYYGGRKYK.",
        "...KSKGGGGKSKyK.",
        "....KKggggKK.y..",
        ".....KgKKgK.....",
        ".....KbK.KbK....",
        ".....KK..KK.....",
    ],
    "mage": [
        "......KK....KK..",
        ".....KPPK..KCCK.",
        "....KPPPPK.KCCK.",
        "...KPPYPPPK.KK..",
        "..KKKKKKKKKK.h..",
        "...KSSSSSSK..h..",
        "...KSESSESK..h..",
        "...KSSSSSSK..h..",
        "....KWWWWK...h..",
        "...KPWWWWPK..h..",
        "..KPPPWWPPPK.h..",
        "..KSPPPPPPPSKh..",
        "...KPPYYPPPKKh..",
        "...KPPPPPPPK.h..",
        "...KpppppppK.h..",
        "....KKKKKKK..h..",
    ],
    "archer": [
        "................",
        ".....KKKKK...H..",
        "....KNNNNNK..WH.",
        "...KNNNNNNNK.W.H",
        "...KNSSSSSNK.W.H",
        "...KNSESSESK.W.H",
        "...KNSSSSSSK.W.H",
        "....KKSssSKK.W.H",
        "....KnNKKNnK.W.H",
        "...KnNNNNNNnKW.H",
        "...KSKNHHNKSKWH.",
        "....KKNNNNKK.H..",
        ".....KnnnnK.....",
        ".....KnKKnK.....",
        ".....KhK.KhK....",
        ".....KK..KK.....",
    ],
    "cleric": [
        "................",
        ".....KKKKKK.....",
        "....KWWWWWWK....",
        "...KWWWYWWWWK...",
        "...KWSSSSSSWK...",
        "...KWSESSESWK...",
        "...KWSSSSSSWK...",
        "....KKSssSKK....",
        "...KKWWYYWWKK...",
        "..KWWWWYYWWWWK..",
        "..KSWYYYYYYWSK..",
        "...KWWWYYWWWK...",
        "...KWWWYYWWWK...",
        "...KLLLLLLLLK...",
        "....KYKKKKYK....",
        "....KK....KK....",
    ],
    # ---------------- มอนสเตอร์ ----------------
    "slime": [
        "................",
        "................",
        "................",
        "................",
        "......KKKK......",
        "....KKNNNNKK....",
        "...KNNWWNNNNK...",
        "..KNNWWNNNNNNK..",
        "..KNNNNNNNNNNK..",
        ".KNNNKENNNKENNK.",
        ".KNNNKENNNKENNK.",
        ".KNNNNNNNNNNNNK.",
        ".KNNNNNKKNNNNNK.",
        ".KnNNNNNNNNNNnK.",
        "..KnnnnnnnnnnK..",
        "...KKKKKKKKKK...",
    ],
    "goblin": [
        "................",
        "......KKKK......",
        "KK...KNNNNK...KK",
        "KNK.KNNNNNNK.KNK",
        ".KNKNNNNNNNNKNK.",
        "..KNNKKNNKKNNK..",
        "..KNNKYNNKYNNK..",
        "...KNNNNNNNNK...",
        "...KNNKWKWKNK...",
        "....KKKKKKKK.Hh.",
        "...KHHHHHHHHKHh.",
        "..KNKHHHHHHKNKh.",
        "..KNKHhhhhHKNK..",
        "...KKHHHHHHKK...",
        "....KnK..KnK....",
        "....KK....KK....",
    ],
    "phantom": [
        "................",
        ".....KKKKKK.....",
        "...KKVVVVVVKK...",
        "..KVVWWVVVVVVK..",
        "..KVWWVVVVVVVK..",
        ".KVVVKKVVVKKVVK.",
        ".KVVVKKVVVKKVVK.",
        ".KVVVVVVVVVVVVK.",
        ".KVVVVVKKKVVVVK.",
        ".KVVVVKKKKKVVVK.",
        ".KVVVVVKKKVVVVK.",
        ".KVVVVVVVVVVVVK.",
        ".KvVVVVVVVVVVvK.",
        ".KvvVVvvVVvvVvK.",
        ".KKvvKKvvKKvvKK.",
        "..K..K..K..KK...",
    ],
    "golem": [
        "......O..O......",
        ".....OYOOYO.....",
        "....KOYYYYOK....",
        "...KKoooooKK....",
        "..KoohhhhhhooK..",
        "..KohYYhhYYhoK..",
        "..KohhhhhhhhoK..",
        ".KKKohhOOhhoKKK.",
        "KohhKKhhhhKKhhoK",
        "KhhhhKhOOhKhhhhK",
        "KhhhhKhhhhKhhhhK",
        ".KKKKhhOOhhKKKK.",
        "....KhhhhhhK....",
        "...KhhhKKhhhK...",
        "...KhhK..KhhK...",
        "...KKKK..KKKK...",
    ],
    "dragon": [
        "..K..........K..",
        ".KdK...KK...KdK.",
        "KDdDK.KDDK.KDdDK",
        "KDDDDKDDDDKDDDDK",
        ".KDDDDDDDDDDDDK.",
        "..KDDRDDDDRDDK..",
        "..KDDDDDDDDDDK..",
        "...KDDDDDDDDK...",
        "...KDDWDDWDDK...",
        "..KDDDKKKKDDDK..",
        ".KDdKDDOODDKdDK.",
        "KDdK.KDOODK.KdDK",
        "KdK..KDDDDK..KdK",
        ".K...KDddDK...K.",
        ".....KDK.KDK....",
        ".....KK...KK....",
    ],
    # ---------------- ไอเทม (12x12) ----------------
    # 'X' = สีหลักของไอเทม เปลี่ยนตามธาตุ (ดู ELEMENT_TINT)
    "weapon": [
        "..........KK",
        ".........KXK",
        "........KXK.",
        ".......KXK..",
        "......KXK...",
        ".....KXK....",
        "..K.KXK.....",
        "..KYKK......",
        "...KYK......",
        "..KhKYK.....",
        ".KhK.KK.....",
        ".KK.........",
    ],
    "bow": [
        "....KKK.....",
        "...KHHK.....",
        "..KHK.W.....",
        "..KHK..W....",
        ".KHK....W...",
        ".KXK.....W..",
        ".KXK.....W..",
        ".KHK....W...",
        "..KHK..W....",
        "..KHK.W.....",
        "...KHHK.....",
        "....KKK.....",
    ],
    "staff": [
        ".......KKK..",
        "......KXXXK.",
        "......KXWXK.",
        "......KXXXK.",
        ".......KhK..",
        "......KhK...",
        ".....KhK....",
        "....KhK.....",
        "...KhK......",
        "..KhK.......",
        ".KhK........",
        ".KK.........",
    ],
    "armor": [
        "..KK....KK..",
        ".KXXK..KXXK.",
        ".KXXXKKXXXK.",
        "KXXXXXXXXXXK",
        "KXXWXXXXXXXK",
        ".KKXXXXXXKK.",
        "..KXXXXXXK..",
        "..KXXYYXXK..",
        "..KXXXXXXK..",
        "..KXXXXXXK..",
        "...KXXXXK...",
        "....KKKK....",
    ],
    "potion": [
        "....KKKK....",
        "....KhhK....",
        ".....KK.....",
        "....KWWK....",
        "....KWWK....",
        "...KRRRRK...",
        "..KRWRRRRK..",
        ".KRWRRRRRRK.",
        ".KRRRRRRRRK.",
        ".KRRRRRRRRK.",
        "..KrrrrrrK..",
        "...KKKKKK...",
    ],
}

# ชื่อภาพของมอนสเตอร์แต่ละชั้น (ตามลำดับใน data.MONSTERS)
MONSTER_SPRITES = ["slime", "goblin", "phantom", "golem", "dragon"]

# สีหลักของอาวุธตามธาตุ / สีของเกราะ
ELEMENT_TINT = {"physical": "#cfd6e0", "fire": "#f08a3c", "ice": "#9fe0ff", "holy": "#f6dc6a"}
ARMOR_TINT = {"leather_armor": "#a8703e", "mage_robe": "#7a5ad6", "chainmail": "#b4bcc8", "dragon_plate": "#5a3f8f"}

# ภาพที่สร้างแล้ว (ต้องเก็บไว้ ไม่งั้น Tk จะลบภาพทิ้ง)
_cache = {}


def sprite(name: str, scale: int = 4, tint: str = None) -> tk.PhotoImage:
    """
    สร้างภาพจากตารางใน SPRITES ขยาย scale เท่า
    tint = สีที่ใช้แทนตัวอักษร 'X' (สีหลักของไอเทม)
    """
    key = (name, scale, tint)
    if key in _cache:
        return _cache[key]

    rows = SPRITES[name]
    height, width = len(rows), len(rows[0])
    image = tk.PhotoImage(width=width, height=height)
    for y, row in enumerate(rows):
        colors = []
        for char in row:
            if char == "X":
                colors.append(tint or "#cfd6e0")
            else:
                colors.append(PALETTE.get(char, "#000000"))
        image.put("{" + " ".join(colors) + "}", to=(0, y))
    # ตั้งพิกเซล '.' ให้โปร่งใส
    for y, row in enumerate(rows):
        for x, char in enumerate(row):
            if char == ".":
                image.transparency_set(x, y, True)

    image = image.zoom(scale)
    _cache[key] = image
    return image


def item_sprite(key: str, item: dict, scale: int = 3) -> tk.PhotoImage:
    """ภาพของไอเทมจากข้อมูลใน data.ITEMS"""
    if item["type"] == "potion":
        return sprite("potion", scale)
    if item["type"] == "armor":
        return sprite("armor", scale, ARMOR_TINT.get(key))
    shape = "staff"
    if "warrior" in item["classes"]:
        shape = "weapon"
    elif "archer" in item["classes"]:
        shape = "bow"
    return sprite(shape, scale, ELEMENT_TINT[item["element"]])
