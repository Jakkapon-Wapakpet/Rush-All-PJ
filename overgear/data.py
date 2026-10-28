#!/usr/bin/env python3
"""
Data Module - OVERGEAR (ร้านตีอาวุธ)
ข้อมูลคงที่ของเกม: เกรด แม่พิมพ์อาวุธ วัตถุดิบ ลูกค้า ผู้กล้า สัตว์ประหลาด ข่าว และระดับความยาก
Static data: grades, weapon molds, materials, customers, heroes, monsters, news, and difficulty settings.
"""

from language import get_language

GOAL_DAY = 30            # มังกรบุกหมู่บ้านตอนจบวันที่ 30
MAX_FAME = 100
MAX_STOCK = 6            # ชั้นวางอาวุธในร้าน
BASE_STORAGE = 20        # คลังวัตถุดิบเริ่มต้น (ชิ้น)
STORAGE_UPGRADE = 10     # ขยายคลังครั้งละ
MAX_STORAGE = 40
MAX_ORDERS = 5           # รับออเดอร์ค้างไว้พร้อมกันได้สูงสุด
BOARD_SIZE = 4           # ลูกค้าบนกระดานต่อวัน
BASE_FORGES = 2          # ตีอาวุธ/ซ่อมได้ต่อวัน (ลูกมือ +1)
MAX_FORGE_LEVEL = 4
CRIT_CHANCE = 0.05       # ตีวิกฤต: เกรดขึ้นอีก 1 ขั้น (ไม่เกินเพดาน)
APPRENTICE_HIRE = 40
APPRENTICE_WAGE = 6
MAX_HEROES = 6
HERO_LEAVE_DAYS = 4      # ผู้กล้าไม่มีอาวุธเกินกี่วันจะไปซื้อร้านอื่น
MAX_LEVEL = 10
LATE_FAME = 3            # ส่งไม่ทันกำหนด เสียชื่อเสียง
CANCEL_FAME = 2          # ยกเลิกออเดอร์เอง เสียชื่อเสียง
DEATH_FAME = 5           # ผู้กล้าที่ใช้อาวุธเราตาย เสียชื่อเสียง
SELL_RATE = 0.5          # ขายวัตถุดิบคืนตลาดได้ครึ่งราคา
WALKIN_RATE = 0.6        # ขายอาวุธให้พ่อค้าเร่ได้ 60% ของมูลค่า

# ---------- เกรดอาวุธ 5 ระดับ ----------
# power = ตัวคูณค่าพลัง, price = ตัวคูณราคา, need = คะแนนคุณภาพขั้นต่ำ
GRADES = [
    {"key": "common", "name": {"th": "ธรรมดา", "en": "Common"}, "icon": "⚪", "power": 1.0, "price": 1, "need": 0},
    {"key": "rare", "name": {"th": "แรร์", "en": "Rare"}, "icon": "🔵", "power": 1.25, "price": 2, "need": 9},
    {"key": "epic", "name": {"th": "อีปิค", "en": "Epic"}, "icon": "🟣", "power": 1.6, "price": 4, "need": 15},
    {"key": "legendary", "name": {"th": "ตำนาน", "en": "Legendary"}, "icon": "🟠", "power": 2.2, "price": 10,
     "need": 21},
    {"key": "mythic", "name": {"th": "เทพนิยาย", "en": "Mythic"}, "icon": "🔴", "power": 3.0, "price": 30,
     "need": 27},
]
COMMON, RARE, EPIC, LEGENDARY, MYTHIC = range(5)

