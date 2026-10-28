#!/usr/bin/env python3
"""
Forge Module - OVERGEAR (ร้านตีอาวุธ)
ตีอาวุธ: เลือกส่วนประกอบ คำนวณคะแนนคุณภาพ เพดานเกรด สุ่มเกรด (ตีวิกฤต 5%) มินิเกมเตาหลอม
และการลงทุน (อัปเกรดเตา ลูกมือ แม่พิมพ์) กับการจัดการอาวุธบนชั้นวาง
Forging: parts, quality score, grade cap, grade roll, the furnace mini-game, upgrades, and the weapon rack.
"""

import math
import random

from language import get_text, clear_screen
from data import (WEAPONS, MATERIALS, GRADES, SLOTS, MYTHIC, LEGENDARY, EPIC, MAX_FORGE_LEVEL, CRIT_CHANCE,
                  FORGE_UPGRADE, APPRENTICE_HIRE, BASE_FORGES, MAX_STOCK, TARGET_PROGRESS, BASE_TURNS, MAX_HEAT,
                  SWEET_HEAT, GOOD_HEAT, RATING_VALUE, AUTO_ACCURACY, APPRENTICE_ACCURACY, tr)
from ui import heading, choose_from_list, ask_yes_no, bar, show_error
import market
import storage

ACTIONS = {
    "hard": {"name": {"th": "ตีแรง", "en": "Hard strike"}, "icon": "🔨", "progress": 2, "heat": 1},
    "light": {"name": {"th": "ตีเบา", "en": "Light tap"}, "icon": "🔧", "progress": 1, "heat": 0},
    "heat": {"name": {"th": "สูบลมเผาไฟ", "en": "Pump the bellows"}, "icon": "🔥", "progress": 0, "heat": 0},
    "wait": {"name": {"th": "รอให้เย็นลง", "en": "Let it cool"}, "icon": "💨", "progress": 0, "heat": 0},
}
RATINGS = {"perfect": {"th": "สมบูรณ์แบบ!", "en": "PERFECT!"}, "good": {"th": "ดี", "en": "Good"},
           "bad": {"th": "แย่", "en": "Poor"}}


# ---------- ส่วนประกอบและสูตร ----------

def materials_for(mold: str, parts: dict) -> dict:
    """วัตถุดิบที่ต้องใช้ทั้งหมด เช่น ดาบ = โลหะ 2 + ด้าม 1 (+ เครื่องประดับ 1)"""
    need = {parts["blade"]: WEAPONS[mold]["blade"]}
    need[parts["handle"]] = need.get(parts["handle"], 0) + 1
    if parts.get("gem"):
        need[parts["gem"]] = need.get(parts["gem"], 0) + 1
    return need


def part_list(parts: dict) -> list:
    """รายการวัตถุดิบที่ใส่ (ไม่รวมช่องว่าง)"""
    return [parts[slot] for slot in ("blade", "handle", "gem") if parts.get(slot)]


def legend_count(parts: dict) -> int:
    """จำนวนชิ้นส่วนที่เป็นวัตถุดิบตำนาน"""
    return sum(1 for key in part_list(parts) if MATERIALS[key]["legend"])


def grade_cap(parts: dict, forge_level: int, perfect: bool) -> int:
    """
    เพดานเกรดตามวัตถุดิบ:
    เหล็กได้สูงสุดแรร์ เงินอีปิค มิธริลตำนาน เหล็กดาวตกเทพนิยาย
    ไม่มีของตำนานเลย -> ไม่เกินอีปิค
    เทพนิยายต้องมีของตำนานครบ 3 ชิ้น + เตาเลเวลสูงสุด + ตีสมบูรณ์แบบทุกจังหวะ
    """
    cap = MATERIALS[parts["blade"]]["cap"]
    legends = legend_count(parts)
    if legends == 0:
        cap = min(cap, EPIC)
    if not (legends == 3 and forge_level >= MAX_FORGE_LEVEL and perfect):
        cap = min(cap, LEGENDARY)
    return cap


