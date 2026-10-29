#!/usr/bin/env python3
"""
Data Module - GHOST REALM (มิติผี)
ข้อมูลคงที่ของเกม: ทรัพยากร งาน สิ่งก่อสร้าง ผู้รอดชีวิตเริ่มต้น และค่าความยาก
Static data: resources, jobs, buildings, starting survivors, and difficulty settings.
"""

from language import get_language

GOAL_DAY = 15            # Base timeline; actual campaign length comes from difficulty.
MAX_PEOPLE = 6             # ศาลารับคนได้สูงสุด
MAX_HP = 100
MIN_SCAVENGE_HP = 40     # HP ต่ำกว่านี้ออกไปหาของ/เฝ้ายามไม่ได้
STARVE_DAMAGE = 20       # ไม่มีอาหาร/น้ำ เสีย HP ต่อวัน (อย่างละ)
REST_HEAL = 15           # พักผ่อนฟื้น HP
RAID_START_DAY = 3       # ผีเริ่มบุกตั้งแต่วันนี้
STRANGER_CHANCE = 0.35   # โอกาสที่จะมีคนมาขอเข้าศาลาในแต่ละเช้า
STRANGER_POSSESSED = 0.3  # โอกาสที่คนแปลกหน้าถูกผีสิงมาแล้ว
TURN_DAYS = 2            # ถูกผีสิงแล้วต้องได้น้ำมนต์ภายในกี่วัน ไม่งั้นกลายเป็นผี

# ผี 5 เลเวล: power = พลังโจมตีต่อตัว, from_day = เริ่มโผล่วันที่
GHOSTS = [
    {"level": 1, "name": {"th": "วิญญาณเร่ร่อน", "en": "Wandering Spirit"}, "icon": "👻", "power": 1, "from_day": 3,
     "about": {"th": "อ่อนแอ แต่มาเป็นฝูง", "en": "Weak, but comes in numbers"}},
    {"level": 2, "name": {"th": "กระสือ", "en": "Krasue"}, "icon": "🔥", "power": 2, "from_day": 5,
     "about": {"th": "ลอยข้ามได้ สายสิญจน์กันได้แค่ครึ่งเดียว", "en": "Floats over: the sacred thread only stops half"}},
    {"level": 3, "name": {"th": "เปรต", "en": "Preta"}, "icon": "🦴", "power": 4, "from_day": 7,
     "about": {"th": "กินของเซ่นไหว้ ธูปเทียนหายตัวละ 2", "en": "Devours offerings: -2 incense each"}},
    {"level": 4, "name": {"th": "ปอบ", "en": "Phi Pop"}, "icon": "👺", "power": 5, "from_day": 10,
     "about": {"th": "โอกาสถูกผีสิงเพิ่มเป็น 2 เท่า", "en": "Doubles the chance of possession"}},
    {"level": 5, "name": {"th": "เสือสมิง", "en": "Saming Tiger"}, "icon": "🐯", "power": 12, "from_day": 15,
     "about": {"th": "บอส! บุกแน่นอนในคืนสุดท้าย", "en": "Boss! Always attacks on the final night"}},
]

# รูปร่างของผู้รอดชีวิต (ใช้เลือกภาพเงาใน GUI เท่านั้น ไม่มีผลกับกฎ)
LOOKS = ["man", "woman", "big", "girl", "elder"]

# ทรัพยากรของศาลา
RESOURCES = {
    "food": {"name": {"th": "อาหาร", "en": "Food"}, "icon": "🍚"},
    "water": {"name": {"th": "น้ำ", "en": "Water"}, "icon": "💧"},
    "incense": {"name": {"th": "ธูปเทียน", "en": "Incense"}, "icon": "🕯"},
    "holy_water": {"name": {"th": "น้ำมนต์", "en": "Holy Water"}, "icon": "🏺"},
}

# ทักษะของผู้รอดชีวิต (ระดับ 1-5)
SKILLS = {
    "scavenge": {"th": "หาของ", "en": "Scavenge"},
    "guard": {"th": "ปราบผี", "en": "Warding"},
    "heal": {"th": "รักษา", "en": "Healing"},
}

