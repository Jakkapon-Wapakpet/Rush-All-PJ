#!/usr/bin/env python3
"""
Realm Module - GHOST REALM (มิติผี)
ระบบเสริมของระดับปกติขึ้นไป: สถานที่หาของ ลางบอกเหตุ ของแก้ผี ไฟกลางคืน บนบานศาลกล่าว ความแค้นของมิติผี
ผีเพื่อน ชิ้นส่วนตั๋ว และคนแปลกหน้าที่มีเรื่องราว
Advanced systems (Normal and Nightmare): locations, omens, counters, lights, vows, grudge, fallen friends, tickets.
"""

import random

from language import get_text
from data import (DIFFICULTIES, LOCATIONS, OMENS, COUNTERS, LIGHTS, VOWS, VOW_DAYS, GHOSTS, MAX_GRUDGE, MERIT_COST,
                  TICKET_PIECES, RAID_START_DAY, tr)
from ui import heading, choose_from_list
import sala
import storage


def setting(key: str):
    """ค่าของระดับความยากที่กำลังเล่น เช่น setting("raid_chance")"""
    return DIFFICULTIES[storage.state["difficulty"]][key]


def advanced() -> bool:
    """กฎ: ระบบเสริมทั้งหมดเปิดเฉพาะระดับปกติขึ้นไป"""
    return setting("advanced")


def cost_label(cost: dict) -> str:
    """ราคา เช่น '🕯 ธูปเทียน 3 + 🍚 อาหาร 2'"""
    return sala.cost_text(cost) if cost else get_text("ฟรี", "free")


# ---------- สถานที่ออกไปหาของ ----------

def location_factor(key: str) -> float:
    """ของที่เหลือในสถานที่นี้: ไปซ้ำครั้งละ -6% (ไม่ต่ำกว่า 40%)"""
    return max(0.4, 1 - 0.06 * storage.state["visits"].get(key, 0))


def gather_at(person: dict, key: str, rng: random.Random, extra: int) -> dict:
    """ของที่หาได้ที่สถานที่นี้ = สุ่ม 0..(ทักษะ + extra) x ตัวคูณของสถานที่ x ของที่เหลือ"""
    place = LOCATIONS[key]
    skill = person["skills"]["scavenge"]
    found = {res: round(rng.randint(0, skill + extra) * mult * location_factor(key)) for res, mult in place["loot"].items()}
    if rng.random() < place["holy_water"]:
        found["holy_water"] = 1
    return found


def injury_at(person: dict, key: str) -> float:
    """โอกาสบาดเจ็บที่สถานที่นี้ (ทักษะหาของสูง = ปลอดภัยกว่า)"""
    return max(0.05, LOCATIONS[key]["injury"] - person["skills"]["scavenge"] * 0.04)


def after_visit(key: str, rng: random.Random, report: list) -> None:
    """หลังไปสถานที่: ของในที่นั้นลดลง อาจเจอชิ้นส่วนตั๋ว และผีแค้นเพิ่ม (ป่าช้า)"""
    state = storage.state
    state["visits"][key] = state["visits"].get(key, 0) + 1
    if rng.random() < LOCATIONS[key]["ticket"]:
        add_ticket(report)
    if LOCATIONS[key]["grudge"]:
        add_grudge(LOCATIONS[key]["grudge"])


def recommend_location() -> str:
    """สถานที่ที่ควรไปตอนนี้ (ไม่แนะนำป่าช้า เพราะเสี่ยงเกินไป ให้ผู้เล่นตัดสินใจเอง)"""
    state = storage.state
    if state["resources"]["holy_water"] == 0 or any(p["possessed"] for p in state["survivors"]):
        return "temple"
    return "market" if sala.days_left("food") <= sala.days_left("water") else "well"


def location_label(key: str) -> str:
    return f"{LOCATIONS[key]['icon']} {tr(LOCATIONS[key]['name'])}"


# ---------- ลางบอกเหตุ ----------

