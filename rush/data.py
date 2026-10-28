#!/usr/bin/env python3
"""
Data Module - LAST SHELTER
ข้อมูลคงที่ของเกม: ทรัพยากร งาน สิ่งก่อสร้าง ผู้รอดชีวิตเริ่มต้น และค่าความยาก
Static data: resources, jobs, buildings, starting survivors, and difficulty settings.
"""

from language import get_language

GOAL_DAY = 15            # เฮลิคอปเตอร์ช่วยเหลือมาถึงหลังจบวันที่ 15 (ได้ดาวตามจำนวนคนที่รอด)
MAX_CAMP = 6             # ศูนย์พักพิงรับคนได้สูงสุด
MAX_HP = 100
MIN_SCAVENGE_HP = 40     # HP ต่ำกว่านี้ออกไปหาเสบียง/เฝ้ายามไม่ได้
STARVE_DAMAGE = 20       # ไม่มีอาหาร/น้ำ เสีย HP ต่อวัน (อย่างละ)
REST_HEAL = 15           # พักผ่อนฟื้น HP
RAID_START_DAY = 3       # ซอมบี้เริ่มบุกตั้งแต่วันนี้
WANDERER_CHANCE = 0.35   # โอกาสที่จะมีคนมาขอเข้าศูนย์ในแต่ละเช้า
WANDERER_INFECTED = 0.3  # โอกาสที่คนแปลกหน้าติดเชื้อมาแล้ว
TURN_DAYS = 2            # ติดเชื้อแล้วต้องได้ยาภายในกี่วัน ไม่งั้นกลายเป็นซอมบี้
MAX_LEVEL = 5            # เลเวลสูงสุดของพลังพิเศษ
XP_PER_LEVEL = 3         # XP ที่ต้องใช้ต่อเลเวล (Lv.1→2 ใช้ 3, Lv.2→3 ใช้ 6, ...)

# ซอมบี้ 5 เลเวล: power = พลังโจมตีต่อตัว, from_day = เริ่มโผล่วันที่
ZOMBIES = [
    {"level": 1, "name": {"th": "ซอมบี้เดิน", "en": "Walker"}, "icon": "🧟", "power": 1, "from_day": 3,
     "about": {"th": "ช้า แต่มาเป็นฝูง", "en": "Slow, but comes in numbers"}},
    {"level": 2, "name": {"th": "ซอมบี้วิ่ง", "en": "Runner"}, "icon": "🏃", "power": 2, "from_day": 5,
     "about": {"th": "แนวกั้นเหล็กป้องกันได้แค่ครึ่งเดียว", "en": "Barricades only stop half as well"}},
    {"level": 3, "name": {"th": "ซอมบี้ยักษ์", "en": "Brute"}, "icon": "💪", "power": 4, "from_day": 7,
     "about": {"th": "ทุบข้าวของ เศษวัสดุเสียหายตัวละ 2", "en": "Smashes things: -2 scrap each"}},
    {"level": 4, "name": {"th": "ซอมบี้พ่นพิษ", "en": "Spitter"}, "icon": "🤮", "power": 5, "from_day": 10,
     "about": {"th": "โอกาสติดเชื้อจากการกัดเพิ่มเป็น 2 เท่า", "en": "Doubles the infection chance of bites"}},
    {"level": 5, "name": {"th": "ราชาซอมบี้", "en": "Zombie King"}, "icon": "👹", "power": 12, "from_day": 15,
     "about": {"th": "บอส! บุกแน่นอนในคืนสุดท้าย", "en": "Boss! Always attacks on the final night"}},
]

# พลังพิเศษของผู้รอดชีวิต (คนละ 1 พลัง เลเวล 1-5)
#   job = งานที่ตรงกับพลัง (ทำงานนี้ได้ XP มากกว่า)
POWERS = {
    "marksman": {"name": {"th": "แม่นปืน", "en": "Marksman"}, "icon": "🎯", "job": "guard",
                 "about": {"th": "เฝ้ายามได้พลังป้องกัน +2 ต่อเลเวล", "en": "+2 defense per level when guarding"}},
    "immune": {"name": {"th": "ภูมิคุ้มกัน", "en": "Immune"}, "icon": "🧬", "job": "scavenge",
               "about": {"th": "โอกาสติดเชื้อลดลง 15% ต่อเลเวล", "en": "-15% infection chance per level"}},
    "mechanic": {"name": {"th": "ช่างซ่อม", "en": "Mechanic"}, "icon": "🔧", "job": "scavenge",
                 "about": {"th": "ค่าก่อสร้าง (เศษวัสดุ) ลดลง 1 ต่อเลเวล", "en": "-1 scrap build cost per level"}},
    "scout": {"name": {"th": "นักสำรวจ", "en": "Scout"}, "icon": "👃", "job": "scavenge",
              "about": {"th": "หาเสบียงได้ของเพิ่ม +1 ต่อเลเวล", "en": "+1 extra supply per level when scavenging"}},
    "scientist": {"name": {"th": "นักวิทยาศาสตร์", "en": "Scientist"}, "icon": "💉", "job": "heal",
                  "about": {"th": "ผลิตยาเองทุก (6 - เลเวล) วัน", "en": "Makes medicine every (6 - level) days"}},
}