# งานประจำวัน: skill = ทักษะที่ใช้ (None = ไม่ใช้ทักษะ), hidden = ไม่แสดงในเมนูมอบหมายงาน
JOBS = {
    "scavenge": {"name": {"th": "ออกไปหาของ", "en": "Scavenge"}, "icon": "🎒", "skill": "scavenge", "hidden": False,
                 "about": {"th": "หาอาหาร น้ำ ธูปเทียน (เสี่ยงโดนผีจู่โจม/สิง)",
                           "en": "Find food, water, incense (risk of ghost attacks)"}},
    "guard": {"name": {"th": "เฝ้ายาม", "en": "Guard"}, "icon": "🛡", "skill": "guard", "hidden": False,
              "about": {"th": "ป้องกันศาลาจากผีตอนกลางคืน", "en": "Defend the sala from night raids"}},
    "heal": {"name": {"th": "ประพรมน้ำมนต์", "en": "Bless"}, "icon": "✚", "skill": "heal", "hidden": False,
             "about": {"th": "ใช้น้ำมนต์ 1: ไล่ผีออกจากร่างก่อน ไม่งั้นรักษาคนที่ HP ต่ำสุด",
                       "en": "Use 1 holy water: drive out a ghost first, else heal the weakest"}},
    "rest": {"name": {"th": "พักผ่อน", "en": "Rest"}, "icon": "💤", "skill": None, "hidden": False,
             "about": {"th": f"ฟื้น HP {REST_HEAL}", "en": f"Recover {REST_HEAL} HP"}},
    "inspect": {"name": {"th": "ตรวจคนแปลกหน้า", "en": "Inspect newcomer"}, "icon": "🔍", "skill": None, "hidden": True,
                "about": {"th": "ส่องดูเงาของคนที่ประตู", "en": "Check the shadow of the person at the gate"}},
}

# สิ่งก่อสร้าง (สร้างได้อย่างละ 1 ครั้ง)
BUILDINGS = {
    "sacred_thread": {"name": {"th": "สายสิญจน์ล้อมศาลา", "en": "Sacred Thread"}, "icon": "🧵", "cost": {"incense": 12},
                  "about": {"th": "พลังป้องกันผีบุก +6", "en": "+6 raid defense"}},
    "vegetable_patch": {"name": {"th": "แปลงผักหลังศาลา", "en": "Vegetable Patch"}, "icon": "🥬", "cost": {"incense": 8},
               "about": {"th": "อาหาร +1 ทุกวัน", "en": "+1 food every day"}},
    "rain_barrel": {"name": {"th": "ถังรองน้ำฝน", "en": "Rain Barrel"}, "icon": "🛢", "cost": {"incense": 9},
                  "about": {"th": "น้ำ +1 ทุกวัน", "en": "+1 water every day"}},
    "spirit_house": {"name": {"th": "ศาลพระภูมิ", "en": "Spirit House"}, "icon": "🛕", "cost": {"incense": 9, "water": 3},
               "about": {"th": "น้ำมนต์ +1 ทุก 2 วัน", "en": "+1 holy water every 2 days"}},
}

# ผู้รอดชีวิตตั้งต้น
STARTING_SURVIVORS = [
    {"name": "กล้า", "skills": {"scavenge": 4, "guard": 2, "heal": 1}, "look": "man"},
    {"name": "พิกุล", "skills": {"scavenge": 2, "guard": 1, "heal": 4}, "look": "woman"},
    {"name": "สิงห์", "skills": {"scavenge": 1, "guard": 4, "heal": 1}, "look": "big"},
]

