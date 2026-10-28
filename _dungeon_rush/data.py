#!/usr/bin/env python3
"""
Data Module - DUNGEON RUSH
ข้อมูลคงที่ของเกม: อาชีพฮีโร่ ไอเทมในร้านค้า และมอนสเตอร์แต่ละชั้น
Static game data: hero classes, shop items, and dungeon monsters.
"""

from language import get_language

# จำนวนฮีโร่สูงสุดในทีม และจำนวนช่องในกระเป๋า
MAX_PARTY = 3
BAG_SIZE = 10

# ธาตุของการโจมตี
ELEMENTS = {
    "physical": {"th": "กายภาพ", "en": "Physical"},
    "fire": {"th": "ไฟ", "en": "Fire"},
    "ice": {"th": "น้ำแข็ง", "en": "Ice"},
    "holy": {"th": "ศักดิ์สิทธิ์", "en": "Holy"},
}

# อาชีพฮีโร่: ราคาจ้าง ค่าสถานะเริ่มต้น และค่าที่เพิ่มขึ้นเมื่อเลเวลอัป
HERO_CLASSES = {
    "warrior": {
        "name": {"th": "นักรบ", "en": "Warrior"},
        "cost": 50, "hp": 45, "atk": 8, "def": 5,
        "growth": {"hp": 8, "atk": 2, "def": 2},
        "about": {"th": "HP และพลังป้องกันสูง", "en": "High HP and defense"},
    },
    "mage": {
        "name": {"th": "นักเวท", "en": "Mage"},
        "cost": 60, "hp": 26, "atk": 11, "def": 2,
        "growth": {"hp": 4, "atk": 3, "def": 1},
        "about": {"th": "โจมตีแรงแต่ตัวบาง", "en": "Strong attack, fragile"},
    },
    "archer": {
        "name": {"th": "นักธนู", "en": "Archer"},
        "cost": 55, "hp": 32, "atk": 9, "def": 3,
        "growth": {"hp": 5, "atk": 3, "def": 1},
        "about": {"th": "สมดุลทุกด้าน", "en": "Well balanced"},
    },
    "cleric": {
        "name": {"th": "นักบวช", "en": "Cleric"},
        "cost": 55, "hp": 34, "atk": 5, "def": 4,
        "growth": {"hp": 6, "atk": 1, "def": 2},
        "about": {"th": "รักษาเพื่อนที่ HP ต่ำสุดทุกเทิร์น", "en": "Heals the weakest ally every turn"},
    },
}