def quality_score(parts: dict, forge_level: int, accuracy: int) -> int:
    """คะแนนคุณภาพ = คะแนนวัตถุดิบ + เลเวลเตา + ความแม่นในมินิเกม (0-10)"""
    points = sum(MATERIALS[key]["points"] for key in part_list(parts))
    return points + (forge_level - 1) * 2 + accuracy


def grade_from_score(score: int) -> int:
    """เกรดสูงสุดที่คะแนนถึงเกณฑ์ (ระดับนรกเหล็กกล้าเกณฑ์สูงขึ้น)"""
    extra = storage.setting("grade_need")
    grade = 0
    for index, info in enumerate(GRADES):
        if score >= info["need"] + extra:
            grade = index
    return grade


def roll_grade(quality: int, cap: int, rng: random.Random) -> tuple:
    """
    เกรดจริง = เกรดตามคะแนน แต่ไม่เกินเพดาน และมีโอกาส 5% ตีวิกฤตขึ้นอีก 1 ขั้น (ไม่เกินเพดาน)
    คืนค่า (เกรด, ตีวิกฤตหรือไม่)
    """
    grade = min(grade_from_score(quality), cap)
    if grade < cap and rng.random() < CRIT_CHANCE:
        return grade + 1, True
    return grade, False


def weapon_stats(mold: str, parts: dict, grade: int, accuracy: int, forge_level: int) -> dict:
    """ค่าพลังของอาวุธ: คม ทนทาน น้ำหนัก พลัง (= (คม + ทนทาน) × ตัวคูณเกรด) ความทนทานสูงสุด และมูลค่า"""
    base = WEAPONS[mold]
    blade = MATERIALS[parts["blade"]]
    handle = MATERIALS[parts["handle"]]
    gem = MATERIALS[parts["gem"]] if parts.get("gem") else {"sharp": 0, "sturdy": 0}
    sharp = base["sharp"] + blade["sharp"] + gem["sharp"] + accuracy // 4
    sturdy = base["sturdy"] + blade["sturdy"] + handle["sturdy"] + gem["sturdy"] + (forge_level - 1) // 2
    weight = max(1, base["weight"] + blade["weight"] + handle["weight"])
    power = round((sharp + sturdy) * GRADES[grade]["power"])
    value = round(base["value"] * GRADES[grade]["price"] * (1 + (sharp + sturdy) / 20))
    return {"sharp": sharp, "sturdy": sturdy, "weight": weight, "power": power, "max_dur": 3 + sturdy,
            "value": value}


def expected_grade(parts: dict, accuracy: int) -> int:
    """เกรดที่คาดว่าจะได้ (ไม่นับตีวิกฤต) ใช้แนะนำสูตรและแสดงตัวอย่าง"""
    level = storage.state["forge_level"]
    perfect = accuracy >= 10
    return min(grade_from_score(quality_score(parts, level, accuracy)), grade_cap(parts, level, perfect))


def make_weapon(mold: str, parts: dict, accuracy: int, perfect: bool, rng: random.Random) -> dict:
    """สร้างอาวุธ 1 ชิ้น (สุ่มเกรด) วางบนชั้นวาง และจดสถิติ"""
    state = storage.state
    level = state["forge_level"]
    quality = quality_score(parts, level, accuracy)
    grade, crit = roll_grade(quality, grade_cap(parts, level, perfect), rng)
    weapon = {"id": storage.next_id(), "name": "", "type": mold, "grade": grade, "parts": dict(parts),
              "day": state["day"], "crit": crit, "quality": quality, "accuracy": accuracy}
    weapon.update(weapon_stats(mold, parts, grade, accuracy, level))
    weapon["dur"] = weapon["max_dur"]
    state["weapons"].append(weapon)
    log = state["log"]
    log["forged"] += 1
    log["grades"][grade] += 1
    log["crits"] += int(crit)
    if log["best"] is None or (grade, weapon["power"]) > (log["best"]["grade"], log["best"]["power"]):
        log["best"] = {"type": mold, "grade": grade, "power": weapon["power"], "day": state["day"]}
    return weapon


