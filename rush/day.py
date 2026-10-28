#!/usr/bin/env python3
"""
Day Module - LAST SHELTER
จบวัน: ผลของงาน → XP/เลเวลอัป → สิ่งก่อสร้างผลิตของ → กินอาหาร/ดื่มน้ำ → เชื้อลุกลาม → เหตุการณ์กลางคืน → ผู้เสียชีวิต → ชนะ/แพ้
และบันทึกศูนย์พักพิง (สถิติ)
End of day: jobs, XP, building output, eating, infection, night events, deaths, win/lose; plus the shelter log.
"""

import random
import time

from language import get_text
from data import (RESOURCES, SKILLS, BUILDINGS, ZOMBIES, POWERS, GOAL_DAY, MAX_CAMP, MAX_HP, STARVE_DAMAGE,
                  REST_HEAL, RAID_START_DAY, WANDERER_CHANCE, WANDERER_INFECTED, WANDERER_NAMES, TURN_DAYS, tr)
from ui import heading, ask_yes_no
import camp
import powers
import storage
import survivors

RAID_CHANCE = 0.55       # โอกาสซอมบี้บุก (ตั้งแต่ RAID_START_DAY, คืนสุดท้ายบุกแน่นอน)
HORDE_GROWTH = 0.5       # จำนวนซอมบี้ในฝูงเพิ่มขึ้นวันละกี่ตัว
SCARCITY_PER_DAY = 0.04  # เมืองถูกค้นจนเกลี้ยง: ของที่หาได้ลดลงวันละ 4%
GATHER_RANGE = 0         # สุ่มของที่หาได้ 0..(ทักษะ + ค่านี้) ต่ออย่าง
RAID_BITES = 3           # ซอมบี้กัดได้สูงสุดกี่คน
BITE_INFECT = 0.4        # โอกาสติดเชื้อเมื่อถูกกัดตอนซอมบี้บุก
SCRATCH_INFECT = 0.3     # โอกาสติดเชื้อเมื่อบาดเจ็บตอนออกไปหาเสบียง
BARRICADE_DEFENSE = 6
LINE_DELAY = 0.25        # หน่วงเวลาระหว่างบรรทัดตอนเล่าเหตุการณ์ (วินาที)


def scarcity() -> float:
    """ตัวคูณของที่หาได้: ลดลงทุกวันเพราะเมืองถูกค้นจนเกลี้ยง (ไม่ต่ำกว่า 0.4)"""
    return max(0.4, 1 - SCARCITY_PER_DAY * (storage.state["day"] - 1))


def gather(person: dict, rng: random.Random) -> dict:
    """เสบียงที่คนนี้หามาได้ = สุ่มตามทักษะหาเสบียง x ความขาดแคลน"""
    skill = person["skills"]["scavenge"]
    factor = scarcity()
    found = {key: round(rng.randint(0, skill + GATHER_RANGE) * factor) for key in ("food", "water", "scrap")}
    # 👃 นักสำรวจ: ได้ของเพิ่มตามเลเวล (สุ่มชนิด)
    for _ in range(powers.scout_bonus(person)):
        found[rng.choice(list(found))] += 1
    return found


def injury_chance(person: dict) -> float:
    """โอกาสบาดเจ็บตอนออกไปหาเสบียง: ทักษะต่ำ = เจ็บง่าย"""
    return 0.40 - person["skills"]["scavenge"] * 0.05


def defense(runners: bool = False) -> int:
    """
    พลังป้องกันคืนนี้ = (ทักษะต่อสู้ x 3 + โบนัสแม่นปืน) ของคนเฝ้ายาม + แนวกั้นเหล็ก
    ถ้ามีซอมบี้วิ่งในฝูง แนวกั้นเหล็กป้องกันได้แค่ครึ่งเดียว
    """
    guards = sum(p["skills"]["guard"] * 3 + powers.guard_bonus(p)
                 for p in storage.state["survivors"] if p["job"] == "guard")
    barricade = BARRICADE_DEFENSE if "barricade" in storage.state["buildings"] else 0
    if runners:
        barricade //= 2
    return guards + barricade


