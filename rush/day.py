#!/usr/bin/env python3
"""
Day Module - GHOST REALM (หลุดมิติผี)
จบวัน: ผลของงาน → สิ่งก่อสร้างผลิตของ → กินอาหาร/ดื่มน้ำ → ผีสิงลุกลาม → เหตุการณ์กลางคืน → ผู้เสียชีวิต → ชนะ/แพ้
และบันทึกศาลา (สถิติ)
End of day: jobs, building output, eating, infection, night events, deaths, win/lose; plus the shelter log.
ระบบเสริมของระดับปกติขึ้นไป (สถานที่ ลาง ของแก้ผี ไฟ บนบาน ผีเพื่อน ตั๋ว) อยู่ใน realm.py
"""

import random
import time

from language import get_text
from data import (RESOURCES, SKILLS, BUILDINGS, ZOMBIES, LOOKS, LOCATIONS, COUNTERS, FRIEND_GHOST_POWER,
                  TICKET_PIECES, MAX_CAMP, MAX_HP, STARVE_DAMAGE,
                  REST_HEAL, RAID_START_DAY, WANDERER_CHANCE, WANDERER_INFECTED, WANDERER_NAMES, TURN_DAYS, tr)
from ui import heading, ask_yes_no
import camp
import realm
import storage
import survivors

# โอกาสผีบุก จำนวนผีที่เพิ่มต่อวัน และโอกาสถูกสิงเมื่อถูกทำร้าย อยู่ใน data.DIFFICULTIES (ต่างกันตามระดับความยาก)
SCARCITY_PER_DAY = 0.03  # Loss per base-timeline day; stretched over the selected campaign.
GATHER_RANGE = 1         # สุ่มของที่หาได้ 0..(ทักษะ + ค่านี้) ต่ออย่าง
RAID_BITES = 3           # ผีทำร้ายได้สูงสุดกี่คน
SCRATCH_INFECT = 0.3     # โอกาสถูกผีสิงเมื่อบาดเจ็บตอนออกไปหาของ
BARRICADE_DEFENSE = 6
GUARD_POWER = 5          # พลังป้องกันต่อทักษะปราบผี 1 ระดับของคนเฝ้ายาม
LINE_DELAY = 0.25        # หน่วงเวลาระหว่างบรรทัดตอนเล่าเหตุการณ์ (วินาที)


def scarcity() -> float:
    """ตัวคูณของที่หาได้: ลดลงทุกวันเพราะของถูกเก็บจนเกลี้ยง (ไม่ต่ำกว่า 0.4)"""
    return max(0.4, 1 - SCARCITY_PER_DAY * (storage.pressure_day() - 1))


def gather(person: dict, rng: random.Random) -> dict:
    """ของที่คนนี้หามาได้ = สุ่มตามทักษะหาของ x ความขาดแคลน"""
    skill = person["skills"]["scavenge"]
    factor = scarcity()
    return {key: round(rng.randint(0, skill + GATHER_RANGE) * factor) for key in ("food", "water", "scrap")}


def injury_chance(person: dict) -> float:
    """โอกาสบาดเจ็บตอนออกไปหาของ: ทักษะต่ำ = เจ็บง่าย"""
    return 0.40 - person["skills"]["scavenge"] * 0.05


def defense(runners: bool = False) -> int:
    """
    พลังป้องกันคืนนี้ = (ทักษะปราบผี x GUARD_POWER ของคนเฝ้ายาม + สายสิญจน์) แล้วคิดผลของไฟ
    ถ้ามีกระสือในฝูง (และไม่ได้เตรียมหนามไผ่) สายสิญจน์ป้องกันได้แค่ครึ่งเดียว
    """
    guards = sum(p["skills"]["guard"] * GUARD_POWER for p in storage.state["survivors"] if p["job"] == "guard")
    barricade = BARRICADE_DEFENSE if "barricade" in storage.state["buildings"] else 0
    if runners:
        barricade //= 2
    return realm.light_defense(guards + barricade)


def hurt(person: dict, amount: int) -> None:
    """ลด HP (ไม่ต่ำกว่า 0)"""
    person["hp"] = max(0, person["hp"] - amount)