def omen_accuracy() -> float:
    """ความแม่นของลาง = ค่าตามระดับความยาก - 4% ต่อความแค้น 1 (ไม่ต่ำกว่า 30%)"""
    return max(0.3, setting("omen_accuracy") - 0.04 * storage.state["grudge"])


def make_omen(rng: random.Random) -> None:
    """
    สุ่มลางของวันนี้: ผีที่จะนำฝูงคืนนี้จริง (actual) กับลางที่เห็น (shown)
    ลางถูกตามความแม่น ถ้ามีคนถูกผีสิงอยู่ เขาจะกระซิบบอกผีตัวจริง (whisper) ลางจึงแม่นแน่นอน
    """
    state = storage.state
    today = state["day"]
    if not advanced() or today < RAID_START_DAY:
        state["omen"] = None
        return
    kinds = [z["level"] for z in GHOSTS if storage.ghost_day(z["level"]) <= today and z["level"] < 5]
    actual = 5 if today >= storage.goal_day() else rng.choices(kinds, weights=[1 / k for k in kinds])[0]
    whisper = next((p["name"] for p in state["survivors"] if p["possessed"]), None)
    others = [k for k in kinds if k != actual]
    if whisper or actual == 5 or not others or rng.random() < omen_accuracy():
        shown = actual
    else:
        shown = rng.choice(others)
    state["omen"] = {"shown": shown, "actual": actual, "whisper": whisper}


def omen_text() -> str:
    """ข้อความลางของวันนี้ หรือ "" ถ้าไม่มี"""
    omen = storage.state["omen"]
    if not omen:
        return ""
    ghost = GHOSTS[omen["shown"] - 1]
    name = f"{ghost['icon']} {tr(ghost['name'])}"
    if omen["whisper"]:
        return get_text(f"😈 {omen['whisper']} กระซิบด้วยเสียงที่ไม่ใช่ของตัวเอง: \"คืนนี้{tr(ghost['name'])}จะมา\" (แม่นแน่นอน)",
                        f"😈 {omen['whisper']} whispers in a voice not their own: \"{tr(ghost['name'])} comes tonight\" (certain)")
    return get_text(f"🔮 ลาง: {tr(OMENS[omen['shown']])} → คืนนี้ {name} น่าจะนำฝูงมา (แม่นราว {omen_accuracy():.0%})",
                    f"🔮 Omen: {tr(OMENS[omen['shown']])} → {name} may lead tonight (about {omen_accuracy():.0%} sure)")


# ---------- ของแก้ผี ----------

def do_prepare(key: str) -> str:
    """เตรียมของแก้ผีสำหรับคืนนี้ คืนข้อความผิดพลาด หรือ "" หากสำเร็จ"""
    state = storage.state
    if key in state["prepared"]:
        return get_text("เตรียมอันนี้ไว้แล้ว", "Already prepared.")
    error = storage.check_resources(COUNTERS[key]["cost"])
    if error:
        return error
    storage.spend(COUNTERS[key]["cost"])
    state["prepared"].append(key)
    storage.save_game()
    return ""


def counter_for(level: int):
    """ของแก้ที่เตรียมไว้สำหรับผีเลเวลนี้ หรือ None"""
    return next((key for key in storage.state["prepared"] if COUNTERS[key]["ghost"] == level), None)


def ghost_power(level: int) -> int:
    """พลังของผี 1 ตัวคืนนี้ (ถ้าเตรียมของแก้ไว้ พลังลดลงตาม COUNTERS)"""
    key = counter_for(level) if advanced() else None
    if key == "rice":
        return 0
    if key == "thorns":
        return 1
    if key == "offering":
        return GHOSTS[level - 1]["power"] // 2
    if key == "fire":
        return 5
    return GHOSTS[level - 1]["power"]


# ---------- ไฟกลางคืน ----------

def do_set_light(key: str) -> str:
    """เปลี่ยนไฟคืนนี้ (คืนของที่จ่ายไปสำหรับไฟเดิมก่อน) คืนข้อความผิดพลาด หรือ "" หากสำเร็จ"""
    state = storage.state
    old = state["light"]
    if old == key:
        return ""
    for res, amount in LIGHTS[old]["cost"].items():
        state["resources"][res] += amount
    error = storage.check_resources(LIGHTS[key]["cost"])
    if error:
        storage.spend(LIGHTS[old]["cost"])
        return error
    storage.spend(LIGHTS[key]["cost"])
    state["light"] = key
    storage.save_game()
    return ""


