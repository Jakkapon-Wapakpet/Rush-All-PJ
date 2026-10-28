#!/usr/bin/env python3
"""
Heroes Module - OVERGEAR (ร้านตีอาวุธ)
ผู้กล้าที่ใช้อาวุธของเราออกล่าสัตว์ประหลาดทุกคืน: รอด -> ชื่อเสียงและของหายาก, ตาย -> ร้านเสียชื่อ
รวมภารกิจตามหาวัตถุดิบตำนาน การมอบอาวุธ และการแต่งตั้งแชมป์สู้มังกร
Heroes hunt every night with our weapons; survivors bring fame and loot, deaths cost fame.
"""

import random

from language import get_text, clear_screen, pause
from data import (CLASSES, HERO_NAMES, MONSTERS, LEGEND_QUESTS, MATERIALS, TASKS, MID_LOOT, HIGH_LOOT, MAX_HEROES,
                  MAX_LEVEL, HERO_LEVEL_POWER, HERO_LEAVE_DAYS, DEATH_FAME, tr)
from ui import heading, choose_from_list, show_error
import forge
import market
import storage


# ---------- ข้อมูลผู้กล้า ----------

def make_hero(rng: random.Random, level: int = 1) -> dict:
    """สร้างผู้กล้า 1 คน (ชื่อไม่ซ้ำกับคนที่อยู่ในเมือง) ยังไม่มีอาวุธ"""
    used = [hero["name"]["en"] for hero in storage.state["heroes"]]
    names = [name for name in HERO_NAMES if name["en"] not in used] or HERO_NAMES
    return {"id": storage.next_id(), "name": dict(rng.choice(names)), "class": rng.choice(list(CLASSES)),
            "level": level, "xp": 0, "weapon": None, "task": "hunt", "rest": 0, "idle": 0, "kills": 0}


def find_hero(hero_id) -> dict:
    """หาผู้กล้าจาก id คืนค่า None ถ้าไม่อยู่แล้ว (ตายหรือออกจากเมือง)"""
    for hero in storage.state["heroes"]:
        if hero["id"] == hero_id:
            return hero
    return None


def armed(hero: dict) -> bool:
    """ถืออาวุธของเราที่ยังไม่หัก"""
    return bool(hero["weapon"]) and hero["weapon"]["dur"] > 0


def hero_power(hero: dict) -> int:
    """พลังของผู้กล้า = เลเวล × 3 + พลังอาวุธของเรา (ถ้าอาวุธหักนับ 0)"""
    weapon_power = hero["weapon"]["power"] if armed(hero) else 0
    return hero["level"] * HERO_LEVEL_POWER + weapon_power


def hero_name(hero: dict) -> str:
    """ชื่อพร้อมอาชีพ เช่น 🛡 อัลดริก (อัศวิน Lv3)"""
    info = CLASSES[hero["class"]]
    return f"{info['icon']} {tr(hero['name'])} ({tr(info['name'])} Lv{hero['level']})"