# เรื่องเล่าหน้าเปิดเรื่อง (GUI แสดงทีละบรรทัดตอนเริ่มเกมใหม่)
STORY = {
    "th": ["คืนวันฮาโลวีน... เพื่อน 3 คนไปเที่ยวงานฮาโลวีนกลางเมือง",
           "มีคนใส่ชุดผีเดินมายื่นบัตรเข้าบ้านผีสิงให้ฟรี",
           "ใต้แสงไฟในงาน... เขาไม่มีเงา",
           "แต่ไม่มีใครสังเกต",
           "พวกเราเดินเข้าไป ประตูปิดลงเอง เสียงเพลงในงานหายไป",
           "พอลืมตาขึ้นมา... เราก็อยู่อีกฝั่งแล้ว"],
    "en": ["Halloween night... three friends went to a Halloween fair downtown.",
           "Someone in a ghost costume handed them free haunted-house tickets.",
           "Under the fair lights... he had no shadow.",
           "But nobody noticed.",
           "We walked in. The door shut by itself. The music outside went silent.",
           "When we opened our eyes... we were on the other side."],
}

# ระดับความยาก: advanced = เปิดระบบเสริมทั้งหมด (สถานที่ ลาง ของแก้ผี ไฟ บนบาน ความแค้น ผีเพื่อน ตั๋ว คนแปลกหน้ามีเรื่อง)
#   resources = ของตั้งต้น, raid_chance = โอกาสผีบุกต่อคืน, wave_growth = ผีเพิ่มวันละกี่ตัว
#   hit_possess = โอกาสถูกสิงเมื่อถูกทำร้าย, omen_accuracy = ลางแม่นแค่ไหน, disguised = โอกาสคนแปลกหน้าเป็นผีปลอมตัว
DIFFICULTIES = {
    "easy": {"name": {"th": "ง่าย", "en": "Easy"}, "icon": "😊", "advanced": False, "days": 15,
             "about": {"th": "กฎพื้นฐาน เหมาะกับการเล่นครั้งแรกหรือเดโม", "en": "Basic rules, good for a first game or a demo"},
             "resources": {"food": 8, "water": 8, "incense": 5, "holy_water": 3},
             "raid_chance": 0.55, "wave_growth": 0.5, "hit_possess": 0.4, "omen_accuracy": 1.0, "disguised": 0.0},
    "normal": {"name": {"th": "ปกติ", "en": "Normal"}, "icon": "😐", "advanced": True, "days": 20,
               "about": {"th": "เปิดทุกระบบ ต้องอ่านลางและเลือกเสี่ยงให้เป็น", "en": "Every system on: read omens, pick your risks"},
               "resources": {"food": 7, "water": 7, "incense": 6, "holy_water": 2},
               "raid_chance": 0.75, "wave_growth": 0.9, "hit_possess": 0.45, "omen_accuracy": 0.75, "disguised": 0.12},
    "nightmare": {"name": {"th": "ฝันร้าย", "en": "Nightmare"}, "icon": "💀", "advanced": True, "days": 25,
                  "about": {"th": "ผีดุ ของน้อย ลางหลอกบ่อย พลาดนิดเดียวไม่รอด", "en": "Fierce ghosts, few supplies, lying omens"},
                  "resources": {"food": 5, "water": 5, "incense": 4, "holy_water": 1},
                  "raid_chance": 0.9, "wave_growth": 1.3, "hit_possess": 0.5, "omen_accuracy": 0.55, "disguised": 0.25},
}