def hurt(person: dict, amount: int) -> None:
    """ลด HP (ไม่ต่ำกว่า 0)"""
    person["hp"] = max(0, person["hp"] - amount)


def infect(person: dict, chance: float, rng: random.Random, report: list) -> None:
    """สุ่มติดเชื้อ (คนที่ติดอยู่แล้วไม่นับซ้ำ, 🧬 ภูมิคุ้มกันช่วยลดโอกาส)"""
    if person["infected"] or rng.random() >= chance * powers.infection_factor(person):
        return
    person["infected"] = 1
    storage.state["log"]["infected"] += 1
    report.append(get_text(f"   🦠 {person['name']} ติดเชื้อ! ต้องได้ยาภายใน {TURN_DAYS} วัน",
                           f"   🦠 {person['name']} is infected! Needs medicine within {TURN_DAYS} days"))


def make_wanderer(rng: random.Random) -> dict:
    """สุ่มคนที่มาขอเข้าศูนย์ (ชื่อไม่ซ้ำ ทักษะรวม 6-8 แต้ม อาจติดเชื้อมาแล้ว)"""
    taken = {p["name"] for p in storage.state["survivors"]}
    names = [n for n in WANDERER_NAMES if n not in taken] or ["???"]
    skills = {s: 1 for s in SKILLS}
    for _ in range(rng.randint(3, 5)):
        skill = rng.choice([s for s in SKILLS if skills[s] < 5])
        skills[skill] += 1
    return {"name": rng.choice(names), "skills": skills, "hp": rng.randint(50, 90),
            "power": rng.choice(list(POWERS)), "level": rng.randint(1, 3),
            "infected": rng.random() < WANDERER_INFECTED, "checked": False}


def resolve_jobs(rng: random.Random, report: list) -> None:
    """ผลของงานแต่ละคน"""
    state = storage.state
    for person in list(state["survivors"]):
        job = person["job"]
        if job == "scavenge":
            found = gather(person, rng)
            for key, amount in found.items():
                storage.gain(key, amount)
            text = ", ".join(f"{RESOURCES[k]['icon']}+{v}" for k, v in found.items() if v)
            report.append(get_text(f"🎒 {person['name']} หาเสบียงได้ {text or 'ไม่ได้อะไรเลย'}",
                                   f"🎒 {person['name']} found {text or 'nothing'}"))
            if rng.random() < injury_chance(person):
                damage = rng.randint(10, 25)
                hurt(person, damage)
                report.append(get_text(f"   🩸 {person['name']} ถูกซอมบี้ข่วนระหว่างทาง (HP -{damage})",
                                       f"   🩸 {person['name']} got scratched by a zombie (HP -{damage})"))
                infect(person, SCRATCH_INFECT, rng, report)
        elif job == "heal" and state["resources"]["medicine"] > 0:
            heal(person, report)
        elif job == "rest":
            person["hp"] = min(MAX_HP, person["hp"] + REST_HEAL)
            report.append(get_text(f"💤 {person['name']} พักผ่อน (HP +{REST_HEAL})",
                                   f"💤 {person['name']} rested (HP +{REST_HEAL})"))
        elif job == "guard":
            report.append(get_text(f"🛡 {person['name']} เฝ้ายามคืนนี้", f"🛡 {person['name']} keeps watch tonight"))
        elif job == "inspect":
            report.append(get_text(f"🔍 {person['name']} ใช้เวลาตรวจคนแปลกหน้าที่ประตู",
                                   f"🔍 {person['name']} spent the day inspecting the newcomer"))


def award_xp(report: list) -> None:
    """ทุกคนที่ทำงานได้ XP 1 ถ้างานตรงกับพลังพิเศษของตัวเองได้ XP 2"""
    for person in storage.state["survivors"]:
        if person["job"] is None:
            continue
        amount = 2 if POWERS[person["power"]]["job"] == person["job"] else 1
        if powers.gain_xp(person, amount):
            report.append(powers.level_up_text(person))