def light_defense(value: int) -> int:
    """พลังป้องกันหลังคิดผลของไฟ"""
    light = LIGHTS[storage.state["light"]] if advanced() else LIGHTS["normal"]
    return int(value * light["defense"]) + light["bonus"]


def raid_chance() -> float:
    """โอกาสผีบุกคืนนี้ = ค่าตามระดับความยาก x ผลของไฟ (สูงสุด 95%)"""
    light = LIGHTS[storage.state["light"]] if advanced() else LIGHTS["normal"]
    return min(0.95, setting("raid_chance") * light["raid"])


# ---------- บนบานศาลกล่าว ----------

def do_vow(key: str) -> str:
    """บนบานขอพร (ได้ผลทันที แต่ต้องแก้บนภายใน VOW_DAYS วัน) คืนข้อความผิดพลาด หรือ "" หากสำเร็จ"""
    state = storage.state
    if state["vow"]:
        return get_text("ยังไม่ได้แก้บนครั้งก่อน บนซ้อนไม่ได้", "Repay your last vow first.")
    if key == "calm" and state["day"] >= storage.goal_day():
        return get_text("คืนสุดท้ายเจ้าที่ก็ช่วยไม่ได้", "Not even the spirit can stop the final night.")
    if key == "calm":
        state["calm"] = True
    elif key == "water":
        state["resources"]["holy_water"] += 3
    else:
        state["resources"]["food"] += 4
        state["resources"]["water"] += 4
    state["vow"] = {"wish": key, "due": state["day"] + VOW_DAYS}
    storage.save_game()
    return ""


def do_repay() -> str:
    """แก้บน คืนข้อความผิดพลาด หรือ "" หากสำเร็จ"""
    state = storage.state
    if not state["vow"]:
        return get_text("ไม่ได้บนอะไรไว้", "You have no vow to repay.")
    cost = VOWS[state["vow"]["wish"]]["repay"]
    error = storage.check_resources(cost)
    if error:
        return error
    storage.spend(cost)
    state["vow"] = None
    storage.save_game()
    return ""


def check_vow(rng: random.Random, report: list) -> None:
    """ตอนจบวัน: ถ้าถึงกำหนดแล้วยังไม่แก้บน โดนสาป (ผีแค้น +3 และมีคนถูกผีสิง 1 คน)"""
    state = storage.state
    vow = state["vow"]
    if not vow or state["day"] < vow["due"]:
        return
    state["vow"] = None
    add_grudge(3)
    report.append(get_text("⚡ ไม่ได้แก้บน! เจ้าที่โกรธ ผีแค้นหนักขึ้น", "⚡ You broke your vow! The spirit is furious."))
    healthy = [p for p in state["survivors"] if not p["possessed"]]
    if healthy:
        victim = rng.choice(healthy)
        victim["possessed"] = 1
        state["log"]["possessed"] += 1
        report.append(get_text(f"   😈 {victim['name']} ถูกผีสิงเพราะคำสาป!", f"   😈 {victim['name']} is possessed by the curse!"))


# ---------- ความแค้นและทำบุญ ----------

def add_grudge(amount: int) -> None:
    """เพิ่ม/ลดความแค้นของมิติผี (0 ถึง MAX_GRUDGE)"""
    state = storage.state
    state["grudge"] = max(0, min(MAX_GRUDGE, state["grudge"] + amount))


def do_merit() -> str:
    """ทำบุญอุทิศส่วนกุศล (วันละครั้ง): ความแค้น -2 และส่งผีเพื่อนตนแรกไปสู่สุคติ คืนข้อความผิดพลาด หรือ "" หากสำเร็จ"""
    state = storage.state
    if state["merit_day"] == state["day"]:
        return get_text("วันนี้ทำบุญไปแล้ว", "You already made merit today.")
    error = storage.check_resources(MERIT_COST)
    if error:
        return error
    storage.spend(MERIT_COST)
    add_grudge(-2)
    if state["fallen"]:
        state["fallen"].pop(0)
    state["merit_day"] = state["day"]
    storage.save_game()
    return ""