# สถานที่ออกไปหาของ (ระดับปกติขึ้นไป): loot = ตัวคูณของที่ได้ต่อชนิด, injury = โอกาสบาดเจ็บ (ก่อนหักทักษะ)
#   possess = โอกาสถูกสิงเมื่อบาดเจ็บ, holy_water = โอกาสได้น้ำมนต์ 1, ticket = โอกาสเจอชิ้นส่วนตั๋ว, grudge = ความแค้นที่เพิ่ม
LOCATIONS = {
    "market": {"name": {"th": "ตลาดร้าง", "en": "Abandoned Market"}, "icon": "🏚",
               "loot": {"food": 2.0, "water": 0.4, "incense": 0.4}, "injury": 0.15, "possess": 0.2, "holy_water": 0.0, "ticket": 0.0, "grudge": 0,
               "about": {"th": "อาหารเยอะ ค่อนข้างปลอดภัย", "en": "Plenty of food, fairly safe"}},
    "well": {"name": {"th": "บ่อน้ำเก่า", "en": "Old Well"}, "icon": "🪣",
             "loot": {"water": 2.0, "food": 0.4}, "injury": 0.15, "possess": 0.25, "holy_water": 0.0, "ticket": 0.0, "grudge": 0,
             "about": {"th": "น้ำเยอะ ค่อนข้างปลอดภัย", "en": "Plenty of water, fairly safe"}},
    "temple": {"name": {"th": "วัดร้าง", "en": "Ruined Temple"}, "icon": "🛕",
               "loot": {"incense": 1.4, "food": 0.35}, "injury": 0.3, "possess": 0.35, "holy_water": 0.45, "ticket": 0.08, "grudge": 0,
               "about": {"th": "ธูปเทียนและน้ำมนต์ เสี่ยงปานกลาง", "en": "Incense and holy water, some risk"}},
    "graveyard": {"name": {"th": "ป่าช้า", "en": "Graveyard"}, "icon": "⚰",
                  "loot": {"incense": 1.0}, "injury": 0.5, "possess": 0.6, "holy_water": 0.3, "ticket": 0.35, "grudge": 1,
                  "about": {"th": "อาจเจอชิ้นส่วนตั๋ว อันตรายมาก ผีแค้นเพิ่ม", "en": "Ticket pieces, very dangerous, angers ghosts"}},
}

# ลางบอกเหตุของผีแต่ละเลเวล (ลางบอกว่าตัวไหนจะนำฝูงคืนนี้)
OMENS = {
    1: {"th": "ได้ยินเสียงร้องไห้แว่วมาจากชายป่า", "en": "Faint crying drifts in from the forest"},
    2: {"th": "หมาหอนทั้งคืน", "en": "Dogs howled all night"},
    3: {"th": "ข้าวบูดเร็วผิดปกติ", "en": "The rice spoiled strangely fast"},
    4: {"th": "ได้กลิ่นคาวเลือดลอยมา", "en": "The smell of blood hangs in the air"},
    5: {"th": "มีรอยเท้าเสือรอบศาลา", "en": "Tiger tracks circle the sala"},
}

# ของแก้ผี (ใช้ได้คืนเดียว): ghost = ผีที่แก้ได้, cost = ราคา
COUNTERS = {
    "rice": {"name": {"th": "ข้าวสารเสก", "en": "Blessed Rice"}, "icon": "🍚", "ghost": 1, "cost": {"incense": 2},
             "about": {"th": "วิญญาณเร่ร่อนไม่กล้าเข้าใกล้ (พลังเป็น 0)", "en": "Wandering spirits keep away (power 0)"}},
    "thorns": {"name": {"th": "หนามไผ่", "en": "Bamboo Thorns"}, "icon": "🌿", "ghost": 2, "cost": {"incense": 3},
               "about": {"th": "กระสือข้ามรั้วไม่ได้ พลังเหลือ 1", "en": "Krasue can't cross: power 1"}},
    "offering": {"name": {"th": "ของเซ่นไหว้", "en": "Offering"}, "icon": "🍌", "ghost": 3, "cost": {"food": 2},
                 "about": {"th": "เปรตกินของเซ่นแทน ไม่ทำลายธูปเทียน พลังครึ่งเดียว", "en": "Pretas eat it instead: no damage, half power"}},
    "herb": {"name": {"th": "ใบหนาด", "en": "Nad Leaves"}, "icon": "📿", "ghost": 4, "cost": {"incense": 3},
             "about": {"th": "ปอบสิงไม่ได้ง่าย (ไม่เพิ่มโอกาสถูกสิง)", "en": "Phi Pop can't possess easily"}},
    "fire": {"name": {"th": "กองไฟรอบศาลา", "en": "Ring of Fire"}, "icon": "🔥", "ghost": 5, "cost": {"incense": 4},
             "about": {"th": "เสือสมิงกลัวไฟ พลังเหลือ 5", "en": "The Saming fears fire: power 5"}},
}