# ทรัพยากรของศูนย์พักพิง
RESOURCES = {
    "food": {"name": {"th": "อาหาร", "en": "Food"}, "icon": "🥫"},
    "water": {"name": {"th": "น้ำ", "en": "Water"}, "icon": "💧"},
    "scrap": {"name": {"th": "เศษวัสดุ", "en": "Scrap"}, "icon": "🔩"},
    "medicine": {"name": {"th": "ยา", "en": "Medicine"}, "icon": "💊"},
}

# ทักษะของผู้รอดชีวิต (ระดับ 1-5)
SKILLS = {
    "scavenge": {"th": "หาเสบียง", "en": "Scavenge"},
    "guard": {"th": "ต่อสู้", "en": "Combat"},
    "heal": {"th": "รักษา", "en": "Medic"},
}

# งานประจำวัน: skill = ทักษะที่ใช้ (None = ไม่ใช้ทักษะ), hidden = ไม่แสดงในเมนูมอบหมายงาน
JOBS = {
    "scavenge": {"name": {"th": "ออกไปหาเสบียง", "en": "Scavenge"}, "icon": "🎒", "skill": "scavenge", "hidden": False,
                 "about": {"th": "หาอาหาร น้ำ เศษวัสดุ (เสี่ยงโดนข่วน/ติดเชื้อ)",
                           "en": "Find food, water, scrap (risk of bites)"}},
    "guard": {"name": {"th": "เฝ้ายาม", "en": "Guard"}, "icon": "🛡", "skill": "guard", "hidden": False,
              "about": {"th": "ป้องกันศูนย์จากซอมบี้ตอนกลางคืน", "en": "Defend the shelter from night raids"}},
    "heal": {"name": {"th": "รักษา", "en": "Heal"}, "icon": "✚", "skill": "heal", "hidden": False,
             "about": {"th": "ใช้ยา 1 ชิ้น: รักษาคนติดเชื้อก่อน ไม่งั้นรักษาคนที่ HP ต่ำสุด",
                       "en": "Use 1 medicine: cure the infected first, else heal the weakest"}},
    "rest": {"name": {"th": "พักผ่อน", "en": "Rest"}, "icon": "💤", "skill": None, "hidden": False,
             "about": {"th": f"ฟื้น HP {REST_HEAL}", "en": f"Recover {REST_HEAL} HP"}},
    "inspect": {"name": {"th": "ตรวจคนแปลกหน้า", "en": "Inspect newcomer"}, "icon": "🔍", "skill": None, "hidden": True,
                "about": {"th": "ตรวจร่างกายคนที่ประตู", "en": "Check the person at the gate"}},
}

# สิ่งก่อสร้าง (สร้างได้อย่างละ 1 ครั้ง)
BUILDINGS = {
    "barricade": {"name": {"th": "แนวกั้นเหล็ก", "en": "Barricade"}, "icon": "🚧", "cost": {"scrap": 12},
                  "about": {"th": "พลังป้องกันการบุก +6", "en": "+6 raid defense"}},
    "garden": {"name": {"th": "แปลงผักบนดาดฟ้า", "en": "Rooftop Garden"}, "icon": "🥬", "cost": {"scrap": 8},
               "about": {"th": "อาหาร +1 ทุกวัน", "en": "+1 food every day"}},
    "collector": {"name": {"th": "ถังเก็บน้ำฝน", "en": "Rain Collector"}, "icon": "🛢", "cost": {"scrap": 9},
                  "about": {"th": "น้ำ +1 ทุกวัน", "en": "+1 water every day"}},
    "clinic": {"name": {"th": "ห้องปฐมพยาบาล", "en": "First-Aid Room"}, "icon": "🏥", "cost": {"scrap": 9, "water": 3},
               "about": {"th": "ยา +1 ทุก 2 วัน", "en": "+1 medicine every 2 days"}},
}

# ผู้รอดชีวิตตั้งต้น
STARTING_SURVIVORS = [
    {"name": "เคน", "skills": {"scavenge": 4, "guard": 2, "heal": 1}, "power": "scout", "level": 2},
    {"name": "หมอแพร", "skills": {"scavenge": 2, "guard": 1, "heal": 4}, "power": "scientist", "level": 1},
    {"name": "บิ๊ก", "skills": {"scavenge": 1, "guard": 4, "heal": 1}, "power": "marksman", "level": 2},
]

# ชื่อของคนที่อาจมาขอเข้าศูนย์
WANDERER_NAMES = ["มายด์", "โจ้", "ฝน", "ต้นกล้า", "ซาร่า", "พี่ตูน", "นัท", "แจ็ค", "เอม", "ลุงชัย", "คิม", "ป๊อป"]


def tr(text: dict) -> str:
    """เลือกข้อความตามภาษาปัจจุบันจาก dict เช่น {'th': 'อาหาร', 'en': 'Food'}"""
    return text.get(get_language(), text["th"])