def weapon_label(weapon: dict) -> str:
    """ชื่ออาวุธแบบสั้น เช่น 🗡 ดาบ 🔵แรร์ «Dawn» พลัง 14"""
    grade = GRADES[weapon["grade"]]
    name = f" «{weapon['name']}»" if weapon.get("name") else ""
    return (f"{WEAPONS[weapon['type']]['icon']} {tr(WEAPONS[weapon['type']]['name'])} "
            f"{grade['icon']}{tr(grade['name'])}{name} {get_text('พลัง', 'PWR')} {weapon['power']}")


def weapon_detail(weapon: dict) -> str:
    """ค่าพลังทั้งหมดของอาวุธในบรรทัดเดียว"""
    return get_text(f"คม {weapon['sharp']}  ทน {weapon['sturdy']}  หนัก {weapon['weight']}  "
                    f"ความทนทาน {weapon['dur']}/{weapon['max_dur']}  มูลค่า {weapon['value']}",
                    f"Sharp {weapon['sharp']}  Sturdy {weapon['sturdy']}  Weight {weapon['weight']}  "
                    f"Durability {weapon['dur']}/{weapon['max_dur']}  Value {weapon['value']}")


# ---------- กฎก่อนตี ----------

def forges_per_day() -> int:
    """จำนวนครั้งที่ตี/ซ่อมได้ต่อวัน (ลูกมือ +1)"""
    return BASE_FORGES + (1 if storage.state["apprentice"] else 0)


def check_forge(mold: str, parts: dict) -> str:
    """กฎก่อนตี: มีแม่พิมพ์ วัตถุดิบตรงช่อง วัตถุดิบครบ ยังมีแรงตีวันนี้ และชั้นวางไม่เต็ม"""
    state = storage.state
    if mold not in WEAPONS:
        return get_text("ไม่มีอาวุธแบบนี้", "Unknown weapon type.")
    if mold not in state["molds"]:
        return get_text(f"ยังไม่มีแม่พิมพ์{tr(WEAPONS[mold]['name'])}", f"You don't own a {tr(WEAPONS[mold]['name'])} mold.")
    for slot in ("blade", "handle", "gem"):
        key = parts.get(slot)
        if slot != "gem" and not key:
            return get_text(f"ยังไม่ได้เลือก{tr(SLOTS[slot])}", f"No {tr(SLOTS[slot])} chosen.")
        if key and (key not in MATERIALS or MATERIALS[key]["slot"] != slot):
            return get_text(f"วัตถุดิบนี้ใช้เป็น{tr(SLOTS[slot])}ไม่ได้", f"That material can't be a {tr(SLOTS[slot])}.")
    if state["forging"]:
        return get_text("ยังตีชิ้นเดิมไม่เสร็จ", "Finish the piece on the anvil first.")
    if state["forges_left"] <= 0:
        return get_text("วันนี้ตีครบแล้ว (เตาต้องพัก) จบวันก่อน", "No forging left today. End the day first.")
    if len(state["weapons"]) >= MAX_STOCK:
        return get_text(f"ชั้นวางอาวุธเต็ม ({MAX_STOCK} ชิ้น) ส่งหรือขายก่อน",
                        f"Weapon rack is full ({MAX_STOCK}). Deliver or sell first.")
    return storage.check_materials(materials_for(mold, parts))


def use_materials(mold: str, parts: dict) -> None:
    """หักวัตถุดิบและแรงตีของวันนี้"""
    for key, amount in materials_for(mold, parts).items():
        storage.state["materials"][key] -= amount
    storage.state["forges_left"] -= 1


# ---------- มินิเกมเตาหลอม ----------

def do_start_forge(mold: str, parts: dict, rng: random.Random = None) -> str:
    """เริ่มตีด้วยมือ: หักวัตถุดิบ แล้ววางเหล็กร้อนบนทั่ง (state['forging'])"""
    rng = rng or random.Random()
    error = check_forge(mold, parts)
    if error:
        return error
    use_materials(mold, parts)
    storage.state["forging"] = {"mold": mold, "parts": dict(parts), "heat": rng.randint(*SWEET_HEAT),
                                "progress": 0, "turns": BASE_TURNS + storage.state["forge_level"],
                                "score": 0.0, "ratings": [], "last": ""}
    storage.save_game()
    return ""


