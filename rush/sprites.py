#!/usr/bin/env python3
"""
Sprites Module - GHOST REALM (หลุดมิติผี) (Bonus, GUI)
โหลดภาพเงาหนังตะลุง (PNG โปร่งใส) จากโฟลเดอร์ assets/ ด้วย tkinter.PhotoImage
Loads the shadow-puppet silhouette PNGs from assets/.

ภาพทั้งหมดสร้างจาก assets/make_art.py ชื่อไฟล์ <ชื่อภาพ>_<ขนาด px>.png และเงาจาง <ชื่อภาพ>_<ขนาด px>_9c6a3e.png
ภาพมีสีเงาเข้ม จึงต้องวางบนพื้นสีจอผ้า (COLORS["screen"]) เหมือนการเล่นหนังตะลุง
"""

import os
import tkinter as tk

ART_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

# ขนาดพื้นฐาน (หน่วย) ของแต่ละภาพ: ทรัพยากรเป็นไอคอนเล็ก 10 หน่วย นอกนั้น 16 หน่วย, ขนาดจริง = หน่วย x scale
SMALL = {"food", "water", "scrap", "medicine"}

# ภาพของผีแต่ละเลเวล (index 0 = Lv.1)
ZOMBIE_SPRITES = ["spirit", "krasue", "preta", "pop", "saming"]

SHADOW = "#9c6a3e"  # สีเงาจาง สำหรับผีที่ยังไม่โผล่ (ต้องตรงกับ assets/make_art.py)

# ภาพที่โหลดแล้ว (ต้องเก็บไว้ ไม่งั้น Tk จะลบภาพทิ้ง)
_cache = {}


def sprite(name: str, scale: int = 4, shadow: bool = False) -> tk.PhotoImage:
    """โหลดภาพขนาด (หน่วย x scale) px (shadow = ใช้ภาพเงาจาง)"""
    key = (name, scale, shadow)
    if key not in _cache:
        size = (10 if name in SMALL else 16) * scale
        path = os.path.join(ART_DIR, f"{name}_{size}" + (f"_{SHADOW[1:]}" if shadow else "") + ".png")
        _cache[key] = tk.PhotoImage(file=path)
    return _cache[key]