def heal(medic: dict, report: list) -> None:
    """ใช้ยา 1 ชิ้น: รักษาคนติดเชื้อที่ใกล้กลายร่างที่สุดก่อน ถ้าไม่มีใครติดเชื้อ รักษาคนที่ HP ต่ำสุด"""
    state = storage.state
    state["resources"]["medicine"] -= 1
    infected = [p for p in state["survivors"] if p["infected"]]
    if infected:
        patient = max(infected, key=lambda p: p["infected"])
        patient["infected"] = 0
        state["log"]["cured"] += 1
        report.append(get_text(f"✚ {medic['name']} ฉีดยาต้านเชื้อให้ {patient['name']} — หายแล้ว! (ใช้ยา 1)",
                               f"✚ {medic['name']} gave {patient['name']} the antidote — cured! (1 medicine)"))
        return
    patient = min(state["survivors"], key=lambda p: p["hp"])
    amount = 15 + medic["skills"]["heal"] * 8
    patient["hp"] = min(MAX_HP, patient["hp"] + amount)
    report.append(get_text(f"✚ {medic['name']} รักษา {patient['name']} (HP +{amount}, ใช้ยา 1)",
                           f"✚ {medic['name']} healed {patient['name']} (HP +{amount}, 1 medicine)"))


def produce(report: list) -> None:
    """สิ่งก่อสร้างผลิตของ (จำนวนดูจาก camp.DAILY_OUTPUT, ห้องปฐมพยาบาลให้ยาทุก 2 วัน) และนักวิทยาศาสตร์ผลิตยา"""
    state = storage.state
    interval = powers.medicine_interval()
    if interval and state["day"] % interval == 0:
        storage.gain("medicine", 1)
        report.append(get_text("💉 นักวิทยาศาสตร์สังเคราะห์ยาได้ 💊+1", "💉 The scientist synthesized 💊+1"))
    for building in state["buildings"]:
        if building not in camp.DAILY_OUTPUT:
            continue
        resource, amount = camp.DAILY_OUTPUT[building]
        if building == "clinic":
            if state["day"] % 2:
                continue
            amount = 1
        storage.gain(resource, amount)
        report.append(f"{BUILDINGS[building]['icon']} {tr(BUILDINGS[building]['name'])} "
                      f"{RESOURCES[resource]['icon']}+{amount}")


def eat_and_drink(rng: random.Random, report: list) -> None:
    """ทุกคนกินอาหาร 1 และดื่มน้ำ 1 ถ้าไม่พอ คนที่ไม่ได้กิน/ดื่มจะเสีย HP"""
    state = storage.state
    people = state["survivors"]
    used = {}
    for key in ("food", "water"):
        used[key] = min(state["resources"][key], len(people))
        state["resources"][key] -= used[key]
    report.append(get_text(f"🍽 มื้อเย็น: 🥫-{used['food']} 💧-{used['water']}",
                           f"🍽 Dinner: 🥫-{used['food']} 💧-{used['water']}"))

    # กฎ: คนที่ไม่ได้กิน/ดื่ม เสีย HP (สุ่มว่าใครไม่ได้)
    for key, word_th, word_en in (("food", "หิวโหย", "starving"), ("water", "กระหายน้ำ", "thirsty")):
        for person in rng.sample(people, len(people) - used[key]):
            hurt(person, STARVE_DAMAGE)
            report.append(get_text(f"😵 {person['name']} {word_th}! (HP -{STARVE_DAMAGE})",
                                   f"😵 {person['name']} is {word_en}! (HP -{STARVE_DAMAGE})"))


def spread_infection(rng: random.Random, report: list) -> None:
    """
    เชื้อลุกลาม: คนที่ติดเชื้อนับวันเพิ่ม ถ้าเกิน TURN_DAYS จะกลายเป็นซอมบี้
    แล้วทำร้ายคนในศูนย์ 1 คน (คนที่ถูกทำร้ายอาจติดเชื้อต่อ)
    """
    state = storage.state
    for person in list(state["survivors"]):
        if not person["infected"]:
            continue
        person["infected"] += 1
        if person["infected"] <= TURN_DAYS:
            report.append(get_text(f"🦠 {person['name']} ตัวร้อนจัด ตาเริ่มขุ่น... (กลายร่างพรุ่งนี้ถ้าไม่ได้ยา)",
                                   f"🦠 {person['name']} burns with fever, eyes clouding... (turns tomorrow without medicine)"))
            continue

        # กลายเป็นซอมบี้
        state["survivors"].remove(person)
        state["log"]["turned"] += 1
        state["log"]["deaths"] += 1
        report.append(get_text(f"🧟 {person['name']} กลายเป็นซอมบี้!!", f"🧟 {person['name']} has turned!!"))
        if state["survivors"]:
            victim = rng.choice(state["survivors"])
            damage = rng.randint(20, 35)
            hurt(victim, damage)
            report.append(get_text(f"   🩸 {victim['name']} ถูกทำร้ายก่อนจะจัดการได้ (HP -{damage})",
                                   f"   🩸 {victim['name']} was attacked before it was stopped (HP -{damage})"))
            infect(victim, 0.5, rng, report)