def rate_heat(heat: int) -> str:
    """ตีตอนเหล็กร้อนแค่ไหน: 6-8 สมบูรณ์แบบ, 4-9 ดี, นอกนั้นแย่"""
    if SWEET_HEAT[0] <= heat <= SWEET_HEAT[1]:
        return "perfect"
    if GOOD_HEAT[0] <= heat <= GOOD_HEAT[1]:
        return "good"
    return "bad"


def do_strike(action: str, rng: random.Random = None) -> str:
    """
    ทำ 1 จังหวะในมินิเกม: ตีแรง (+2 ขึ้นรูป) / ตีเบา (+1) / สูบลม (ร้อนขึ้น 2-4) / รอ (เย็นลง)
    ทุกครั้งที่ตีหรือรอ เหล็กจะเย็นลงตามระดับความยาก
    """
    rng = rng or random.Random()
    session = storage.state["forging"]
    if not session:
        return get_text("ไม่มีเหล็กบนทั่ง", "Nothing on the anvil.")
    if action not in ACTIONS:
        return get_text("ไม่มีท่านี้", "Unknown action.")
    if forge_done(session):
        return get_text("ชิ้นนี้เสร็จแล้ว", "This piece is finished.")

    info = ACTIONS[action]
    if action == "heat":
        session["heat"] = min(MAX_HEAT, session["heat"] + rng.randint(2, 4))
        session["last"] = "heat"
    else:
        if info["progress"]:
            rating = rate_heat(session["heat"])
            gain = min(info["progress"], TARGET_PROGRESS - session["progress"])
            session["progress"] += gain
            session["score"] += RATING_VALUE[rating] * gain
            session["ratings"].append(rating)
            session["heat"] -= info["heat"]
            session["last"] = rating
        else:
            session["last"] = "wait"
        session["heat"] = max(0, session["heat"] - rng.randint(*storage.setting("cool")))
    session["turns"] -= 1
    storage.save_game()
    return ""


def forge_done(session: dict) -> bool:
    """มินิเกมจบเมื่อขึ้นรูปครบ หรือถ่านหมด (จำนวนจังหวะหมด)"""
    return session["progress"] >= TARGET_PROGRESS or session["turns"] <= 0


def session_accuracy(session: dict) -> int:
    """ความแม่น 0-10 = คะแนนจังหวะที่ตี ÷ จำนวนที่ต้องขึ้นรูป (ส่วนที่ยังไม่ได้ตีนับ 0)"""
    return round(10 * session["score"] / TARGET_PROGRESS)


def session_perfect(session: dict) -> bool:
    """ตีสมบูรณ์แบบทุกจังหวะ และขึ้นรูปครบ"""
    return session["progress"] >= TARGET_PROGRESS and all(r == "perfect" for r in session["ratings"])


def suggest_action(session: dict) -> str:
    """
    แนะนำท่าต่อไป: ร้อนเกินรอให้เย็น, ร้อนพอดีตีแรง (เหลือ 1 จังหวะตีเบา),
    เย็นไปสูบลม ถ้ายังเหลือจังหวะพอ ไม่งั้นตีเลย
    """
    remaining = TARGET_PROGRESS - session["progress"]
    heat = session["heat"]
    strikes_needed = math.ceil(remaining / 2)
    if heat > SWEET_HEAT[1] and session["turns"] > strikes_needed:
        return "wait"
    if heat < SWEET_HEAT[0] and session["turns"] > strikes_needed:
        return "heat"
    return "hard" if remaining >= 2 else "light"


def do_finish_forge(rng: random.Random = None) -> dict:
    """จบมินิเกม: คำนวณความแม่น สุ่มเกรด แล้ววางอาวุธบนชั้นวาง คืนค่าอาวุธ (หรือ None ถ้าไม่มีงานค้าง)"""
    rng = rng or random.Random()
    session = storage.state["forging"]
    if not session:
        return None
    weapon = make_weapon(session["mold"], session["parts"], session_accuracy(session), session_perfect(session), rng)
    storage.state["forging"] = None
    storage.save_game()
    return weapon


def auto_accuracy() -> int:
    """ความแม่นเมื่อให้ตีอัตโนมัติ (มีลูกมือแม่นกว่า)"""
    return APPRENTICE_ACCURACY if storage.state["apprentice"] else AUTO_ACCURACY