# ---------- แม่พิมพ์อาวุธ ----------
# blade = จำนวนโลหะที่ใช้ทำใบมีด, mold = ราคาซื้อแม่พิมพ์ (0 = มีตั้งแต่เริ่ม)
WEAPONS = {
    "dagger": {"name": {"th": "มีดสั้น", "en": "Dagger"}, "icon": "🔪", "sharp": 3, "sturdy": 1, "weight": 1,
               "value": 15, "blade": 1, "mold": 0},
    "sword": {"name": {"th": "ดาบ", "en": "Sword"}, "icon": "🗡", "sharp": 4, "sturdy": 3, "weight": 3,
              "value": 28, "blade": 2, "mold": 0},
    "axe": {"name": {"th": "ขวาน", "en": "Axe"}, "icon": "🪓", "sharp": 3, "sturdy": 4, "weight": 5,
            "value": 26, "blade": 2, "mold": 0},
    "spear": {"name": {"th": "หอก", "en": "Spear"}, "icon": "🔱", "sharp": 5, "sturdy": 2, "weight": 3,
              "value": 32, "blade": 1, "mold": 50},
    "hammer": {"name": {"th": "ค้อนศึก", "en": "Warhammer"}, "icon": "🔨", "sharp": 1, "sturdy": 7, "weight": 7,
               "value": 40, "blade": 3, "mold": 90},
}

# ---------- วัตถุดิบ ----------
# slot: blade (ใบมีด) / handle (ด้าม) / gem (เครื่องประดับ)
# points = คะแนนคุณภาพ, cap = เพดานเกรด (เฉพาะใบมีด), legend = ได้จากผู้กล้าที่รอดกลับมาเท่านั้น
# market = ขายในตลาดทุกวัน, ถ้า False จะมีเฉพาะวันที่คาราวานมา (ของตำนานไม่ขายในตลาดเลย)
MATERIALS = {
    "iron": {"slot": "blade", "name": {"th": "เหล็ก", "en": "Iron"}, "icon": "⬛", "points": 1, "cap": RARE,
             "price": 6, "sharp": 0, "sturdy": 1, "weight": 1, "market": True, "legend": False},
    "silver": {"slot": "blade", "name": {"th": "เงิน", "en": "Silver"}, "icon": "🥈", "points": 4, "cap": EPIC,
               "price": 14, "sharp": 2, "sturdy": 1, "weight": 0, "market": True, "legend": False},
    "mithril": {"slot": "blade", "name": {"th": "มิธริล", "en": "Mithril"}, "icon": "💠", "points": 7,
                "cap": LEGENDARY, "price": 38, "sharp": 3, "sturdy": 3, "weight": -1, "market": False,
                "legend": False},
    "star_iron": {"slot": "blade", "name": {"th": "เหล็กดาวตก", "en": "Star Iron"}, "icon": "☄", "points": 10,
                  "cap": MYTHIC, "price": 90, "sharp": 5, "sturdy": 5, "weight": -1, "market": False,
                  "legend": True},
    "oak": {"slot": "handle", "name": {"th": "ไม้โอ๊ก", "en": "Oak"}, "icon": "🪵", "points": 0, "cap": None,
            "price": 3, "sharp": 0, "sturdy": 0, "weight": 0, "market": True, "legend": False},
    "ironwood": {"slot": "handle", "name": {"th": "ไม้เหล็ก", "en": "Ironwood"}, "icon": "🌲", "points": 2,
                 "cap": None, "price": 11, "sharp": 0, "sturdy": 1, "weight": 0, "market": True, "legend": False},
    "ent_heart": {"slot": "handle", "name": {"th": "แก่นไม้เอนท์", "en": "Ent Heartwood"}, "icon": "🌳",
                  "points": 4, "cap": None, "price": 70, "sharp": 0, "sturdy": 3, "weight": -1, "market": False,
                  "legend": True},
    "ruby": {"slot": "gem", "name": {"th": "ทับทิม", "en": "Ruby"}, "icon": "💎", "points": 2, "cap": None,
             "price": 16, "sharp": 2, "sturdy": 0, "weight": 0, "market": True, "legend": False},
    "runestone": {"slot": "gem", "name": {"th": "หินรูน", "en": "Runestone"}, "icon": "🪨", "points": 2,
                  "cap": None, "price": 15, "sharp": 0, "sturdy": 2, "weight": 0, "market": True, "legend": False},
    "phoenix": {"slot": "gem", "name": {"th": "ขนนกฟีนิกซ์", "en": "Phoenix Feather"}, "icon": "🪶", "points": 4,
                "cap": None, "price": 80, "sharp": 3, "sturdy": 3, "weight": 0, "market": False,
                "legend": True},
}
SLOTS = {"blade": {"th": "ใบมีด", "en": "Blade"}, "handle": {"th": "ด้าม", "en": "Handle"},
         "gem": {"th": "เครื่องประดับ", "en": "Ornament"}}