def add_fallen(name: str) -> None:
    """จำชื่อเพื่อนที่จากไป (ตาย/กลายเป็นผี/ถูกไล่ออก) ไว้ เขาอาจกลับมากับฝูงผี"""
    if advanced():
        storage.state["fallen"].append(name)


def friends_joining(rng: random.Random) -> list:
    """ผีเพื่อนที่มากับฝูงคืนนี้ (แต่ละตนมา 50% สูงสุด 2 ตน)"""
    if not advanced():
        return []
    return [name for name in storage.state["fallen"] if rng.random() < 0.5][:2]


# ---------- ชิ้นส่วนตั๋ว ----------

def add_ticket(report: list) -> None:
    state = storage.state
    if state["tickets"] >= TICKET_PIECES:
        return
    state["tickets"] += 1
    report.append(get_text(f"🎫 พบชิ้นส่วนตั๋วบ้านผีสิง! ({state['tickets']}/{TICKET_PIECES})",
                           f"🎫 A piece of the haunted-house ticket! ({state['tickets']}/{TICKET_PIECES})"))


def escape_ready() -> bool:
    """Collect all ticket pieces to escape before the selected campaign's final night."""
    return advanced() and storage.state["tickets"] >= TICKET_PIECES


# ---------- คนแปลกหน้าที่มีเรื่องราว ----------

def stranger_story(rng: random.Random) -> dict:
    """
    เรื่องของคนแปลกหน้า: disguised = ผีปลอมตัว (ส่องดูเงาแล้วดูปกติ), ticket = พกชิ้นส่วนตั๋วมา
    cold = ตัวเย็นเฉียบ (ผีปลอมตัวเป็นทุกตน แต่คนปกติก็เป็นได้ 20%)
    """
    if not advanced():
        return {"disguised": False, "ticket": False, "cold": False}
    disguised = rng.random() < setting("disguised")
    ticket = not disguised and storage.state["tickets"] < TICKET_PIECES and rng.random() < 0.15
    return {"disguised": disguised, "ticket": ticket, "cold": disguised or rng.random() < 0.2}


def story_lines(stranger: dict) -> list:
    """เบาะแสที่สังเกตเห็นจากคนแปลกหน้า"""
    lines = []
    if stranger.get("cold"):
        lines.append(get_text("🥶 มือเย็นเฉียบผิดปกติ...", "🥶 Their hands are unnaturally cold..."))
    if stranger.get("ticket"):
        lines.append(get_text("🎫 กำเศษกระดาษแปลกๆ ไว้แน่นในมือ", "🎫 They clutch a strange scrap of paper"))
    return lines


# ---------- เมนู Terminal ----------