def do_auto_forge(mold: str, parts: dict, rng: random.Random = None) -> str:
    """ตีแบบอัตโนมัติ (ไม่เล่นมินิเกม) ความแม่นคงที่ และไม่มีทางได้เทพนิยาย อาวุธใหม่อยู่ท้ายชั้นวาง"""
    rng = rng or random.Random()
    error = check_forge(mold, parts)
    if error:
        return error
    use_materials(mold, parts)
    make_weapon(mold, parts, auto_accuracy(), False, rng)
    storage.save_game()
    return ""


# ---------- การลงทุน ----------

def do_upgrade_forge() -> str:
    """อัปเกรดเตา: คะแนนคุณภาพ +2 ต่อเลเวล มินิเกมมีจังหวะเพิ่ม และเลเวล 4 ปลดล็อกเทพนิยาย"""
    state = storage.state
    if state["forge_level"] >= MAX_FORGE_LEVEL:
        return get_text("เตาเลเวลสูงสุดแล้ว", "The forge is already at max level.")
    cost = FORGE_UPGRADE[state["forge_level"] + 1]
    error = storage.check_gold(cost)
    if error:
        return error
    storage.pay(cost)
    state["forge_level"] += 1
    storage.save_game()
    return ""


def do_hire() -> str:
    """จ้างลูกมือ: ตีได้วันละ +1 ครั้ง และตีอัตโนมัติแม่นขึ้น (มีค่าจ้างรายวัน)"""
    state = storage.state
    if state["apprentice"]:
        return get_text("มีลูกมืออยู่แล้ว", "You already have an apprentice.")
    error = storage.check_gold(APPRENTICE_HIRE)
    if error:
        return error
    storage.pay(APPRENTICE_HIRE)
    state["apprentice"] = True
    state["forges_left"] += 1
    storage.save_game()
    return ""


def do_fire() -> str:
    """เลิกจ้างลูกมือ (ประหยัดค่าจ้าง)"""
    state = storage.state
    if not state["apprentice"]:
        return get_text("ยังไม่มีลูกมือ", "You have no apprentice.")
    state["apprentice"] = False
    state["forges_left"] = max(0, state["forges_left"] - 1)
    storage.save_game()
    return ""


def do_buy_mold(mold: str) -> str:
    """ซื้อแม่พิมพ์อาวุธแบบใหม่"""
    state = storage.state
    if mold not in WEAPONS:
        return get_text("ไม่มีอาวุธแบบนี้", "Unknown weapon type.")
    if mold in state["molds"]:
        return get_text("มีแม่พิมพ์นี้แล้ว", "You already own this mold.")
    error = storage.check_gold(WEAPONS[mold]["mold"])
    if error:
        return error
    storage.pay(WEAPONS[mold]["mold"])
    state["molds"].append(mold)
    storage.save_game()
    return ""


# ---------- ชั้นวางอาวุธ (ดู / สลักชื่อ / หลอมคืน) ----------

def validate_engraving(text: str) -> str:
    """ชื่อที่สลักต้องไม่ว่าง ยาวไม่เกิน 14 ตัวอักษร และไม่ซ้ำกับอาวุธชิ้นอื่น"""
    if not text:
        return get_text("ชื่อห้ามว่าง", "The name can't be empty.")
    if len(text) > 14:
        return get_text("ชื่อยาวไม่เกิน 14 ตัวอักษร", "Name must be 14 characters or less.")
    names = [w.get("name", "").lower() for w in storage.state["weapons"]]
    if text.lower() in names:
        return get_text("มีอาวุธชื่อนี้แล้ว", "Another weapon already has that name.")
    return ""


def do_engrave(weapon: dict, text: str) -> str:
    """สลักชื่อบนอาวุธ (แก้ไขข้อมูลอาวุธ)"""
    text = text.strip()
    if weapon not in storage.state["weapons"]:
        return get_text("ไม่มีอาวุธชิ้นนี้บนชั้นวาง", "That weapon is not on the rack.")
    error = validate_engraving(text)
    if error:
        return error
    weapon["name"] = text
    storage.save_game()
    return ""