def infect(person: dict, chance: float, rng: random.Random, report: list) -> None:
    """สุ่มถูกผีสิง (คนที่ถูกสิงอยู่แล้วไม่นับซ้ำ)"""
    if person["infected"] or rng.random() >= chance:
        return
    person["infected"] = 1
    storage.state["log"]["infected"] += 1
    report.append(get_text(f"   😈 {person['name']} ถูกผีสิง! ต้องได้น้ำมนต์ภายใน {TURN_DAYS} วัน",
                           f"   😈 {person['name']} is possessed! Needs holy water within {TURN_DAYS} days"))


def make_wanderer(rng: random.Random) -> dict:
    """สุ่มคนที่มาขอเข้าศาลา (ชื่อไม่ซ้ำ ทักษะรวม 6-8 แต้ม อาจถูกผีสิงมาแล้ว)"""
    taken = {p["name"] for p in storage.state["survivors"]}
    names = [n for n in WANDERER_NAMES if n not in taken] or ["???"]
    skills = {s: 1 for s in SKILLS}
    for _ in range(rng.randint(3, 5)):
        skill = rng.choice([s for s in SKILLS if skills[s] < 5])
        skills[skill] += 1
    story = realm.wanderer_story(rng)
    return {"name": rng.choice(names), "skills": skills, "hp": rng.randint(50, 90), "look": rng.choice(LOOKS),
            "infected": not story["disguised"] and rng.random() < WANDERER_INFECTED, "checked": False, **story}


def resolve_jobs(rng: random.Random, report: list) -> None:
    """ผลของงานแต่ละคน"""
    state = storage.state
    for person in list(state["survivors"]):
        job = person["job"]
        if job == "scavenge":
            # ระดับปกติขึ้นไป: ของที่ได้และความเสี่ยงขึ้นกับสถานที่ที่เลือก
            place = person.get("target") if realm.advanced() else None
            found = realm.gather_at(person, place, rng, GATHER_RANGE) if place else gather(person, rng)
            for key, amount in found.items():
                storage.gain(key, amount)
            text = ", ".join(f"{RESOURCES[k]['icon']}+{v}" for k, v in found.items() if v)
            where = f" ({tr(LOCATIONS[place]['name'])})" if place else ""
            report.append(get_text(f"🎒 {person['name']} หาของได้ {text or 'ไม่ได้อะไรเลย'}{where}",
                                   f"🎒 {person['name']} found {text or 'nothing'}{where}"))
            if place:
                realm.after_visit(place, rng, report)
            if rng.random() < (realm.injury_at(person, place) if place else injury_chance(person)):
                damage = rng.randint(10, 25)
                hurt(person, damage)
                report.append(get_text(f"   🩸 {person['name']} ถูกผีจู่โจมระหว่างทาง (HP -{damage})",
                                       f"   🩸 {person['name']} was attacked by a ghost on the way (HP -{damage})"))
                infect(person, LOCATIONS[place]["infect"] if place else SCRATCH_INFECT, rng, report)
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


def heal(medic: dict, report: list) -> None:
    """ใช้น้ำมนต์ 1: ไล่ผีออกจากคนที่ใกล้กลายเป็นผีที่สุดก่อน ถ้าไม่มีใครถูกผีสิง รักษาคนที่ HP ต่ำสุด"""
    state = storage.state
    state["resources"]["medicine"] -= 1
    infected = [p for p in state["survivors"] if p["infected"]]
    if infected:
        patient = max(infected, key=lambda p: p["infected"])
        patient["infected"] = 0
        state["log"]["cured"] += 1
        report.append(get_text(f"✚ {medic['name']} ประพรมน้ำมนต์ไล่ผีออกจากร่าง {patient['name']} — หายแล้ว! (ใช้น้ำมนต์ 1)",
                               f"✚ {medic['name']} drove the ghost out of {patient['name']} — freed! (1 holy water)"))
        return
    patient = min(state["survivors"], key=lambda p: p["hp"])
    amount = 15 + medic["skills"]["heal"] * 8
    patient["hp"] = min(MAX_HP, patient["hp"] + amount)
    report.append(get_text(f"✚ {medic['name']} รักษา {patient['name']} (HP +{amount}, ใช้น้ำมนต์ 1)",
                           f"✚ {medic['name']} healed {patient['name']} (HP +{amount}, 1 holy water)"))