# ---------- การลงทุน ----------
FORGE_UPGRADE = {2: 70, 3: 150, 4: 280}     # เลเวลเตา -> ราคาอัปเกรด

# ---------- มินิเกมเตาหลอม ----------
TARGET_PROGRESS = 6       # ต้องตีขึ้นรูปให้ครบ 6 จังหวะ
BASE_TURNS = 6            # จำนวนครั้งที่ทำได้ก่อนถ่านหมด (+ เลเวลเตา)
MAX_HEAT = 10
SWEET_HEAT = (6, 8)       # ตีตอนนี้ = สมบูรณ์แบบ
GOOD_HEAT = (4, 9)        # ตีตอนนี้ = ดี (นอกช่วง = แย่)
RATING_VALUE = {"perfect": 1.0, "good": 0.6, "bad": 0.2}
AUTO_ACCURACY = 4         # ให้ตีอัตโนมัติ (ไม่ตั้งใจ) ได้ความแม่นเท่านี้ (เต็ม 10)
APPRENTICE_ACCURACY = 7   # ให้ลูกมือตีแทนได้ความแม่นเท่านี้

# ---------- ลูกค้า ----------
# grade = เกรดขั้นต่ำปกติ, pay = ตัวคูณค่าจ้าง, fame = ชื่อเสียงที่ได้, weight = โอกาสโผล่บนกระดาน
CUSTOMERS = {
    "villager": {"name": {"th": "ชาวบ้าน", "en": "Villager"}, "icon": "👨‍🌾", "types": ["dagger", "axe"],
                 "grade": COMMON, "pay": 1.1, "fame": 1, "weight": 3},
    "guard": {"name": {"th": "ทหารรักษาเมือง", "en": "Town Guard"}, "icon": "💂", "types": ["sword", "spear", "axe"],
              "grade": RARE, "pay": 1.0, "fame": 2, "weight": 3},
    "merchant": {"name": {"th": "พ่อค้าเร่", "en": "Peddler"}, "icon": "🧳",
                 "types": ["dagger", "sword", "axe", "spear", "hammer"], "grade": COMMON, "pay": 0.9, "fame": 0,
                 "weight": 2},
    "noble": {"name": {"th": "ขุนนาง (VIP)", "en": "Noble (VIP)"}, "icon": "👑", "types": ["sword", "spear", "hammer"],
              "grade": EPIC, "pay": 1.3, "fame": 4, "weight": 2},
    "hero": {"name": {"th": "ผู้กล้า", "en": "Hero"}, "icon": "⚔", "types": [], "grade": COMMON, "pay": 1.15,
             "fame": 2, "weight": 0},
    "repair": {"name": {"th": "ซ่อมอาวุธ", "en": "Repair"}, "icon": "🔧", "types": [], "grade": COMMON, "pay": 0.35,
               "fame": 1, "weight": 0},
}
CUSTOMER_NAMES = {
    "villager": [{"th": "ทอม", "en": "Tom"}, {"th": "แมกกี้", "en": "Maggie"}, {"th": "โรซี่", "en": "Rosie"},
                 {"th": "ฟิน", "en": "Finn"}],
    "guard": [{"th": "จ่าบรูโน่", "en": "Sgt. Bruno"}, {"th": "หมวดเกรต้า", "en": "Lt. Greta"},
              {"th": "พลทหารออตโต้", "en": "Pvt. Otto"}],
    "merchant": [{"th": "ฮิวโก้", "en": "Hugo"}, {"th": "บาร์ท", "en": "Bart"}, {"th": "เอลซ่า", "en": "Elsa"}],
    "noble": [{"th": "ลอร์ดเวน", "en": "Lord Wen"}, {"th": "เลดี้ไอริส", "en": "Lady Iris"},
              {"th": "ท่านเคานต์โมโร", "en": "Count Moro"}],
}