def make_horde(rng: random.Random) -> list:
    """
    สุ่มฝูงซอมบี้ของคืนนี้ คืนค่า list ของเลเวลซอมบี้แต่ละตัว
    จำนวน = 3 + (วัน x HORDE_GROWTH) + สุ่ม 0-2 ตัว, ชนิดที่สุ่มได้ = ชนิดที่ถึงวันโผล่แล้ว (เลเวลสูงโผล่น้อยกว่า)
    คืนสุดท้ายมีราชาซอมบี้มาด้วยเสมอ
    """
    day = storage.state["day"]
    kinds = [z for z in ZOMBIES if z["from_day"] <= day and z["level"] < 5]
    weights = [1 / z["level"] for z in kinds]
    count = 3 + round(day * HORDE_GROWTH) + rng.randint(0, 2)
    horde = [z["level"] for z in rng.choices(kinds, weights=weights, k=count)]
    if day >= GOAL_DAY:
        horde.append(5)
    return sorted(horde)


def horde_power(horde: list) -> int:
    """พลังรวมของฝูง = ผลรวมพลังของซอมบี้ทุกตัว"""
    return sum(ZOMBIES[level - 1]["power"] for level in horde)


def horde_text(horde: list) -> str:
    """องค์ประกอบของฝูง เช่น '🧟x5 🏃x2 💪x1'"""
    return " ".join(f"{ZOMBIES[level - 1]['icon']}x{horde.count(level)}" for level in sorted(set(horde)))