def produce(report: list) -> None:
    """สิ่งก่อสร้างผลิตของ (จำนวนดูจาก camp.DAILY_OUTPUT, ศาลพระภูมิให้น้ำมนต์ทุก 2 วัน)"""
    state = storage.state
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
    report.append(get_text(f"🍽 มื้อเย็น: 🍚-{used['food']} 💧-{used['water']}",
                           f"🍽 Dinner: 🍚-{used['food']} 💧-{used['water']}"))

    # กฎ: คนที่ไม่ได้กิน/ดื่ม เสีย HP (สุ่มว่าใครไม่ได้)
    for key, word_th, word_en in (("food", "หิวโหย", "starving"), ("water", "กระหายน้ำ", "thirsty")):
        for person in rng.sample(people, len(people) - used[key]):
            hurt(person, STARVE_DAMAGE)
            report.append(get_text(f"😵 {person['name']} {word_th}! (HP -{STARVE_DAMAGE})",
                                   f"😵 {person['name']} is {word_en}! (HP -{STARVE_DAMAGE})"))


def spread_infection(rng: random.Random, report: list) -> None:
    """
    ผีสิงลุกลาม: คนที่ถูกผีสิงนับวันเพิ่ม ถ้าเกิน TURN_DAYS จะกลายเป็นผี
    แล้วทำร้ายคนในศาลา 1 คน (คนที่ถูกทำร้ายอาจถูกผีสิงต่อ)
    """
    state = storage.state
    for person in list(state["survivors"]):
        if not person["infected"]:
            continue
        person["infected"] += 1
        if person["infected"] <= TURN_DAYS:
            report.append(get_text(f"😈 {person['name']} ตัวเย็นเฉียบ พูดจาแปลกๆ... (กลายเป็นผีพรุ่งนี้ถ้าไม่ได้น้ำมนต์)",
                                   f"😈 {person['name']} is ice cold, whispering strangely... (becomes a ghost tomorrow without holy water)"))
            continue

        # กลายเป็นผี
        state["survivors"].remove(person)
        state["log"]["turned"] += 1
        state["log"]["deaths"] += 1
        realm.add_fallen(person["name"])
        report.append(get_text(f"💀 {person['name']} กลายเป็นผีไปแล้ว!!", f"💀 {person['name']} has become a ghost!!"))
        if state["survivors"]:
            victim = rng.choice(state["survivors"])
            damage = rng.randint(20, 35)
            hurt(victim, damage)
            report.append(get_text(f"   🩸 {victim['name']} ถูกทำร้ายก่อนจะไล่ผีออกไปได้ (HP -{damage})",
                                   f"   🩸 {victim['name']} was attacked before the ghost was driven off (HP -{damage})"))
            infect(victim, 0.5, rng, report)


def reveal_disguised(rng: random.Random, report: list) -> None:
    """ผีปลอมตัวที่รับเข้ามา: ครบ 2 คืนจะเผยร่าง ทำร้ายคนในศาลา 2 คน แล้วหายไป (ผีแค้นเพิ่ม)"""
    state = storage.state
    for person in list(state["survivors"]):
        if not person.get("disguised"):
            continue
        person["disguised"] -= 1
        if person["disguised"] > 0:
            continue
        state["survivors"].remove(person)
        realm.add_grudge(1)
        report.append(get_text(f"🎭 {person['name']} เผยร่างจริง... เป็นผีปลอมตัวมาตลอด!",
                               f"🎭 {person['name']} shows their true face... a ghost all along!"))
        for victim in rng.sample(state["survivors"], min(2, len(state["survivors"]))):
            damage = rng.randint(20, 35)
            hurt(victim, damage)
            report.append(get_text(f"   🩸 {victim['name']} ถูกทำร้าย (HP -{damage})",
                                   f"   🩸 {victim['name']} was attacked (HP -{damage})"))