# ---------- ผู้กล้า ----------
# likes = แบบอาวุธที่อยากได้, bold = ล่าสัตว์ประหลาดสูงกว่าเลเวลตัวเองกี่ขั้น
CLASSES = {
    "knight": {"name": {"th": "อัศวิน", "en": "Knight"}, "icon": "🛡", "likes": ["sword", "spear"], "bold": 0},
    "barbarian": {"name": {"th": "บาร์บาเรียน", "en": "Barbarian"}, "icon": "💢", "likes": ["axe", "hammer"],
                  "bold": 1},
    "ranger": {"name": {"th": "เรนเจอร์", "en": "Ranger"}, "icon": "🏹", "likes": ["dagger", "spear"], "bold": 0},
    "paladin": {"name": {"th": "พาลาดิน", "en": "Paladin"}, "icon": "⚜", "likes": ["hammer", "sword"], "bold": 0},
}
HERO_NAMES = [
    {"th": "อัลดริก", "en": "Aldric"}, {"th": "เบรนน่า", "en": "Brenna"}, {"th": "เซดริก", "en": "Cedric"},
    {"th": "แด็กนี", "en": "Dagny"}, {"th": "เอ็ดวิน", "en": "Edwin"}, {"th": "เฟรยา", "en": "Freya"},
    {"th": "แกร์ริก", "en": "Garrick"}, {"th": "ฮิลด์", "en": "Hilde"}, {"th": "ไอโว", "en": "Ivo"},
    {"th": "ลูแคน", "en": "Lucan"}, {"th": "มิร่า", "en": "Mira"}, {"th": "โรแลนด์", "en": "Roland"},
    {"th": "ซิกริด", "en": "Sigrid"}, {"th": "โทเบียส", "en": "Tobias"}, {"th": "เรน", "en": "Wren"},
    {"th": "ยอริก", "en": "Yorick"},
]
HERO_LEVEL_POWER = 3      # พลังของผู้กล้าต่อเลเวล (บวกพลังอาวุธ)

# ---------- สัตว์ประหลาด 5 ระดับ (ผู้กล้าเลือกล่าตามเลเวล) ----------
MONSTERS = [
    {"name": {"th": "ก็อบลิน", "en": "Goblins"}, "icon": "👺", "threat": 12, "level": 1, "loot": 0.0},
    {"name": {"th": "หมาป่าดำ", "en": "Dire Wolves"}, "icon": "🐺", "threat": 20, "level": 3, "loot": 0.35},
    {"name": {"th": "โทรลล์", "en": "Troll"}, "icon": "👹", "threat": 30, "level": 5, "loot": 0.45},
    {"name": {"th": "ไวเวิร์น", "en": "Wyvern"}, "icon": "🦇", "threat": 44, "level": 7, "loot": 0.5},
    {"name": {"th": "ลิช", "en": "Lich"}, "icon": "💀", "threat": 60, "level": 9, "loot": 0.6},
]
# ของที่ผู้กล้านำกลับมาขาย: ระดับสัตว์ 2-3 ได้ของกลาง, 4-5 อาจได้มิธริลหรือของตำนาน
MID_LOOT = ["silver", "ironwood", "ruby", "runestone"]
HIGH_LOOT = ["mithril", "mithril", "star_iron", "ent_heart", "phoenix"]