def night_event(rng: random.Random, report: list) -> str:
    """เหตุการณ์กลางคืน 1 อย่าง คืนค่าชื่อเหตุการณ์"""
    state = storage.state
    people = state["survivors"]
    roll = rng.random()
    if not people:
        return "none"

    final_night = state["day"] >= GOAL_DAY
    if final_night or (state["day"] >= RAID_START_DAY and roll < RAID_CHANCE):
        horde = make_horde(rng)
        power = horde_power(horde)
        guard = defense(runners=2 in horde)
        state["log"]["raids"] += 1
        state["log"]["biggest_horde"] = max(state["log"]["biggest_horde"], power)
        if final_night:
            report.append(get_text("👹 คืนสุดท้าย... ราชาซอมบี้นำฝูงมาเอง!", "👹 The final night... The Zombie King leads the horde!"))
        report.append(get_text(f"🧟 ฝูงซอมบี้บุก! {horde_text(horde)} = พลัง {power} vs พลังป้องกัน {guard}",
                               f"🧟 Horde attack! {horde_text(horde)} = power {power} vs defense {guard}"))
        if 2 in horde and "barricade" in state["buildings"]:
            report.append(get_text("   🏃 ซอมบี้วิ่งปีนข้ามแนวกั้นได้ (แนวกั้นป้องกันได้ครึ่งเดียว)",
                                   "   🏃 Runners climb the barricade (it only stops half as well)"))
        smashed = min(state["resources"]["scrap"], horde.count(3) * 2)
        if smashed:
            state["resources"]["scrap"] -= smashed
            report.append(get_text(f"   💪 ซอมบี้ยักษ์ทุบข้าวของ 🔩-{smashed}", f"   💪 Brutes smash your stuff 🔩-{smashed}"))
        if guard >= power:
            state["log"]["repelled"] += 1
            report.append(get_text("   ✔ ต้านไว้ได้! ฝูงซอมบี้ถอยกลับไป", "   ✔ You held the line! The horde retreats."))
        else:
            bite = BITE_INFECT * (2 if 4 in horde else 1)
            lost = min(state["resources"]["food"], (power - guard) // 2 + 1)
            state["resources"]["food"] -= lost
            report.append(get_text(f"   ✖ ซอมบี้ทะลวงเข้ามา! เสบียงเสียหาย 🥫-{lost}",
                                   f"   ✖ They broke through! Supplies ruined 🥫-{lost}"))
            for person in rng.sample(people, min(len(people), rng.randint(1, RAID_BITES))):
                damage = rng.randint(15, 30)
                hurt(person, damage)
                report.append(get_text(f"   🩸 {person['name']} ถูกกัด (HP -{damage})", f"   🩸 {person['name']} was bitten (HP -{damage})"))
                infect(person, bite, rng, report)
        return "raid"
    if roll < 0.60:
        scrap = min(2, state["resources"]["scrap"])
        state["resources"]["scrap"] -= scrap
        storage.gain("water", 3)
        report.append(get_text(f"⛈ ฝนตกหนัก! หลังคารั่ว เศษวัสดุพัง 🔩-{scrap} แต่รองน้ำฝนได้ 💧+3",
                               f"⛈ Heavy rain! The roof leaks, ruining 🔩-{scrap}, but you collect 💧+3"))
        return "rain"
    if roll < 0.70:
        person = rng.choice(people)
        hurt(person, 20)
        report.append(get_text(f"🤒 {person['name']} มีไข้สูงกลางดึก (HP -20)", f"🤒 {person['name']} ran a high fever (HP -20)"))
        return "sick"
    if roll < 0.82:
        storage.gain("medicine", 1)
        storage.gain("food", 2)
        report.append(get_text("🚁 มีเสบียงทิ้งลงมาจากฟ้า! 💊+1 🥫+2", "🚁 A supply drop from the sky! 💊+1 🥫+2"))
        return "drop"
    report.append(get_text("🌙 คืนนี้เงียบ... ได้ยินแต่เสียงครางไกลๆ", "🌙 A quiet night... only distant groans."))
    return "quiet"


def rescued() -> list:
    """คนที่ได้ขึ้นเฮลิคอปเตอร์ (กฎ: คนที่ติดเชื้อห้ามขึ้น)"""
    return [p for p in storage.state["survivors"] if not p["infected"]]


def ending_grade(alive: int) -> tuple:
    """ผลลัพธ์ตอนจบตามจำนวนคนที่ได้รับการช่วยเหลือ คืนค่า (จำนวนดาว 0-3, ชื่อฉายา)"""
    if alive >= 5:
        return 3, get_text("ผู้นำในตำนาน", "Legendary Leader")
    if alive >= 3:
        return 2, get_text("ศูนย์พักพิงแข็งแกร่ง", "Unbreakable Shelter")
    if alive >= 1:
        return 1, get_text("รอดแบบหวุดหวิด", "Barely Made It")
    return 0, get_text("ศูนย์พักพิงล่มสลาย", "The Shelter Has Fallen")


def do_end_day(rng: random.Random = None) -> dict:
    """
    จบวันและคำนวณผลทั้งหมด (ใช้ร่วมกันทั้ง Terminal และ GUI)
    คืนค่า {"lines": [ข้อความเล่าเหตุการณ์], "event": เหตุการณ์กลางคืน, "dead": [ชื่อคนที่เสียชีวิต], "status": ...}
    """
    rng = rng or random.Random()
    state = storage.state
    report = []

    resolve_jobs(rng, report)
    award_xp(report)
    produce(report)
    eat_and_drink(rng, report)
    spread_infection(rng, report)
    event = night_event(rng, report)

    # ผู้ที่ HP หมดเสียชีวิต
    dead = [p["name"] for p in state["survivors"] if p["hp"] <= 0]
    state["survivors"] = [p for p in state["survivors"] if p["hp"] > 0]
    state["log"]["deaths"] += len(dead)
    for name in dead:
        report.append(get_text(f"🪦 {name} จากไปแล้ว...", f"🪦 {name} did not survive..."))

    state["log"]["days"].append({"day": state["day"], "food": state["resources"]["food"],
                                 "water": state["resources"]["water"], "people": len(state["survivors"]),
                                 "event": event})

    # ตรวจชนะ/แพ้ แล้วเริ่มวันใหม่
    if not state["survivors"]:
        state["status"] = "lost"
    elif state["day"] >= GOAL_DAY:
        state["status"] = "won"
    else:
        state["day"] += 1
        for person in state["survivors"]:
            person["job"] = None
        state["wanderer"] = None
        if len(state["survivors"]) < MAX_CAMP and rng.random() < WANDERER_CHANCE:
            state["wanderer"] = make_wanderer(rng)

    # เกมจบ: จดผลลงประวัติ
    if state["status"] != "playing":
        saved = len(rescued()) if state["status"] == "won" else 0
        storage.record_result(ending_grade(saved)[0], saved)

    storage.save_game()
    return {"lines": report, "event": event, "dead": dead, "status": state["status"]}


# ---------- เมนู Terminal ----------

def end_day() -> None:
    """จบวัน: ยืนยัน แล้วเล่าเหตุการณ์ทีละบรรทัด"""
    state = storage.state
    heading(f"จบวันที่ {state['day']}", f"END OF DAY {state['day']}")
    idle = [p["name"] for p in state["survivors"] if p["job"] is None]
    if idle and not ask_yes_no(f"ยังมีคนไม่มีงาน ({', '.join(idle)}) จบวันเลย?",
                               f"Some survivors have no job ({', '.join(idle)}). End the day anyway?"):
        print(get_text("ยังไม่จบวัน", "Not yet."))
        return

    result = do_end_day()
    print()
    for line in result["lines"]:
        print(line)
        time.sleep(LINE_DELAY)

    if result["status"] == "won":
        saved = rescued()
        left_behind = len(state["survivors"]) - len(saved)
        stars, title = ending_grade(len(saved))
        print(get_text(f"\n🚁 เสียงใบพัดเฮลิคอปเตอร์! ทีมช่วยเหลือมาถึงแล้ว พาผู้รอดชีวิตออกไปได้ {len(saved)} คน",
                       f"\n🚁 Rotor blades overhead! Rescue has arrived and takes {len(saved)} survivor(s) to safety"))
        if left_behind:
            print(get_text(f"   (คนติดเชื้อ {left_behind} คนไม่ได้รับอนุญาตให้ขึ้นเครื่อง...)",
                           f"   ({left_behind} infected survivor(s) were not allowed on board...)"))
        print(f"   {'⭐' * stars}  {title}")
    elif result["status"] == "lost":
        print(get_text("\n☠ ศูนย์พักพิงเงียบงัน... ไม่มีใครรอดชีวิต", "\n☠ The shelter falls silent... No one survived."))
    else:
        print(get_text(f"\n🌅 เช้าวันที่ {state['day']}/{GOAL_DAY}", f"\n🌅 Morning of day {state['day']}/{GOAL_DAY}"))
        infected = [p["name"] for p in state["survivors"] if p["infected"]]
        if infected:
            print(get_text(f"🦠 ติดเชื้ออยู่: {', '.join(infected)} — มอบงานรักษาด่วน!",
                           f"🦠 Infected: {', '.join(infected)} — assign a medic now!"))
        if state["wanderer"]:
            print(get_text(f"🚶 มีคนมาขอเข้าศูนย์ที่ประตู: {state['wanderer']['name']}",
                           f"🚶 Someone is at the gate: {state['wanderer']['name']}"))


def camp_stats() -> dict:
    """
    คำนวณสถิติศูนย์พักพิง (ใช้ร่วมกันทั้ง Terminal และ GUI):
    ของที่หามาได้ทั้งหมด อัตราป้องกันการบุก อัตรารักษาการติดเชื้อ คนที่เก่งแต่ละด้าน และอาหาร/น้ำต่ำสุดที่เคยเหลือ
    """
    log = storage.state["log"]
    people = storage.state["survivors"]
    best = {}
    for skill in SKILLS:
        if people:
            best[skill] = max(people, key=lambda p: p["skills"][skill])
    days = log["days"]
    return {
        "gathered": sum(log["gathered"].values()),
        "defense_rate": log["repelled"] / log["raids"] * 100 if log["raids"] else 0,
        "cure_rate": log["cured"] / log["infected"] * 100 if log["infected"] else 0,
        "best": best,
        "top_level": max(people, key=lambda p: (p["level"], p["xp"])) if people else None,
        "lowest_food": min((d["food"] for d in days), default=storage.state["resources"]["food"]),
        "lowest_water": min((d["water"] for d in days), default=storage.state["resources"]["water"]),
    }


def camp_log() -> None:
    """บันทึกศูนย์พักพิง: สถิติและกราฟอาหารรายวัน"""
    state = storage.state
    log = state["log"]
    stats = camp_stats()
    heading("บันทึกศูนย์พักพิง", "SHELTER LOG")
    survived = min(state["day"] - (0 if state["status"] != "playing" else 1), GOAL_DAY)
    print(get_text(f"รอดมาแล้ว {survived}/{GOAL_DAY} วัน   ", f"Survived {survived}/{GOAL_DAY} days   ")
          + "■" * survived + "□" * (GOAL_DAY - survived))
    print(get_text(f"ผู้รอดชีวิต {len(state['survivors'])} คน   เข้าร่วมใหม่ {log['joined']}   เสียชีวิต {log['deaths']}",
                   f"Survivors {len(state['survivors'])}   joined {log['joined']}   died {log['deaths']}"))
    print(get_text(f"ซอมบี้บุก {log['raids']} ครั้ง   ต้านไว้ได้ {log['repelled']} ({stats['defense_rate']:.0f}%)",
                   f"Raids {log['raids']}   repelled {log['repelled']} ({stats['defense_rate']:.0f}%)"))
    print(get_text(f"ติดเชื้อ {log['infected']} ครั้ง   รักษาหาย {log['cured']} ({stats['cure_rate']:.0f}%)   กลายเป็นซอมบี้ {log['turned']}",
                   f"Infections {log['infected']}   cured {log['cured']} ({stats['cure_rate']:.0f}%)   turned {log['turned']}"))
    print(get_text(f"ฝูงใหญ่ที่สุดที่เจอ: พลัง {log['biggest_horde']}   เลเวลอัปทั้งหมด {log['level_ups']} ครั้ง",
                   f"Biggest horde faced: power {log['biggest_horde']}   total level-ups {log['level_ups']}"))
    gathered = "  ".join(f"{RESOURCES[k]['icon']}{v}" for k, v in log["gathered"].items())
    print(get_text(f"หาเสบียงได้ทั้งหมด {stats['gathered']} ชิ้น   ({gathered})", f"Total gathered {stats['gathered']}   ({gathered})"))
    print(get_text(f"อาหารเหลือน้อยสุด {stats['lowest_food']}   น้ำเหลือน้อยสุด {stats['lowest_water']}",
                   f"Lowest food {stats['lowest_food']}   lowest water {stats['lowest_water']}"))

    if stats["best"]:
        print(get_text("\nเก่งที่สุดในศูนย์:", "\nBest in the shelter:"))
        for skill, person in stats["best"].items():
            print(f"  {tr(SKILLS[skill]):<10} {person['name']:<10} {survivors.stars(person['skills'][skill])}")
        top = stats["top_level"]
        print(get_text(f"  พลังสูงสุด  {top['name']:<10} {powers.power_label(top)}",
                       f"  Top power  {top['name']:<10} {powers.power_label(top)}"))

    if log["days"]:
        print(get_text("\nอาหารคงเหลือตอนจบแต่ละวัน:", "\nFood left at the end of each day:"))
        for entry in log["days"][-8:]:
            print(f"  {get_text('วัน', 'Day')} {entry['day']:>2}  {'█' * min(entry['food'], 30):<30} {entry['food']}")
    print(get_text(f"\nคาดการณ์ตอนนี้: อาหาร{camp.days_text('food')}  น้ำ{camp.days_text('water')}",
                   f"\nForecast now: food {camp.days_text('food')}, water {camp.days_text('water')}"))