# ไฟในศาลาตอนกลางคืน: raid = ตัวคูณโอกาสถูกบุก, defense = ตัวคูณพลังป้องกัน, bonus = ป้องกันเพิ่ม, cost = ราคา
LIGHTS = {
    "dark": {"name": {"th": "ดับไฟซ่อนตัว", "en": "Lights Out"}, "icon": "🌑", "raid": 0.6, "defense": 0.6, "bonus": 0, "cost": {},
             "about": {"th": "ผีหาเจอยาก แต่สู้ในความมืดได้ไม่ดี", "en": "Harder to find, but you fight blind"}},
    "normal": {"name": {"th": "ตะเกียงปกติ", "en": "Lamp"}, "icon": "🪔", "raid": 1.0, "defense": 1.0, "bonus": 0, "cost": {},
               "about": {"th": "ไม่มีผลพิเศษ", "en": "No effect"}},
    "fire": {"name": {"th": "จุดไฟรอบศาลา", "en": "Torches"}, "icon": "🔥", "raid": 1.3, "defense": 1.0, "bonus": 8,
             "cost": {"incense": 2}, "about": {"th": "ผีมาง่ายขึ้น แต่ป้องกัน +8", "en": "Draws ghosts, but +8 defense"}},
}

# บนบานศาลกล่าว: ขอแล้วต้องแก้บน (repay) ภายใน VOW_DAYS วัน ไม่งั้นโดนสาป
VOW_DAYS = 3
VOWS = {
    "calm": {"name": {"th": "ขอให้คืนนี้ผีไม่บุก", "en": "A calm night"}, "icon": "🌙", "repay": {"food": 4, "incense": 3},
             "about": {"th": "คืนนี้ไม่มีผีบุก (ยกเว้นคืนสุดท้าย)", "en": "No raid tonight (except the final night)"}},
    "water": {"name": {"th": "ขอน้ำมนต์", "en": "Holy water"}, "icon": "🏺", "repay": {"food": 5},
              "about": {"th": "น้ำมนต์ +3 ทันที", "en": "+3 holy water now"}},
    "supplies": {"name": {"th": "ขอเสบียง", "en": "Supplies"}, "icon": "🍚", "repay": {"incense": 5},
                 "about": {"th": "อาหาร +4 และน้ำ +4 ทันที", "en": "+4 food and +4 water now"}},
}

MAX_GRUDGE = 10           # ความแค้นของมิติผีสูงสุด
MERIT_COST = {"food": 3, "incense": 2}   # ทำบุญอุทิศส่วนกุศล: ลดความแค้นและส่งผีเพื่อน 1 ตนไปสู่สุคติ
FRIEND_GHOST_POWER = 6    # พลังของผีเพื่อนที่กลับมากับฝูง
TICKET_PIECES = 3         # ชิ้นส่วนตั๋วที่ต้องเก็บให้ครบเพื่อกลับบ้านก่อน

# ชื่อของคนที่อาจมาขอเข้าศาลา
STRANGER_NAMES = ["ชบา", "เทียน", "บัว", "ขุน", "จำปี", "แก้ว", "อิน", "มั่น", "แสง", "ลุงเพิ่ม", "จันทร์", "ทอง"]
# Upgrade only former built-in names; player-written names stay as entered.
CHARACTER_NAME_UPDATES = dict(zip(
    ["เคน", "แพร", "บิ๊ก", "มายด์", "โจ้", "ฝน", "ต้นกล้า", "ซาร่า", "พี่ตูน", "นัท", "แจ็ค", "เอม", "ลุงชัย", "คิม", "ป๊อป"],
    ["กล้า", "พิกุล", "สิงห์"] + STRANGER_NAMES))


def tr(text: dict) -> str:
    """เลือกข้อความตามภาษาปัจจุบันจาก dict เช่น {'th': 'อาหาร', 'en': 'Food'}"""
    return text.get(get_language(), text["th"])