# ภารกิจตามหาวัตถุดิบตำนาน (ผู้เล่นจ่ายค่าจ้างส่งผู้กล้าที่ถืออาวุธของเราไป)
LEGEND_QUESTS = {
    "crater": {"name": {"th": "หลุมอุกกาบาตเพลิง", "en": "Burning Crater"}, "icon": "☄", "material": "star_iron",
               "threat": 34, "fee": 30},
    "elder_wood": {"name": {"th": "ป่าเอนท์โบราณ", "en": "Elder Wood"}, "icon": "🌳", "material": "ent_heart",
                   "threat": 28, "fee": 25},
    "ember_peak": {"name": {"th": "ยอดเขาฟีนิกซ์", "en": "Ember Peak"}, "icon": "🔥", "material": "phoenix",
                   "threat": 40, "fee": 35},
}
TASKS = {"hunt": {"th": "ออกล่า", "en": "Hunting"}, "rest": {"th": "พัก", "en": "Resting"}}

# ---------- ข่าวรายวัน (รู้ล่วงหน้า 1 วันเป็นข่าวลือ) ----------
# price = ตัวคูณราคาวัตถุดิบ, demand = แบบอาวุธที่คนต้องการ (ออเดอร์แบบนี้มากขึ้นและจ่ายแพงขึ้น)
# pay = ตัวคูณค่าจ้างออเดอร์, threat = ตัวคูณความแข็งของสัตว์ประหลาด, loot = ตัวคูณโอกาสได้ของ
NEWS = {
    "calm": {"name": {"th": "วันธรรมดา", "en": "Quiet day"}, "icon": "☀", "weight": 4,
             "about": {"th": "ไม่มีอะไรพิเศษ", "en": "Nothing special"}},
    "orc_raid": {"name": {"th": "ออร์คบุกทางเหนือ", "en": "Orcs raid the north"}, "icon": "⚔", "weight": 2,
                 "about": {"th": "คนแห่ซื้อขวาน เหล็กแพงขึ้น", "en": "Axes in demand, iron pricier"},
                 "price": {"iron": 1.4}, "demand": "axe", "pay": 1.25},
    "tourney": {"name": {"th": "เทศกาลประลองอัศวิน", "en": "Knights' tourney"}, "icon": "🏇", "weight": 2,
                "about": {"th": "คนแห่ซื้อดาบ จ่ายดี", "en": "Swords in demand, good pay"},
                "price": {"silver": 1.2}, "demand": "sword", "pay": 1.3},
    "mine_collapse": {"name": {"th": "เหมืองเงินถล่ม", "en": "Silver mine collapse"}, "icon": "⛏", "weight": 1,
                      "about": {"th": "ราคาเงินพุ่ง", "en": "Silver price soars"}, "price": {"silver": 1.8}},
    "caravan": {"name": {"th": "คาราวานคนแคระมาถึง", "en": "Dwarf caravan arrives"}, "icon": "🐫", "weight": 2,
                "about": {"th": "มีมิธริลขาย อัญมณีลดราคา", "en": "Mithril on sale, gems discounted"},
                "price": {"mithril": 0.85, "ruby": 0.7, "runestone": 0.7, "ironwood": 0.8}, "caravan": True},
    "rival_sale": {"name": {"th": "ร้านคู่แข่งตัดราคา", "en": "Rival smith undercuts"}, "icon": "🏪", "weight": 2,
                   "about": {"th": "ลูกค้าต่อราคา (ชื่อเสียง 40+ ไม่โดน)", "en": "Customers haggle (fame 40+ immune)"},
                   "pay": 0.8},
    "monster_surge": {"name": {"th": "สัตว์ประหลาดชุกชุม", "en": "Monster surge"}, "icon": "👹", "weight": 2,
                      "about": {"th": "ล่ายากขึ้น แต่ได้ของมากขึ้น", "en": "Hunts harder, but more loot"},
                      "threat": 1.25, "loot": 2.0},
    "timber": {"name": {"th": "ไม้ล้นตลาด", "en": "Timber glut"}, "icon": "🪵", "weight": 1,
               "about": {"th": "ไม้ราคาถูก", "en": "Wood is cheap"}, "price": {"oak": 0.5, "ironwood": 0.6}},
}
RIVAL_IMMUNE_FAME = 40