def tonight_menu() -> None:
    """คืนนี้: ดูลาง เตรียมของแก้ผี และเลือกไฟ"""
    state = storage.state
    heading("เตรียมรับคืนนี้", "PREPARE FOR TONIGHT")
    print(omen_text() or get_text("ยังไม่มีลาง (ผีเริ่มบุกวันที่ 3)", "No omen yet (raids start on day 3)."))
    print(get_text(f"ไฟคืนนี้: {LIGHTS[state['light']]['icon']} {tr(LIGHTS[state['light']]['name'])}",
                   f"Tonight's light: {LIGHTS[state['light']]['icon']} {tr(LIGHTS[state['light']]['name'])}"))
    keys = list(COUNTERS)
    print(get_text("\nของแก้ผี (ใช้ได้คืนเดียว):", "\nCounters (tonight only):"))
    for number, key in enumerate(keys, start=1):
        info = COUNTERS[key]
        ghost = GHOSTS[info["ghost"] - 1]
        done = get_text("  ✔ เตรียมแล้ว", "  ✔ ready") if key in state["prepared"] else ""
        print(f"{number}. {info['icon']} {tr(info['name']):<14} vs {ghost['icon']} {tr(ghost['name']):<14} "
              f"{cost_label(info['cost']):<22} {tr(info['about'])}{done}")
    lights = list(LIGHTS)
    for number, key in enumerate(lights, start=len(keys) + 1):
        info = LIGHTS[key]
        print(f"{number}. {info['icon']} {tr(info['name']):<14} {cost_label(info['cost']):<22} {tr(info['about'])}")
    choice = choose_from_list(keys + lights, "เลือก", "Choose")
    if choice is None:
        return
    if choice in COUNTERS:
        error = do_prepare(choice)
        print(error or get_text(f"เตรียม{tr(COUNTERS[choice]['name'])}แล้ว", f"{tr(COUNTERS[choice]['name'])} ready."))
    else:
        error = do_set_light(choice)
        print(error or get_text(f"คืนนี้: {tr(LIGHTS[choice]['name'])}", f"Tonight: {tr(LIGHTS[choice]['name'])}"))


def shrine_menu() -> None:
    """ศาลเจ้าที่: บนบาน แก้บน และทำบุญ"""
    state = storage.state
    heading("ศาลเจ้าที่", "SPIRIT SHRINE")
    print(get_text(f"ความแค้นของมิติผี: {state['grudge']}/{MAX_GRUDGE}   ผีเพื่อนที่ยังวนเวียน: {', '.join(state['fallen']) or '-'}",
                   f"Realm grudge: {state['grudge']}/{MAX_GRUDGE}   Restless friends: {', '.join(state['fallen']) or '-'}"))
    if state["vow"]:
        vow = VOWS[state["vow"]["wish"]]
        print(get_text(f"บนไว้: {tr(vow['name'])} — แก้บนด้วย {cost_label(vow['repay'])} ภายในวันที่ {state['vow']['due']}",
                       f"Vow: {tr(vow['name'])} — repay {cost_label(vow['repay'])} by day {state['vow']['due']}"))
    options = [("vow", key) for key in VOWS] + [("repay", None), ("merit", None)]
    for number, (kind, key) in enumerate(options, start=1):
        if kind == "vow":
            info = VOWS[key]
            print(get_text(f"{number}. {info['icon']} บน: {tr(info['name'])} ({tr(info['about'])}) → แก้บน {cost_label(info['repay'])} ภายใน {VOW_DAYS} วัน",
                           f"{number}. {info['icon']} Vow: {tr(info['name'])} ({tr(info['about'])}) → repay {cost_label(info['repay'])} within {VOW_DAYS} days"))
        elif kind == "repay":
            print(get_text(f"{number}. 🙏 แก้บน", f"{number}. 🙏 Repay vow"))
        else:
            print(get_text(f"{number}. 🪷 ทำบุญอุทิศส่วนกุศล ({cost_label(MERIT_COST)}): ความแค้น -2 และส่งผีเพื่อน 1 ตนไปสู่สุคติ",
                           f"{number}. 🪷 Make merit ({cost_label(MERIT_COST)}): grudge -2 and lay one friend to rest"))
    choice = choose_from_list(options, "เลือก", "Choose")
    if choice is None:
        return
    kind, key = choice
    if kind == "vow":
        error = do_vow(key)
        print(error or get_text(f"เจ้าที่รับคำขอแล้ว: {tr(VOWS[key]['about'])}", f"The spirit grants it: {tr(VOWS[key]['about'])}"))
    elif kind == "repay":
        print(do_repay() or get_text("แก้บนเรียบร้อย", "Vow repaid."))
    else:
        laid = state["fallen"][0] if state["fallen"] else None
        error = do_merit()
        if error:
            print(error)
        else:
            print(get_text("ทำบุญแล้ว ความแค้นลดลง", "Merit made. The grudge eases."))
            if laid:
                print(get_text(f"🪷 ผีของ{laid}ไปสู่สุคติแล้ว", f"🪷 {laid}'s spirit is at peace."))