def make_horde(rng: random.Random) -> list:
    """
    สุ่มฝูงผีของคืนนี้ คืนค่า list ของเลเวลผีแต่ละตัว
    จำนวน = 3 + (วันตามสัดส่วนแคมเปญ x horde_growth) + สุ่ม 0-2 ตัว, เลเวลสูงโผล่น้อยกว่า
    ระดับปกติขึ้นไป: ผีตัวจริงตามลางมาเพิ่ม 2 ตัว และความแค้นทุก 2 แต้มเพิ่มผีอีก 1 ตัว
    คืนสุดท้ายมีเสือสมิงมาด้วยเสมอ
    """
    state = storage.state
    day = state["day"]
    kinds = [z for z in ZOMBIES if storage.ghost_day(z["level"]) <= day and z["level"] < 5]
    weights = [1 / z["level"] for z in kinds]
    count = 3 + round(storage.pressure_day() * realm.setting("horde_growth")) + rng.randint(0, 2) + state["grudge"] // 2
    horde = [z["level"] for z in rng.choices(kinds, weights=weights, k=count)]
    if state["omen"] and state["omen"]["actual"] < 5:
        horde += [state["omen"]["actual"]] * 2
    if day >= storage.goal_day():
        horde.append(5)
    return sorted(horde)


def horde_power(horde: list) -> int:
    """พลังรวมของฝูง = ผลรวมพลังของผีทุกตัว (คิดของแก้ผีที่เตรียมไว้แล้ว)"""
    return sum(realm.ghost_power(level) for level in horde)


def expected_horde_power() -> int:
    """
    พลังฝูงผีโดยเฉลี่ยถ้าคืนนี้ถูกบุก (GUI ใช้เทียบกับพลังป้องกัน) คืนค่า 0 ถ้ายังไม่ถึงวันที่ผีเริ่มบุก
    = พลังเฉลี่ยต่อตัวตามน้ำหนักที่ใช้สุ่ม x จำนวนตัวเฉลี่ย (+ เสือสมิงในคืนสุดท้าย)
    """
    today = storage.state["day"]
    if today < RAID_START_DAY:
        return 0
    kinds = [z for z in ZOMBIES if storage.ghost_day(z["level"]) <= today and z["level"] < 5]
    weights = [1 / z["level"] for z in kinds]
    average = sum(w * z["power"] for w, z in zip(weights, kinds)) / sum(weights)
    count = 3 + round(storage.pressure_day() * realm.setting("horde_growth")) + 1 + storage.state["grudge"] // 2
    boss = realm.ghost_power(5) if today >= storage.goal_day() else 0
    omen = storage.state["omen"]
    featured = realm.ghost_power(omen["actual"]) * 2 if omen and omen["actual"] < 5 else 0
    return round(average * count) + boss + featured


def horde_text(horde: list) -> str:
    """องค์ประกอบของฝูง เช่น '👻x5 🔥x2 🦴x1'"""
    return " ".join(f"{ZOMBIES[level - 1]['icon']}x{horde.count(level)}" for level in sorted(set(horde)))