# ---------- ฉากจบ: มังกรบุก ----------
GARRISON_RATE = 0.4       # อาวุธในคลังทหาร นับพลัง ×0.4 (ทหารธรรมดาใช้อาวุธได้ไม่เต็มที่)
CHAMPION_RATE = 2.0       # พลังของแชมป์นับ ×2
HERO_RATE = 1.0           # ผู้กล้าคนอื่นที่ยังมีชีวิตและถืออาวุธเรา นับพลังเต็ม
MYTHIC_CHAMPION = 2.0     # แชมป์ถืออาวุธเทพนิยาย นับพลังเพิ่มอีก ×2
ENDINGS = [               # (สัดส่วนพลังป้องกัน/พลังมังกรขั้นต่ำ, ดาว, ชื่อ)
    (1.0, 3, {"th": "หมู่บ้านรอดปลอดภัย", "en": "The village stands"}),
    (0.65, 2, {"th": "รอด แต่บ้านเรือนเสียหาย", "en": "Survived, but scarred"}),
    (0.35, 1, {"th": "ยับเยิน ชาวบ้านหนีทัน", "en": "In ruins, but the people fled"}),
    (0.0, 0, {"th": "หมู่บ้านล่มสลาย", "en": "The village has fallen"}),
]

# ---------- ระดับความยาก ----------
# grade_need = บวกเกณฑ์คะแนนของทุกเกรด, picky = ลูกค้าจุกจิก (สเปกเข้มขึ้น), swing = ราคาผันผวน
# threat = ตัวคูณสัตว์ประหลาด, dragon = พลังมังกร, cool = ความร้อนลดต่อจังหวะ (ต่ำสุด, สูงสุด)
DIFFICULTIES = {
    "easy": {"name": {"th": "ง่าย", "en": "Easy"}, "icon": "😊",
             "about": {"th": "ทุนเยอะ ราคานิ่ง มังกรอ่อน (ไว้เดโม)", "en": "Rich start, stable prices, weak dragon"},
             "gold": 160, "fame": 15, "swing": 0.12, "grade_need": 0, "picky": 0, "threat": 0.85,
             "dragon": 160, "upkeep": 3, "vip_fame": 25, "cool": (1, 1)},
    "normal": {"name": {"th": "ปกติ", "en": "Normal"}, "icon": "😐",
               "about": {"th": "ต้องวางแผนเงินและผู้กล้าให้ดี", "en": "Plan your gold and heroes"},
               "gold": 110, "fame": 10, "swing": 0.25, "grade_need": 0, "picky": 0, "threat": 1.0,
               "dragon": 330, "upkeep": 4, "vip_fame": 30, "cool": (1, 2)},
    "nightmare": {"name": {"th": "นรกเหล็กกล้า", "en": "Steel Inferno"}, "icon": "💀",
                  "about": {"th": "ราคาผันผวน ลูกค้าจุกจิก มังกรแข็ง เกรดยาก",
                            "en": "Wild prices, picky buyers, tough dragon, harder grades"},
                  "gold": 80, "fame": 5, "swing": 0.4, "grade_need": 2, "picky": 1, "threat": 1.15,
                  "dragon": 380, "upkeep": 6, "vip_fame": 40, "cool": (1, 2)},
}


def tr(text: dict) -> str:
    """เลือกข้อความตามภาษาปัจจุบันจาก dict เช่น {'th': 'ดาบ', 'en': 'Sword'}"""
    return text.get(get_language(), text["th"])