def max_heroes() -> int:
    """ผู้กล้าที่อยู่ในเมืองได้ตามชื่อเสียงร้าน: 2 + ชื่อเสียง/25 (สูงสุด 6)"""
    return min(MAX_HEROES, 2 + storage.state["fame"] // 25)


# ---------- การล่า ----------

def hunt_target(hero: dict) -> int:
    """สัตว์ประหลาดที่ผู้กล้าเลือกล่า: ตามเลเวล (บาร์บาเรียนบ้าบิ่นล่าสูงกว่า 1 ขั้น)"""
    target = 0
    for index, monster in enumerate(MONSTERS):
        if hero["level"] >= monster["level"]:
            target = index
    return min(len(MONSTERS) - 1, target + CLASSES[hero["class"]]["bold"])


def threat_of(base: int) -> int:
    """ความแข็งจริง = ค่าฐาน × ระดับความยาก × ข่าว (สัตว์ประหลาดชุกชุม)"""
    return round(base * storage.setting("threat") * market.news_value("threat", 1.0))


def win_chance(power: int, threat: int) -> float:
    """โอกาสชนะ = 1 − 0.3 ÷ (พลัง/ความแข็ง)²  (อยู่ระหว่าง 5%-97%)"""
    ratio = power / threat if threat else 9
    return max(0.05, min(0.97, 1 - 0.3 / (ratio * ratio)))


def death_chance(power: int, threat: int) -> float:
    """ถ้าแพ้: โอกาสตาย 15% (ถ้าพลังน้อยกว่าความแข็ง 35%) ที่เหลือบาดเจ็บกลับมา"""
    return 0.15 if power >= threat else 0.35


def tonight_plan(hero: dict) -> dict:
    """คืนนี้ผู้กล้าจะไปไหน คืนค่า {"kind": rest/idle/hunt/quest, "threat", "chance", "name"}"""
    if hero["rest"] > 0:
        return {"kind": "wounded", "threat": 0, "chance": 0, "name": get_text("พักฟื้น", "recovering")}
    if not armed(hero):
        return {"kind": "idle", "threat": 0, "chance": 0, "name": get_text("รออาวุธ", "needs a weapon")}
    if hero["task"] == "rest":
        return {"kind": "rest", "threat": 0, "chance": 0, "name": tr(TASKS["rest"])}
    if hero["task"] in LEGEND_QUESTS:
        quest = LEGEND_QUESTS[hero["task"]]
        threat = threat_of(quest["threat"])
        return {"kind": "quest", "threat": threat, "chance": win_chance(hero_power(hero), threat),
                "name": f"{quest['icon']} {tr(quest['name'])}"}
    monster = MONSTERS[hunt_target(hero)]
    threat = threat_of(monster["threat"])
    return {"kind": "hunt", "threat": threat, "chance": win_chance(hero_power(hero), threat),
            "name": f"{monster['icon']} {tr(monster['name'])}"}


def gain_xp(hero: dict, amount: int) -> bool:
    """เพิ่มประสบการณ์ เลเวลขึ้นเมื่อ xp ถึงเลเวลปัจจุบัน คืนค่า True ถ้าเลเวลขึ้น"""
    hero["xp"] += amount
    leveled = False
    while hero["level"] < MAX_LEVEL and hero["xp"] >= hero["level"]:
        hero["xp"] -= hero["level"]
        hero["level"] += 1
        leveled = True
    return leveled


def loot_offer(hero: dict, monster_index: int, rng: random.Random):
    """ผู้กล้าที่ชนะอาจนำของกลับมาขาย: สัตว์ระดับ 2 ได้ของกลาง ระดับ 3 ลุ้นของดี 30% ระดับ 4-5 ได้มิธริลหรือของตำนาน"""
    chance = MONSTERS[monster_index]["loot"] * market.news_value("loot", 1.0)
    if rng.random() >= chance:
        return None
    high = monster_index >= 3 or (monster_index == 2 and rng.random() < 0.3)
    key = rng.choice(HIGH_LOOT if high else MID_LOOT)
    price = max(1, round(MATERIALS[key]["price"] * rng.uniform(0.5, 0.8)))
    return {"material": key, "price": price, "hero": dict(hero["name"])}


def hunt_result(hero: dict, rng: random.Random) -> dict:
    """
    ผลการออกล่า 1 คืนของผู้กล้า 1 คน (ใช้อาวุธของเรา)
    คืนค่า {"outcome": win/wounded/dead/skip, "plan": ..., "loot": ของที่ได้ หรือ None, "level_up": bool}
    """
    plan = tonight_plan(hero)
    result = {"outcome": "skip", "plan": plan, "loot": None, "level_up": False, "broke": False}
    if plan["kind"] not in ("hunt", "quest"):
        return result
    state = storage.state
    weapon = hero["weapon"]
    quest = LEGEND_QUESTS.get(hero["task"]) if plan["kind"] == "quest" else None
    state["log"]["hunts"] += 1
    if rng.random() < plan["chance"]:
        result["outcome"] = "win"
        state["log"]["wins"] += 1
        hero["kills"] += 1
        weapon["dur"] -= 1
        if quest:
            # ภารกิจตำนานสำเร็จ: ได้วัตถุดิบตำนานฟรี (จ่ายค่าจ้างไปแล้ว)
            state["materials"][quest["material"]] += 1
            state["log"]["legends"] += 1
            result["loot"] = {"material": quest["material"], "price": 0, "hero": dict(hero["name"])}
            result["level_up"] = gain_xp(hero, 3)
            storage.add_fame(3)
            hero["task"] = "hunt"
        else:
            index = hunt_target(hero)
            result["level_up"] = gain_xp(hero, 2 if index >= 3 else 1)
            storage.add_fame((1 if index >= 1 else 0) + (1 if index >= 3 else 0))
            result["loot"] = loot_offer(hero, index, rng)
    elif rng.random() < death_chance(hero_power(hero), plan["threat"]):
        result["outcome"] = "dead"
    else:
        result["outcome"] = "wounded"
        hero["rest"] = 2
        weapon["dur"] -= 2
        if quest:
            hero["task"] = "hunt"
    if weapon["dur"] <= 0:
        weapon["dur"] = 0
        result["broke"] = result["outcome"] != "dead"
    return result


def outcome_text(hero: dict, result: dict) -> str:
    """ข้อความเล่าผลการล่าของผู้กล้า 1 คน"""
    name = hero_name(hero)
    plan = result["plan"]
    if result["outcome"] == "win":
        text = get_text(f"🏆 {name} ปราบ {plan['name']} ได้! (ชื่อเสียงร้าน +)",
                        f"🏆 {name} defeated {plan['name']}! (shop fame +)")
        if result["loot"] and result["loot"]["price"] == 0:
            text += get_text(f" ได้ {market.material_text(result['loot']['material'])} มามอบให้ร้าน!",
                             f" Brought back {market.material_text(result['loot']['material'])} for you!")
        elif result["loot"]:
            text += get_text(f" นำ {market.material_text(result['loot']['material'])} มาขายพรุ่งนี้",
                             f" Will sell {market.material_text(result['loot']['material'])} tomorrow")
        if result["level_up"]:
            text += get_text(f" ⬆ เลเวล {hero['level']}", f" ⬆ Level {hero['level']}")
    elif result["outcome"] == "wounded":
        text = get_text(f"🩹 {name} แพ้ {plan['name']} บาดเจ็บกลับมา (พัก 2 วัน)",
                        f"🩹 {name} lost to {plan['name']} and limped home (rests 2 days)")
    else:
        text = get_text(f"⚰ {name} ไม่ได้กลับมาจาก {plan['name']}... ร้านเสียชื่อเสียง -{DEATH_FAME}",
                        f"⚰ {name} never came back from {plan['name']}... fame -{DEATH_FAME}")
    if result["broke"]:
        text += get_text("  🔧 อาวุธหัก! ต้องซ่อม", "  🔧 Weapon broke! Needs repair")
    return text


def night_hunts(rng: random.Random, report: list) -> None:
    """ลูปผู้กล้าออกล่าในคืนนี้ แล้วจัดการคนที่ตาย พักฟื้น และของที่นำมาขายพรุ่งนี้"""
    state = storage.state
    offers = []
    for hero in list(state["heroes"]):
        if hero["rest"] > 0:
            hero["rest"] -= 1
            continue
        if hero["task"] in LEGEND_QUESTS:
            fee = LEGEND_QUESTS[hero["task"]]["fee"]
            if not armed(hero) or state["gold"] < fee:
                hero["task"] = "hunt"
                report.append(get_text(f"✖ {tr(hero['name'])} ยกเลิกภารกิจตำนาน (เงินไม่พอหรืออาวุธหัก)",
                                       f"✖ {tr(hero['name'])} cancelled the legend quest (no gold or broken weapon)"))
            else:
                storage.pay(fee)
        result = hunt_result(hero, rng)
        if result["outcome"] == "skip":
            continue
        report.append(outcome_text(hero, result))
        if result["outcome"] == "dead":
            remove_hero(hero, died=True)
        elif result["loot"] and result["loot"]["price"] > 0:
            offers.append(result["loot"])
    state["offers"] = offers


def remove_hero(hero: dict, died: bool) -> None:
    """เอาผู้กล้าออกจากเมือง (ตาย = เสียชื่อเสียงและจดชื่อไว้)"""
    state = storage.state
    state["heroes"].remove(hero)
    if state["champion"] == hero["id"]:
        state["champion"] = None
    # ออเดอร์ของผู้กล้าคนนี้ไม่มีคนรับของแล้ว ยกเลิกโดยไม่เสียชื่อ
    state["orders"] = [o for o in state["orders"] if o.get("hero") != hero["id"]]
    state["board"] = [o for o in state["board"] if o.get("hero") != hero["id"]]
    if died:
        storage.add_fame(-DEATH_FAME)
        state["log"]["deaths"] += 1
        state["fallen"].append(dict(hero["name"]))


def morning_heroes(rng: random.Random, report: list) -> None:
    """ตอนเช้า: ผู้กล้าที่ไม่มีอาวุธนานเกินไปจะไปซื้อร้านอื่น และอาจมีผู้กล้าคนใหม่มาที่เมือง"""
    state = storage.state
    for hero in list(state["heroes"]):
        if armed(hero):
            hero["idle"] = 0
            continue
        hero["idle"] += 1
        if hero["idle"] > HERO_LEAVE_DAYS:
            remove_hero(hero, died=False)
            storage.add_fame(-1)
            report.append(get_text(f"🚶 {tr(hero['name'])} รออาวุธไม่ไหว ไปซื้อร้านคู่แข่งแล้ว (ชื่อเสียง -1)",
                                   f"🚶 {tr(hero['name'])} gave up waiting and went to the rival smith (fame -1)"))
    if len(state["heroes"]) < max_heroes() and rng.random() < 0.45:
        top = min(5, 1 + state["day"] // 7)
        hero = make_hero(rng, rng.randint(1, top))
        state["heroes"].append(hero)
        report.append(get_text(f"🐎 ผู้กล้าคนใหม่มาถึงเมือง: {hero_name(hero)}",
                               f"🐎 A new hero arrives in town: {hero_name(hero)}"))


# ---------- การกระทำของผู้เล่น ----------

def do_set_task(hero: dict, task: str) -> str:
    """สั่งงานผู้กล้าคืนนี้: ออกล่า / พัก / ภารกิจตามหาวัตถุดิบตำนาน (จ่ายค่าจ้างตอนออกเดินทาง)"""
    if hero not in storage.state["heroes"]:
        return get_text("ไม่มีผู้กล้าคนนี้แล้ว", "That hero is gone.")
    if task not in TASKS and task not in LEGEND_QUESTS:
        return get_text("ไม่มีงานนี้", "Unknown task.")
    if task in LEGEND_QUESTS:
        if not armed(hero):
            return get_text("ต้องถืออาวุธของเราที่ยังไม่หักก่อน", "The hero needs one of our unbroken weapons.")
        if hero["rest"] > 0:
            return get_text("ผู้กล้ากำลังพักฟื้น", "The hero is still recovering.")
        error = storage.check_gold(LEGEND_QUESTS[task]["fee"])
        if error:
            return error
    hero["task"] = task
    storage.save_game()
    return ""


def do_give_weapon(hero: dict, weapon: dict) -> str:
    """มอบอาวุธจากชั้นวางให้ผู้กล้า (ฟรี ชื่อเสียง +1) อาวุธเก่าที่ยังใช้ได้กลับมาที่ชั้นวาง"""
    state = storage.state
    if hero not in state["heroes"]:
        return get_text("ไม่มีผู้กล้าคนนี้แล้ว", "That hero is gone.")
    if weapon not in state["weapons"]:
        return get_text("ไม่มีอาวุธชิ้นนี้บนชั้นวาง", "That weapon is not on the rack.")
    state["weapons"].remove(weapon)
    old = hero["weapon"]
    if old and old["dur"] > 0:
        state["weapons"].append(old)
    hero["weapon"] = weapon
    hero["idle"] = 0
    # ผู้กล้าได้อาวุธแล้ว ออเดอร์/คำขอซ่อมของเขาบนกระดานไม่จำเป็นแล้ว
    state["board"] = [o for o in state["board"] if o.get("hero") != hero["id"]]
    storage.add_fame(1)
    storage.save_game()
    return ""


def do_set_champion(hero: dict) -> str:
    """แต่งตั้งแชมป์ที่จะสู้มังกรวันที่ 30 (ต้องถืออาวุธของเรา)"""
    if hero not in storage.state["heroes"]:
        return get_text("ไม่มีผู้กล้าคนนี้แล้ว", "That hero is gone.")
    if not hero["weapon"]:
        return get_text("แชมป์ต้องถืออาวุธของร้านเรา", "The champion must carry one of our weapons.")
    storage.state["champion"] = hero["id"]
    storage.save_game()
    return ""


def champion() -> dict:
    """ผู้กล้าแชมป์ปัจจุบัน (หรือ None)"""
    return find_hero(storage.state["champion"])


# ---------- เมนู Terminal ----------

def show_heroes() -> None:
    """ตารางผู้กล้าทุกคน: เลเวล อาวุธ พลัง และแผนคืนนี้พร้อมโอกาสรอด"""
    state = storage.state
    heading("ผู้กล้าในเมือง", "HEROES IN TOWN")
    print(get_text(f" รับได้ {len(state['heroes'])}/{max_heroes()} คน (ชื่อเสียงยิ่งสูง ผู้กล้ายิ่งมาเยอะ)",
                   f" {len(state['heroes'])}/{max_heroes()} heroes (more fame attracts more heroes)"))
    if not state["heroes"]:
        print(get_text(" ยังไม่มีผู้กล้า", " No heroes yet."))
    for number, hero in enumerate(state["heroes"], start=1):
        crown = " 👑" if hero["id"] == state["champion"] else ""
        print(f"\n {number}. {hero_name(hero)}{crown}  {get_text('พลัง', 'PWR')} {hero_power(hero)}  "
              f"XP {hero['xp']}/{hero['level']}  {get_text('ปราบ', 'kills')} {hero['kills']}")
        if hero["weapon"]:
            broken = get_text(" (หัก!)", " (BROKEN!)") if hero["weapon"]["dur"] <= 0 else ""
            print(f"    {forge.weapon_label(hero['weapon'])}  {get_text('ทนทาน', 'dur')} "
                  f"{hero['weapon']['dur']}/{hero['weapon']['max_dur']}{broken}")
        else:
            likes = ", ".join(tr(forge.WEAPONS[t]["name"]) for t in CLASSES[hero["class"]]["likes"])
            print(get_text(f"    ไม่มีอาวุธ อยากได้: {likes} (รออีก {HERO_LEAVE_DAYS - hero['idle']} วัน)",
                           f"    Unarmed, wants: {likes} (leaves in {HERO_LEAVE_DAYS - hero['idle']} days)"))
        plan = tonight_plan(hero)
        if plan["kind"] in ("hunt", "quest"):
            print(get_text(f"    คืนนี้: {plan['name']} (ความแข็ง {plan['threat']}) โอกาสชนะ {plan['chance']:.0%}",
                           f"    Tonight: {plan['name']} (threat {plan['threat']}) win chance {plan['chance']:.0%}"))
        else:
            print(get_text(f"    คืนนี้: {plan['name']}", f"    Tonight: {plan['name']}"))
    if state["fallen"]:
        names = ", ".join(tr(name) for name in state["fallen"])
        print(get_text(f"\n ⚰ ผู้กล้าที่จากไป: {names}", f"\n ⚰ Fallen heroes: {names}"))


def task_menu() -> None:
    """สั่งงานผู้กล้า: ออกล่า พัก หรือส่งไปภารกิจตำนาน"""
    hero = choose_from_list(storage.state["heroes"], "เลือกผู้กล้า", "Choose a hero")
    if hero is None:
        return
    tasks = ["hunt", "rest"] + list(LEGEND_QUESTS)
    for number, task in enumerate(tasks, start=1):
        if task in TASKS:
            print(f" {number}. {tr(TASKS[task])}")
            continue
        quest = LEGEND_QUESTS[task]
        threat = threat_of(quest["threat"])
        print(get_text(f" {number}. {quest['icon']} {tr(quest['name'])} → {market.material_text(quest['material'])}  "
                       f"ค่าจ้าง {quest['fee']}  ความแข็ง {threat}  โอกาสชนะ {win_chance(hero_power(hero), threat):.0%}",
                       f" {number}. {quest['icon']} {tr(quest['name'])} → {market.material_text(quest['material'])}  "
                       f"fee {quest['fee']}  threat {threat}  win {win_chance(hero_power(hero), threat):.0%}"))
    task = choose_from_list(tasks, "เลือกงาน", "Choose a task")
    if task and not show_error(do_set_task(hero, task)):
        print(get_text("✔ สั่งงานแล้ว (มีผลคืนนี้)", "✔ Task set for tonight."))


def give_menu() -> None:
    """มอบอาวุธจากชั้นวางให้ผู้กล้า"""
    state = storage.state
    hero = choose_from_list(state["heroes"], "เลือกผู้กล้า", "Choose a hero")
    if hero is None:
        return
    for number, weapon in enumerate(state["weapons"], start=1):
        print(f" {number}. {forge.weapon_label(weapon)}")
    weapon = choose_from_list(state["weapons"], "เลือกอาวุธที่จะมอบ", "Choose a weapon to give")
    if weapon and not show_error(do_give_weapon(hero, weapon)):
        print(get_text(f"✔ {tr(hero['name'])} รับอาวุธแล้ว พลังตอนนี้ {hero_power(hero)}",
                       f"✔ {tr(hero['name'])} took it. Power now {hero_power(hero)}"))


def champion_menu() -> None:
    """แต่งตั้งแชมป์สู้มังกร"""
    hero = choose_from_list(storage.state["heroes"], "เลือกแชมป์", "Choose a champion")
    if hero and not show_error(do_set_champion(hero)):
        print(get_text(f"👑 {tr(hero['name'])} คือแชมป์ของหมู่บ้าน!", f"👑 {tr(hero['name'])} is the village champion!"))


def heroes_menu() -> None:
    """ลูปเมนูผู้กล้า"""
    actions = {"1": task_menu, "2": give_menu, "3": champion_menu}
    while True:
        clear_screen()
        show_heroes()
        print("-" * 60)
        print(get_text("1. สั่งงาน/ภารกิจตำนาน   2. มอบอาวุธจากชั้นวาง   3. แต่งตั้งแชมป์ 👑   0. กลับ",
                       "1. Task / legend quest   2. Give a rack weapon   3. Appoint champion 👑   0. Back"))
        choice = input(get_text("\nเลือก: ", "\nChoose: ")).strip()
        if choice == "0":
            return
        if choice in actions:
            actions[choice]()
        else:
            print(get_text("ไม่มีเมนูนี้", "Invalid option."))
        pause("\nกด Enter...", "\nPress Enter...")