def melt_return(weapon: dict) -> dict:
    """หลอมคืนได้โลหะใบมีดกลับมาครึ่งหนึ่ง (ปัดลง อย่างน้อย 1 ชิ้น)"""
    blade = weapon["parts"]["blade"]
    return {blade: max(1, WEAPONS[weapon["type"]]["blade"] // 2)}


def do_melt(weapon: dict) -> str:
    """หลอมอาวุธทิ้ง (ลบออกจากชั้นวาง) แล้วได้โลหะคืนบางส่วน"""
    state = storage.state
    if weapon not in state["weapons"]:
        return get_text("ไม่มีอาวุธชิ้นนี้บนชั้นวาง", "That weapon is not on the rack.")
    back = melt_return(weapon)
    error = storage.check_space(sum(back.values()))
    if error:
        return error
    state["weapons"].remove(weapon)
    for key, amount in back.items():
        state["materials"][key] += amount
    storage.save_game()
    return ""


# ---------- เมนู Terminal ----------

def owned_for(slot: str, amount: int) -> list:
    """วัตถุดิบในคลังที่ใช้กับช่องนี้ได้และมีพอ"""
    return [key for key, info in MATERIALS.items()
            if info["slot"] == slot and storage.state["materials"][key] >= amount]


def choose_parts(mold: str):
    """ให้ผู้เล่นเลือก ใบมีด + ด้าม + เครื่องประดับ จากของในคลัง คืนค่า parts หรือ None ถ้ายกเลิก"""
    state = storage.state
    parts = {}
    need = {"blade": WEAPONS[mold]["blade"], "handle": 1, "gem": 1}
    for slot in ("blade", "handle", "gem"):
        options = owned_for(slot, need[slot])
        print(get_text(f"\n{tr(SLOTS[slot])} (ต้องใช้ {need[slot]} ชิ้น):", f"\n{tr(SLOTS[slot])} (needs {need[slot]}):"))
        if slot == "gem":
            options = ["none"] + options        # เครื่องประดับไม่ใส่ก็ได้
        if not options:
            print(get_text("  ✖ ในคลังไม่มีพอ ไปซื้อที่ตลาดก่อน", "  ✖ Not enough in storage. Visit the market."))
            return None
        for number, key in enumerate(options, start=1):
            if key == "none":
                print(get_text(f"  {number}. (ไม่ใส่)", f"  {number}. (none)"))
                continue
            info = MATERIALS[key]
            cap = f" {get_text('เพดาน', 'cap')} {GRADES[info['cap']]['icon']}" if info["cap"] is not None else ""
            legend = " ★" if info["legend"] else ""
            print(f"  {number}. {market.material_text(key)} x{state['materials'][key]}  "
                  f"{get_text('คม', 'SHP')}+{info['sharp']} {get_text('ทน', 'STD')}+{info['sturdy']} "
                  f"{get_text('คะแนน', 'pts')}+{info['points']}{cap}{legend}")
        choice = choose_from_list(options, "เลือก", "Choose")
        if choice is None:
            return None
        parts[slot] = None if choice == "none" else choice
    # ใบมีดกับด้ามเป็นคนละช่อง จึงใช้วัตถุดิบชิ้นเดียวกันซ้ำไม่ได้อยู่แล้ว แต่ตรวจจำนวนรวมอีกรอบ
    if show_error(storage.check_materials(materials_for(mold, parts))):
        return None
    return parts


def preview(mold: str, parts: dict) -> None:
    """แสดงตัวอย่างเกรดและค่าพลังที่คาดว่าจะได้ก่อนตี"""
    level = storage.state["forge_level"]
    cap = grade_cap(parts, level, True)
    for label_th, label_en, accuracy in (("ตีเองแม่นๆ", "Manual (good)", 9),
                                         ("ตีอัตโนมัติ", "Automatic", auto_accuracy())):
        grade = expected_grade(parts, accuracy)
        stats = weapon_stats(mold, parts, grade, accuracy, level)
        print(get_text(f"  {label_th:<12} → {GRADES[grade]['icon']} {tr(GRADES[grade]['name'])} พลัง {stats['power']} "
                       f"คม {stats['sharp']} หนัก {stats['weight']}",
                       f"  {label_en:<14} → {GRADES[grade]['icon']} {tr(GRADES[grade]['name'])} PWR {stats['power']} "
                       f"sharp {stats['sharp']} weight {stats['weight']}"))
    print(get_text(f"  เพดานเกรดของสูตรนี้: {GRADES[cap]['icon']} {tr(GRADES[cap]['name'])}",
                   f"  Grade cap of this recipe: {GRADES[cap]['icon']} {tr(GRADES[cap]['name'])}"))
    if cap < MYTHIC and legend_count(parts) == 3:
        print(get_text("  (เทพนิยายต้องมีเตาเลเวล 4 และตีสมบูรณ์แบบทุกจังหวะ)",
                       "  (Mythic needs a level-4 forge and every strike perfect)"))


def heat_line(heat: int) -> str:
    """แถบความร้อนของเหล็ก พร้อมบอกโซน"""
    zone = rate_heat(heat)
    label = {"perfect": get_text("ร้อนพอดี", "just right"), "good": get_text("พอใช้", "okay"),
             "bad": get_text("ร้อนเกิน!" if heat > GOOD_HEAT[1] else "เย็นไป!", "too hot!" if heat > GOOD_HEAT[1]
                             else "too cold!")}[zone]
    cells = "".join("▓" if i < heat else "·" for i in range(MAX_HEAT))
    return f"🌡 [{cells}] {heat}/{MAX_HEAT} {label}"


def play_minigame(rng: random.Random = None) -> dict:
    """มินิเกมเตาหลอมบน Terminal: เลือกท่าทีละจังหวะจนขึ้นรูปเสร็จหรือถ่านหมด"""
    keys = list(ACTIONS)
    session = storage.state["forging"]
    while session and not forge_done(session):
        clear_screen()
        heading("เตาหลอม - ตีขณะเหล็กยังร้อน", "THE FURNACE - strike while the iron is hot")
        print(get_text(" ตีตอนความร้อน 6-8 = สมบูรณ์แบบ, 4-9 = ดี, นอกนั้น = แย่",
                       " Strike at heat 6-8 = perfect, 4-9 = good, otherwise poor"))
        print(f"\n {heat_line(session['heat'])}")
        print(get_text(f" ⚒ ขึ้นรูป [{bar(session['progress'], TARGET_PROGRESS, TARGET_PROGRESS)}] "
                       f"{session['progress']}/{TARGET_PROGRESS}   🪨 ถ่านเหลือ {session['turns']} จังหวะ",
                       f" ⚒ Shape [{bar(session['progress'], TARGET_PROGRESS, TARGET_PROGRESS)}] "
                       f"{session['progress']}/{TARGET_PROGRESS}   🪨 {session['turns']} moves of coal left"))
        if session["last"] in RATINGS:
            print(get_text(" จังหวะที่แล้ว: ", " Last strike: ") + tr(RATINGS[session["last"]]))
        tip = suggest_action(session)
        print()
        for number, key in enumerate(keys, start=1):
            mark = get_text("  💡 แนะนำ", "  💡 tip") if key == tip else ""
            print(f" {number}. {ACTIONS[key]['icon']} {tr(ACTIONS[key]['name'])}{mark}")
        choice = input(get_text("\nเลือกท่า: ", "\nYour move: ")).strip()
        if choice in ("1", "2", "3", "4"):
            do_strike(keys[int(choice) - 1], rng)
        else:
            print(get_text("กรุณาเลือก 1-4", "Please choose 1-4."))
            input(get_text("กด Enter...", "Press Enter..."))
    accuracy = session_accuracy(session)
    perfect = session_perfect(session)
    weapon = do_finish_forge(rng)
    print(get_text(f"\nความแม่น {accuracy}/10" + ("  ✨ สมบูรณ์แบบทุกจังหวะ!" if perfect else ""),
                   f"\nAccuracy {accuracy}/10" + ("  ✨ Every strike perfect!" if perfect else "")))
    return weapon


def announce(weapon: dict) -> None:
    """ประกาศอาวุธที่เพิ่งตีเสร็จ"""
    if weapon["crit"]:
        print(get_text("💥 ตีวิกฤต! เกรดขึ้นอีก 1 ขั้น!", "💥 CRITICAL FORGE! One grade higher!"))
    print(get_text("✔ ตีเสร็จ: ", "✔ Forged: ") + weapon_label(weapon))
    print("   " + weapon_detail(weapon))


def forge_flow(mold: str, parts: dict) -> None:
    """ถามวิธีตี (มินิเกม / อัตโนมัติ) แล้วตีตามสูตร"""
    error = check_forge(mold, parts)
    if show_error(error):
        return
    preview(mold, parts)
    print(get_text("\n1. 🔥 ตีเอง (มินิเกม แม่นได้ถึง 10 และลุ้นเทพนิยาย)",
                   "\n1. 🔥 Forge by hand (mini-game, up to 10 accuracy, Mythic possible)"))
    who = get_text("ลูกมือ", "apprentice") if storage.state["apprentice"] else get_text("ตีลวกๆ", "rushed")
    print(get_text(f"2. ⚡ ตีอัตโนมัติ ({who} ความแม่น {auto_accuracy()})",
                   f"2. ⚡ Automatic ({who}, accuracy {auto_accuracy()})"))
    choice = input(get_text("เลือก (0 = ยกเลิก): ", "Choose (0 = cancel): ")).strip()
    if choice == "1":
        if not show_error(do_start_forge(mold, parts)):
            announce(play_minigame())
            engrave_prompt(storage.state["weapons"][-1])
    elif choice == "2":
        if not show_error(do_auto_forge(mold, parts)):
            announce(storage.state["weapons"][-1])
    elif choice != "0":
        print(get_text("ไม่มีตัวเลือกนี้", "Invalid option."))


def engrave_prompt(weapon: dict) -> None:
    """ถามว่าจะสลักชื่ออาวุธเลยไหม (เฉพาะเกรดอีปิคขึ้นไป)"""
    if weapon["grade"] >= EPIC and ask_yes_no("สลักชื่ออาวุธชิ้นนี้ไหม", "Engrave a name on it"):
        text = input(get_text("ชื่อ: ", "Name: "))
        if not show_error(do_engrave(weapon, text)):
            print(get_text("✔ สลักชื่อแล้ว", "✔ Engraved."))


def forge_menu() -> None:
    """เมนูตีอาวุธแบบเลือกสูตรเอง (ตีให้ออเดอร์ด้วยสูตรแนะนำอยู่ในกระดานออเดอร์)"""
    state = storage.state
    if state["forging"]:
        print(get_text("มีเหล็กค้างบนทั่ง ตีต่อให้เสร็จ...", "A piece is still on the anvil. Finishing it..."))
        input(get_text("กด Enter...", "Press Enter..."))
        announce(play_minigame())
        return
    heading("ตีอาวุธ (เลือกสูตรเอง)", "FORGE (custom recipe)")
    print(get_text(f" เตาเลเวล {state['forge_level']}/{MAX_FORGE_LEVEL}   ตีได้อีก {state['forges_left']} ครั้งวันนี้   "
                   f"ชั้นวาง {len(state['weapons'])}/{MAX_STOCK}",
                   f" Forge lv {state['forge_level']}/{MAX_FORGE_LEVEL}   {state['forges_left']} forgings left today   "
                   f"Rack {len(state['weapons'])}/{MAX_STOCK}"))
    molds = list(state["molds"])
    for number, mold in enumerate(molds, start=1):
        info = WEAPONS[mold]
        print(get_text(f" {number}. {info['icon']} {tr(info['name']):<8} โลหะ {info['blade']}  คม {info['sharp']} "
                       f"ทน {info['sturdy']} หนัก {info['weight']}",
                       f" {number}. {info['icon']} {tr(info['name']):<9} metal {info['blade']}  sharp {info['sharp']} "
                       f"sturdy {info['sturdy']} weight {info['weight']}"))
    mold = choose_from_list(molds, "เลือกแบบอาวุธ", "Choose a weapon type")
    if mold is None:
        return
    parts = choose_parts(mold)
    if parts is None:
        return
    print()
    forge_flow(mold, parts)
