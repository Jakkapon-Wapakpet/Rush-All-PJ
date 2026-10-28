#!/usr/bin/env python3
"""
Data Module - WITCH'S BREW
ข้อมูลคงที่ของร้าน: สมุนไพร สูตรยา อาการป่วย ส่วนผสมต้องห้าม และชื่อลูกค้า
Static data: herbs, recipes, symptoms, forbidden mixes, and customer names.
"""

from language import get_language

SHELF_SIZE = 10          # ชั้นวางยาจุได้กี่ขวด
CUSTOMERS_PER_DAY = 3    # ลูกค้าต่อวัน
EXPLOSION_COST = 15      # ค่าซ่อมหม้อเมื่อระเบิด

# สมุนไพร: ราคาพื้นฐาน (ราคาในตลาดจะขึ้นลงทุกวัน)
HERBS = {
    "mint": {"name": {"th": "สะระแหน่", "en": "Mint"}, "icon": "🌿", "price": 6},
    "ginger": {"name": {"th": "ขิง", "en": "Ginger"}, "icon": "🌱", "price": 6},
    "honey": {"name": {"th": "น้ำผึ้ง", "en": "Honey"}, "icon": "🍯", "price": 8},
    "nettle": {"name": {"th": "ใบตำแย", "en": "Nettle"}, "icon": "🍃", "price": 5},
    "glowshroom": {"name": {"th": "เห็ดเรืองแสง", "en": "Glowshroom"}, "icon": "🍄", "price": 15},
    "moonflower": {"name": {"th": "ดอกจันทร์", "en": "Moonflower"}, "icon": "🌼", "price": 14},
    "dragon_root": {"name": {"th": "รากมังกร", "en": "Dragon Root"}, "icon": "🌶", "price": 18},
    "phoenix": {"name": {"th": "ขนนกฟีนิกซ์", "en": "Phoenix Feather"}, "icon": "🪶", "price": 35},
}

# อาการป่วยของลูกค้า
SYMPTOMS = {
    "cough": {"th": "ไอ", "en": "Cough"},
    "fever": {"th": "ตัวร้อน", "en": "Fever"},
    "insomnia": {"th": "นอนไม่หลับ", "en": "Insomnia"},
    "ache": {"th": "ปวดเมื่อย", "en": "Aching"},
    "curse": {"th": "โดนสาป", "en": "Cursed"},
    "heartbreak": {"th": "อกหัก", "en": "Heartbroken"},
}

# สูตรยา
#   herbs  = สมุนไพรที่ต้องใช้ (อย่างละ 1)
#   cures  = อาการที่รักษาได้
#   price  = ราคาขายแนะนำ
#   secret = True ถ้าเป็นสูตรลับที่ต้องค้นพบเอง
RECIPES = {
    "cough_syrup": {"name": {"th": "ยาแก้ไอ", "en": "Cough Syrup"}, "herbs": ["mint", "honey"],
                    "cures": ["cough"], "price": 30, "secret": False},
    "fever_tea": {"name": {"th": "ชาลดไข้", "en": "Fever Tea"}, "herbs": ["ginger", "mint"],
                  "cures": ["fever"], "price": 30, "secret": False},
    "dream_drop": {"name": {"th": "ยาหลับฝันดี", "en": "Dream Drops"}, "herbs": ["moonflower", "honey"],
                   "cures": ["insomnia"], "price": 40, "secret": False},
    "cure_all": {"name": {"th": "ยาครอบจักรวาล", "en": "Cure-All Tonic"}, "herbs": ["ginger", "mint", "honey"],
                 "cures": ["cough", "fever"], "price": 55, "secret": True},
    "muscle_balm": {"name": {"th": "ยาแก้ปวดเมื่อย", "en": "Muscle Balm"}, "herbs": ["ginger", "nettle", "dragon_root"],
                    "cures": ["ache"], "price": 60, "secret": True},
    "hex_breaker": {"name": {"th": "ยาแก้คำสาป", "en": "Hex Breaker"}, "herbs": ["glowshroom", "moonflower"],
                    "cures": ["curse"], "price": 70, "secret": True},
    "mended_heart": {"name": {"th": "ยาสมานใจ", "en": "Mended Heart"}, "herbs": ["phoenix", "honey", "moonflower"],
                     "cures": ["heartbreak"], "price": 90, "secret": True},
}

# คู่สมุนไพรที่ห้ามผสมกัน (ผสมแล้วหม้อระเบิด!)
FORBIDDEN = [("dragon_root", "moonflower"), ("phoenix", "nettle")]

CUSTOMER_NAMES = ["ป้าศรี", "ลุงมี", "หนูนา", "ตาเหลือง", "พี่ต้อม", "ยายจันทร์", "อัศวินบอย", "น้องฝน",
                  "เชฟก้อง", "นักกวีพลอย", "ชาวนาทอง", "พ่อค้าเพชร"]


def tr(text: dict) -> str:
    """เลือกข้อความตามภาษาปัจจุบันจาก dict เช่น {'th': 'ขิง', 'en': 'Ginger'}"""
    return text.get(get_language(), text["th"])