# ไอเทมในร้านค้า
#   type    = weapon (เพิ่ม atk) / armor (เพิ่ม def) / potion (ฟื้น HP อัตโนมัติในการต่อสู้)
#   level   = เลเวลขั้นต่ำที่ใส่ได้
#   classes = อาชีพที่ใช้ได้
ITEMS = {
    "wooden_sword": {"name": {"th": "ดาบไม้", "en": "Wooden Sword"}, "type": "weapon",
                     "price": 30, "atk": 3, "element": "physical", "level": 1, "classes": ["warrior"]},
    "iron_sword": {"name": {"th": "ดาบเหล็ก", "en": "Iron Sword"}, "type": "weapon",
                   "price": 70, "atk": 6, "element": "physical", "level": 1, "classes": ["warrior"]},
    "flame_sword": {"name": {"th": "ดาบเพลิง", "en": "Flame Sword"}, "type": "weapon",
                    "price": 180, "atk": 9, "element": "fire", "level": 3, "classes": ["warrior"]},
    "short_bow": {"name": {"th": "ธนูสั้น", "en": "Short Bow"}, "type": "weapon",
                  "price": 50, "atk": 5, "element": "physical", "level": 1, "classes": ["archer"]},
    "frost_bow": {"name": {"th": "ธนูน้ำแข็ง", "en": "Frost Bow"}, "type": "weapon",
                  "price": 150, "atk": 8, "element": "ice", "level": 2, "classes": ["archer"]},
    "oak_staff": {"name": {"th": "คทาไม้โอ๊ค", "en": "Oak Staff"}, "type": "weapon",
                  "price": 40, "atk": 4, "element": "physical", "level": 1, "classes": ["mage", "cleric"]},
    "fire_staff": {"name": {"th": "คทาเพลิง", "en": "Fire Staff"}, "type": "weapon",
                   "price": 120, "atk": 7, "element": "fire", "level": 2, "classes": ["mage"]},
    "ice_staff": {"name": {"th": "คทาน้ำแข็ง", "en": "Ice Staff"}, "type": "weapon",
                  "price": 160, "atk": 9, "element": "ice", "level": 3, "classes": ["mage"]},
    "holy_mace": {"name": {"th": "คทาศักดิ์สิทธิ์", "en": "Holy Mace"}, "type": "weapon",
                  "price": 110, "atk": 6, "element": "holy", "level": 1, "classes": ["cleric", "mage"]},
    "leather_armor": {"name": {"th": "ชุดหนัง", "en": "Leather Armor"}, "type": "armor",
                      "price": 35, "def": 2, "level": 1, "classes": ["warrior", "mage", "archer", "cleric"]},
    "mage_robe": {"name": {"th": "เสื้อคลุมเวท", "en": "Mage Robe"}, "type": "armor",
                  "price": 60, "def": 3, "level": 1, "classes": ["mage", "cleric"]},
    "chainmail": {"name": {"th": "เกราะโซ่", "en": "Chainmail"}, "type": "armor",
                  "price": 100, "def": 5, "level": 2, "classes": ["warrior", "archer", "cleric"]},
    "dragon_plate": {"name": {"th": "เกราะเกล็ดมังกร", "en": "Dragon Plate"}, "type": "armor",
                     "price": 240, "def": 9, "level": 4, "classes": ["warrior"]},
    "potion": {"name": {"th": "ยาฟื้นพลัง", "en": "Potion"}, "type": "potion",
               "price": 15, "heal": 20, "level": 1, "classes": ["warrior", "mage", "archer", "cleric"]},
}

# มอนสเตอร์ประจำแต่ละชั้น (ชั้น 1-5)
#   weak    = ธาตุที่แพ้ทาง (ดาเมจ x2)
#   immune  = ธาตุที่ไม่ได้รับความเสียหาย (ดาเมจ 0)
#   attacks = จำนวนครั้งที่โจมตีต่อเทิร์น
MONSTERS = [
    {"name": {"th": "สไลม์", "en": "Slime"}, "icon": "🟢",
     "hp": 45, "atk": 9, "def": 1, "weak": "fire", "immune": None, "attacks": 1, "gold": 60, "xp": 30},
    {"name": {"th": "แก๊งก็อบลิน", "en": "Goblin Gang"}, "icon": "👺",
     "hp": 70, "atk": 12, "def": 3, "weak": None, "immune": None, "attacks": 1, "gold": 90, "xp": 45},
    {"name": {"th": "วิญญาณหลอน", "en": "Phantom"}, "icon": "👻",
     "hp": 120, "atk": 17, "def": 3, "weak": "holy", "immune": "physical", "attacks": 1, "gold": 130, "xp": 60},
    {"name": {"th": "โกเลมเพลิง", "en": "Fire Golem"}, "icon": "🔥",
     "hp": 230, "atk": 23, "def": 7, "weak": "ice", "immune": "fire", "attacks": 2, "gold": 180, "xp": 80},
    {"name": {"th": "มังกรดำ", "en": "Black Dragon"}, "icon": "🐉",
     "hp": 400, "atk": 25, "def": 8, "weak": "ice", "immune": "fire", "attacks": 2, "gold": 500, "xp": 100},
]


def tr(text: dict) -> str:
    """เลือกข้อความตามภาษาปัจจุบันจาก dict เช่น {'th': 'นักรบ', 'en': 'Warrior'}"""
    return text.get(get_language(), text["th"])