def night_event(rng: random.Random, report: list) -> str:
    """เหตุการณ์กลางคืน 1 อย่าง คืนค่าชื่อเหตุการณ์"""
    state = storage.state
    people = state["survivors"]
    roll = rng.random()
    if not people:
        return "none"

    final_night = state["day"] >= storage.goal_day()
    calm = state["calm"] and not final_night
    if calm:
        report.append(get_text("🌙 เจ้าที่คุ้มครอง... คืนนี้ไม่มีผีกล้าเข้าใกล้", "🌙 The spirit keeps watch... no ghost dares come near."))
    if final_night or (not calm and state["day"] >= RAID_START_DAY and roll < realm.raid_chance()):
        horde = make_horde(rng)
        friends = realm.friends_joining(rng)
        power = horde_power(horde) + FRIEND_GHOST_POWER * len(friends)
        runners = 2 in horde and not realm.counter_for(2)
        guard = defense(runners=runners)
        state["log"]["raids"] += 1
        state["log"]["biggest_horde"] = max(state["log"]["biggest_horde"], power)
        if final_night:
            report.append(get_text("🐯 คืนสุดท้าย... เสือสมิงนำฝูงผีมาเอง!", "🐯 The final night... The Saming Tiger leads the horde!"))
        report.append(get_text(f"👻 ฝูงผีบุก! {horde_text(horde)} = พลัง {power} vs พลังป้องกัน {guard}",
                               f"👻 Ghost raid! {horde_text(horde)} = power {power} vs defense {guard}"))
        for name in friends:
            report.append(get_text(f"   👤 ผีของ{name}มากับฝูงด้วย... \"ให้ฉันเข้าไปหน่อย\" (พลัง +{FRIEND_GHOST_POWER})",
                                   f"   👤 {name}'s ghost walks with them... \"let me in\" (power +{FRIEND_GHOST_POWER})"))
        for level in sorted(set(horde)):
            key = realm.counter_for(level)
            if key:
                report.append(get_text(f"   {COUNTERS[key]['icon']} {tr(COUNTERS[key]['name'])}ได้ผล! {tr(COUNTERS[key]['about'])}",
                                       f"   {COUNTERS[key]['icon']} {tr(COUNTERS[key]['name'])} works! {tr(COUNTERS[key]['about'])}"))
        if runners and "barricade" in state["buildings"]:
            report.append(get_text("   🔥 กระสือลอยข้ามสายสิญจน์ได้ (สายสิญจน์กันได้ครึ่งเดียว)",
                                   "   🔥 Krasue float over the sacred thread (it only stops half as well)"))
        smashed = 0 if realm.counter_for(3) else min(state["resources"]["scrap"], horde.count(3) * 2)
        if smashed:
            state["resources"]["scrap"] -= smashed
            report.append(get_text(f"   🦴 เปรตกินของเซ่นไหว้ 🕯-{smashed}", f"   🦴 Pretas devour your offerings 🕯-{smashed}"))
        if guard >= power:
            state["log"]["repelled"] += 1
            report.append(get_text("   ✔ ต้านไว้ได้! ฝูงผีถอยกลับไป", "   ✔ You held the line! The ghosts retreat."))
        else:
            bite = realm.setting("bite_infect") * (2 if 4 in horde and not realm.counter_for(4) else 1)
            lost = min(state["resources"]["food"], (power - guard) // 2 + 1)
            state["resources"]["food"] -= lost
            report.append(get_text(f"   ✖ ผีบุกเข้ามาในศาลา! อาหารเสียหาย 🍚-{lost}",
                                   f"   ✖ They broke into the sala! Food ruined 🍚-{lost}"))
            for person in rng.sample(people, min(len(people), rng.randint(1, RAID_BITES))):
                damage = rng.randint(15, 30)
                hurt(person, damage)
                report.append(get_text(f"   🩸 {person['name']} ถูกผีทำร้าย (HP -{damage})", f"   🩸 {person['name']} was attacked (HP -{damage})"))
                infect(person, bite, rng, report)
        return "raid"
    if roll < 0.60:
        scrap = min(2, state["resources"]["scrap"])
        state["resources"]["scrap"] -= scrap
        storage.gain("water", 3)
        report.append(get_text(f"⛈ ฝนตกหนัก! หลังคาศาลารั่ว ธูปเทียนเปียก 🕯-{scrap} แต่รองน้ำฝนได้ 💧+3",
                               f"⛈ Heavy rain! The roof leaks, soaking 🕯-{scrap}, but you collect 💧+3"))
        return "rain"
    if roll < 0.70:
        person = rng.choice(people)
        hurt(person, 20)
        report.append(get_text(f"😱 {person['name']} ฝันร้ายทั้งคืน (HP -20)", f"😱 {person['name']} had nightmares all night (HP -20)"))
        return "sick"
    if roll < 0.82:
        storage.gain("medicine", 1)
        storage.gain("food", 2)
        report.append(get_text("🎁 ญาติที่โลกมนุษย์ทำบุญส่งของมาให้! 🏺+1 🍚+2", "🎁 Family back home made merit for you! 🏺+1 🍚+2"))
        return "drop"
    report.append(get_text("🌙 คืนนี้เงียบ... ได้ยินแต่เสียงหมาหอนไกลๆ", "🌙 A quiet night... only dogs howling in the distance."))
    return "quiet"


def rescued() -> list:
    """คนที่ได้ผ่านประตูมิติกลับบ้าน (กฎ: คนที่ถูกผีสิงผ่านไม่ได้)"""
    return [p for p in storage.state["survivors"] if not p["infected"]]


def ending_grade(alive: int, early: bool = False) -> tuple:
    """
    ผลลัพธ์ตอนจบตามจำนวนคนที่ได้รับการช่วยเหลือ คืนค่า (จำนวนดาว 0-3, ชื่อฉายา)
    กลับบ้านก่อนด้วยตั๋วครบ (early) ได้ดาวพิเศษ +1 (สูงสุด 3)
    """
    bonus = 1 if early and alive else 0
    if alive >= 5:
        return 3, get_text("ผู้นำในตำนาน", "Legendary Leader")
    if alive >= 3:
        return min(3, 2 + bonus), get_text("ทีมใจเหล็ก", "Iron Hearts")
    if alive >= 1:
        return 1 + bonus, get_text("รอดแบบหวุดหวิด", "Barely Made It")
    return 0, get_text("ติดอยู่ในมิติผีตลอดกาล", "Lost Forever")


def do_end_day(rng: random.Random = None) -> dict:
    """
    จบวันและคำนวณผลทั้งหมด (ใช้ร่วมกันทั้ง Terminal และ GUI)
    คืนค่า {"lines": [ข้อความเล่าเหตุการณ์], "event": เหตุการณ์กลางคืน, "dead": [ชื่อคนที่เสียชีวิต], "status": ...}
    """
    rng = rng or random.Random()
    state = storage.state
    report = []

    resolve_jobs(rng, report)
    produce(report)
    eat_and_drink(rng, report)
    spread_infection(rng, report)
    reveal_disguised(rng, report)
    realm.check_vow(rng, report)
    event = night_event(rng, report)

    # ผู้ที่ HP หมดเสียชีวิต (ระดับปกติขึ้นไป ผีของเขาอาจกลับมา)
    dead = [p["name"] for p in state["survivors"] if p["hp"] <= 0]
    state["survivors"] = [p for p in state["survivors"] if p["hp"] > 0]
    state["log"]["deaths"] += len(dead)
    for name in dead:
        realm.add_fallen(name)
        report.append(get_text(f"🪦 {name} จากไปแล้ว...", f"🪦 {name} did not survive..."))

    state["log"]["days"].append({"day": state["day"], "food": state["resources"]["food"],
                                 "water": state["resources"]["water"], "people": len(state["survivors"]),
                                 "event": event})

    # ตรวจชนะ/แพ้ (ตั๋วครบ = กลับบ้านก่อน) แล้วเริ่มวันใหม่
    early = bool(state["survivors"]) and realm.escape_ready() and state["day"] < storage.goal_day()
    if not state["survivors"]:
        state["status"] = "lost"
    elif state["day"] >= storage.goal_day() or early:
        state["status"] = "won"
        state["escaped"] = early
    else:
        state["day"] += 1
        for person in state["survivors"]:
            person["job"] = None
        state["prepared"], state["light"], state["calm"] = [], "normal", False
        state["wanderer"] = None
        if len(state["survivors"]) < MAX_CAMP and rng.random() < WANDERER_CHANCE:
            state["wanderer"] = make_wanderer(rng)
        realm.make_omen(rng)

    # เกมจบ: จดผลลงประวัติ
    if state["status"] != "playing":
        saved = len(rescued()) if state["status"] == "won" else 0
        storage.record_result(ending_grade(saved, early)[0], saved, early)

    storage.save_game()
    return {"lines": report, "event": event, "dead": dead, "status": state["status"], "early": early}


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
        stars, title = ending_grade(len(saved), result["early"])
        if result["early"]:
            print(get_text(f"\n🎫 ตั๋วครบ {TICKET_PIECES} ชิ้น! ประตูบ้านผีสิงเปิดออกตั้งแต่คืนที่ {state['day']} (ดาวพิเศษ +1)",
                           f"\n🎫 All {TICKET_PIECES} ticket pieces! The haunted-house door opens on night {state['day']} (bonus star)"))
        print(get_text(f"\n🌀 ประตูมิติเปิดแล้ว! พากลับโลกมนุษย์ได้ {len(saved)} คน",
                       f"\n🌀 The portal opens! {len(saved)} survivor(s) make it home"))
        if left_behind:
            print(get_text(f"   (คนที่ถูกผีสิง {left_behind} คนผ่านประตูมิติไม่ได้...)",
                           f"   ({left_behind} possessed survivor(s) could not pass through...)"))
        print(f"   {'⭐' * stars}  {title}")
    elif result["status"] == "lost":
        print(get_text("\n☠ ศาลาเงียบงัน... ไม่มีใครได้กลับบ้าน", "\n☠ The sala falls silent... No one made it home."))
    else:
        print(get_text(f"\n🌅 เช้าวันที่ {state['day']}/{storage.goal_day()}", f"\n🌅 Morning of day {state['day']}/{storage.goal_day()}"))
        if realm.omen_text():
            print(realm.omen_text())
        infected = [p["name"] for p in state["survivors"] if p["infected"]]
        if infected:
            print(get_text(f"😈 ถูกผีสิงอยู่: {', '.join(infected)} — มอบงานประพรมน้ำมนต์ด่วน!",
                           f"😈 Possessed: {', '.join(infected)} — assign someone to bless them now!"))
        if state["wanderer"]:
            print(get_text(f"🚶 มีคนมาขอเข้าศาลาที่ประตู: {state['wanderer']['name']}",
                           f"🚶 Someone is at the gate: {state['wanderer']['name']}"))


def camp_stats() -> dict:
    """
    คำนวณสถิติศาลา (ใช้ร่วมกันทั้ง Terminal และ GUI):
    ของที่หามาได้ทั้งหมด อัตราป้องกันการบุก อัตราไล่ผีออกจากร่าง คนที่เก่งแต่ละด้าน และอาหาร/น้ำต่ำสุดที่เคยเหลือ
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
        "lowest_food": min((d["food"] for d in days), default=storage.state["resources"]["food"]),
        "lowest_water": min((d["water"] for d in days), default=storage.state["resources"]["water"]),
    }


def camp_log() -> None:
    """บันทึกศาลา: สถิติและกราฟอาหารรายวัน"""
    state = storage.state
    log = state["log"]
    stats = camp_stats()
    heading("บันทึกศาลา", "SALA LOG")
    survived = min(state["day"] - (0 if state["status"] != "playing" else 1), storage.goal_day())
    print(get_text(f"รอดมาแล้ว {survived}/{storage.goal_day()} วัน   ", f"Survived {survived}/{storage.goal_day()} days   ")
          + "■" * survived + "□" * (storage.goal_day() - survived))
    print(get_text(f"ผู้รอดชีวิต {len(state['survivors'])} คน   เข้าร่วมใหม่ {log['joined']}   เสียชีวิต {log['deaths']}",
                   f"Survivors {len(state['survivors'])}   joined {log['joined']}   died {log['deaths']}"))
    print(get_text(f"ผีบุก {log['raids']} ครั้ง   ต้านไว้ได้ {log['repelled']} ({stats['defense_rate']:.0f}%)",
                   f"Raids {log['raids']}   repelled {log['repelled']} ({stats['defense_rate']:.0f}%)"))
    print(get_text(f"ถูกผีสิง {log['infected']} ครั้ง   ไล่ผีออกได้ {log['cured']} ({stats['cure_rate']:.0f}%)   กลายเป็นผี {log['turned']}",
                   f"Possessions {log['infected']}   freed {log['cured']} ({stats['cure_rate']:.0f}%)   became ghosts {log['turned']}"))
    print(get_text(f"ฝูงใหญ่ที่สุดที่เจอ: พลัง {log['biggest_horde']}", f"Biggest horde faced: power {log['biggest_horde']}"))
    gathered = "  ".join(f"{RESOURCES[k]['icon']}{v}" for k, v in log["gathered"].items())
    print(get_text(f"หาของได้ทั้งหมด {stats['gathered']} ชิ้น   ({gathered})", f"Total gathered {stats['gathered']}   ({gathered})"))
    print(get_text(f"อาหารเหลือน้อยสุด {stats['lowest_food']}   น้ำเหลือน้อยสุด {stats['lowest_water']}",
                   f"Lowest food {stats['lowest_food']}   lowest water {stats['lowest_water']}"))

    if stats["best"]:
        print(get_text("\nเก่งที่สุดในศาลา:", "\nBest in the sala:"))
        for skill, person in stats["best"].items():
            print(f"  {tr(SKILLS[skill]):<10} {person['name']:<10} {survivors.stars(person['skills'][skill])}")

    if log["days"]:
        print(get_text("\nอาหารคงเหลือตอนจบแต่ละวัน:", "\nFood left at the end of each day:"))
        for entry in log["days"][-8:]:
            print(f"  {get_text('วัน', 'Day')} {entry['day']:>2}  {'█' * min(entry['food'], 30):<30} {entry['food']}")
    print(get_text(f"\nคาดการณ์ตอนนี้: อาหาร{camp.days_text('food')}  น้ำ{camp.days_text('water')}",
                   f"\nForecast now: food {camp.days_text('food')}, water {camp.days_text('water')}"))
