#!/usr/bin/env python3
"""
Dungeon Module - DUNGEON RUSH
สอดแนมศัตรู คำนวณโอกาสชนะ ต่อสู้ และสรุปบันทึกการผจญภัย
Scout the enemy, estimate win chance, fight, and show the adventure log.

สูตรต่อสู้ (อธิบายได้ในประโยคเดียว):
  ดาเมจ = ATK ผู้โจมตี - DEF ผู้รับ (อย่างน้อย 1) สุ่ม ±20%
          ถ้าโดนธาตุที่แพ้ทาง x2, ถ้าโดนธาตุที่ไม่เข้า = 0
"""

import random
import time

from language import get_text
from data import MONSTERS, ELEMENTS, ITEMS, tr
from ui import heading, ask_yes_no, choose_from_list
import heroes
import items
import storage

MAX_ROUNDS = 30          # ต่อสู้นานเกินนี้ถือว่าแพ้ (ถอยทัพ)
SIMULATIONS = 300        # จำนวนรอบจำลองเพื่อคำนวณโอกาสชนะ
POTION_AT = 0.4          # ดื่มยาอัตโนมัติเมื่อ HP ต่ำกว่า 40%
LOSS_PENALTY = 0.2       # แพ้แล้วเสียทอง 20%
BATTLE_DELAY = 0.35      # หน่วงเวลาระหว่างบรรทัดตอนต่อสู้ (วินาที)


def current_monster():
    """มอนสเตอร์ของชั้นที่จะลงต่อไป หรือ None หากปราบครบทุกชั้นแล้ว"""
    floor = storage.state["floor"]
    if floor > len(MONSTERS):
        return None
    return MONSTERS[floor - 1]


def roll(value: int, rng: random.Random) -> int:
    """สุ่มค่า ±20%"""
    return round(value * rng.uniform(0.8, 1.2))


def hit_monster(hero: dict, monster: dict, rng: random.Random) -> tuple:
    """ดาเมจที่ฮีโร่ทำกับมอนสเตอร์ คืนค่า (ดาเมจ, 'weak' / 'immune' / '')"""
    element = heroes.hero_element(hero)
    if element == monster["immune"]:
        return 0, "immune"
    damage = max(1, roll(max(1, heroes.hero_attack(hero) - monster["def"]), rng))
    if element == monster["weak"]:
        return damage * 2, "weak"
    return damage, ""


def heal_amount(hero: dict) -> int:
    """ปริมาณที่นักบวชรักษาต่อเทิร์น"""
    return 4 + hero["level"] * 2


def fight(monster: dict, rng: random.Random, show: bool, record: bool = False) -> dict:
    """
    จำลองการต่อสู้ 1 ครั้ง โดยไม่แก้ไขข้อมูลจริงของเกม
      show   = พิมพ์ผลทีละบรรทัด (Terminal)
      record = เก็บเหตุการณ์ทุกบรรทัดพร้อม HP ณ ตอนนั้น ไว้ให้ GUI เล่นซ้ำ
    คืนค่า {"won": bool, "hp": [HP ของฮีโร่แต่ละคนหลังสู้], "potions": จำนวนยาที่ใช้,
            "rounds": จำนวนเทิร์น, "events": [{"text", "kind", "monster_hp", "hp"}, ...]}
    """
    party = storage.state["heroes"]
    hp = [hero["hp"] for hero in party]
    potions_left = items.count_potions()
    potions_used = 0
    monster_hp = monster["hp"]
    name = tr(monster["name"])

    events = []

    def say(text: str, kind: str) -> None:
        if show:
            print(text)
            time.sleep(BATTLE_DELAY)
        if record:
            events.append({"text": text.strip(), "kind": kind, "monster_hp": max(monster_hp, 0), "hp": list(hp)})

    for round_number in range(1, MAX_ROUNDS + 1):
        say(get_text(f"\n── เทิร์น {round_number} ──  {name} HP {max(monster_hp, 0)}/{monster['hp']}",
                     f"\n── Round {round_number} ──  {name} HP {max(monster_hp, 0)}/{monster['hp']}"), "round")

        # ตาของฮีโร่ทีละคน
        for index, hero in enumerate(party):
            if hp[index] <= 0:
                continue

            # ดื่มยาแทนการโจมตี เมื่อ HP ต่ำและยังมียา
            if hp[index] < hero["max_hp"] * POTION_AT and potions_left > 0:
                potions_left -= 1
                potions_used += 1
                hp[index] = min(hero["max_hp"], hp[index] + ITEMS["potion"]["heal"])
                say(get_text(f"🧪 {hero['name']} ดื่มยา → HP {hp[index]}/{hero['max_hp']}",
                             f"🧪 {hero['name']} drinks a potion → HP {hp[index]}/{hero['max_hp']}"), "potion")
                continue

            damage, note = hit_monster(hero, monster, rng)
            monster_hp -= damage
            if note == "immune":
                say(get_text(f"⚔  {hero['name']} โจมตี → {name} ไม่ได้รับความเสียหาย!",
                             f"⚔  {hero['name']} attacks → {name} is unharmed!"), "immune")
            elif note == "weak":
                say(get_text(f"✦  {hero['name']} โจมตี → {damage} ดาเมจ (แพ้ทาง x2!)",
                             f"✦  {hero['name']} attacks → {damage} damage (weakness x2!)"), "weak")
            else:
                say(get_text(f"⚔  {hero['name']} โจมตี → {damage} ดาเมจ",
                             f"⚔  {hero['name']} attacks → {damage} damage"), "hit")

            if monster_hp <= 0:
                say(get_text(f"\n💥 {name} ถูกปราบแล้ว!", f"\n💥 {name} is defeated!"), "win")
                return {"won": True, "hp": hp, "potions": potions_used, "rounds": round_number, "events": events}

            # นักบวชรักษาเพื่อนที่ HP ต่ำที่สุด (คิดเป็นสัดส่วน)
            if hero["class"] == "cleric":
                alive = [i for i in range(len(party)) if hp[i] > 0]
                target = min(alive, key=lambda i: hp[i] / party[i]["max_hp"])
                if hp[target] < party[target]["max_hp"]:
                    hp[target] = min(party[target]["max_hp"], hp[target] + heal_amount(hero))
                    say(get_text(f"✚  {hero['name']} รักษา {party[target]['name']} → HP {hp[target]}",
                                 f"✚  {hero['name']} heals {party[target]['name']} → HP {hp[target]}"), "heal")

        # ตาของมอนสเตอร์: โจมตีฮีโร่ที่ยังยืนอยู่แบบสุ่ม ตามจำนวนครั้งต่อเทิร์น
        for _ in range(monster["attacks"]):
            alive = [i for i in range(len(party)) if hp[i] > 0]
            target = rng.choice(alive)
            defense = heroes.hero_defense(party[target])
            damage = max(1, roll(max(1, monster["atk"] - defense), rng))
            hp[target] = max(0, hp[target] - damage)
            say(get_text(f"{monster['icon']} {name} โจมตี {party[target]['name']} → {damage} ดาเมจ"
                         f" (HP {hp[target]}/{party[target]['max_hp']})",
                         f"{monster['icon']} {name} hits {party[target]['name']} → {damage} damage"
                         f" (HP {hp[target]}/{party[target]['max_hp']})"), "monster")
            if hp[target] == 0:
                say(get_text(f"   💀 {party[target]['name']} หมดสติ!", f"   💀 {party[target]['name']} is knocked out!"), "ko")

            if all(value == 0 for value in hp):
                say(get_text("\n☠  ทีมของคุณพ่ายแพ้...", "\n☠  Your party has fallen..."), "lose")
                return {"won": False, "hp": hp, "potions": potions_used, "rounds": round_number, "events": events}

    say(get_text("\n⌛ สู้นานเกินไป ทีมต้องถอยทัพ!", "\n⌛ The battle drags on. Your party retreats!"), "lose")
    return {"won": False, "hp": hp, "potions": potions_used, "rounds": MAX_ROUNDS, "events": events}


def win_chance(monster: dict) -> float:
    """โอกาสชนะ (%) จากการจำลองการต่อสู้ SIMULATIONS ครั้ง (Monte Carlo)"""
    rng = random.Random()
    wins = sum(1 for _ in range(SIMULATIONS) if fight(monster, rng, show=False)["won"])
    return wins / SIMULATIONS * 100


def reward_gold(floor: int) -> int:
    """ทองที่ได้จากชั้นนี้: ชั้นที่เคยผ่านแล้วได้ครึ่งเดียว"""
    gold = MONSTERS[floor - 1]["gold"]
    if floor < storage.state["floor"]:
        return gold // 2
    return gold


def scout(floor: int) -> float:
    """แสดงข้อมูลศัตรู จุดอ่อนเทียบกับทีม และโอกาสชนะ คืนค่าโอกาสชนะ"""
    monster = MONSTERS[floor - 1]
    heading(f"ชั้น {floor}/{len(MONSTERS)}: {tr(monster['name'])}",
            f"FLOOR {floor}/{len(MONSTERS)}: {tr(monster['name'])}")
    print(f"{monster['icon']}  HP {monster['hp']}   ATK {monster['atk']}   DEF {monster['def']}"
          + get_text(f"   โจมตี {monster['attacks']} ครั้ง/เทิร์น", f"   {monster['attacks']} attack(s)/round"))
    if monster["weak"]:
        print(get_text(f"✦ แพ้ทางธาตุ{tr(ELEMENTS[monster['weak']])} (ดาเมจ x2)",
                       f"✦ Weak to {tr(ELEMENTS[monster['weak']])} (x2 damage)"))
    if monster["immune"]:
        print(get_text(f"⚠ ธาตุ{tr(ELEMENTS[monster['immune']])}ตีไม่เข้า",
                       f"⚠ Immune to {tr(ELEMENTS[monster['immune']])}"))
    print(get_text(f"รางวัล: {reward_gold(floor)} ทอง, {monster['xp']} XP",
                   f"Reward: {reward_gold(floor)} gold, {monster['xp']} XP"))

    print(get_text("\nทีมของคุณ:", "\nYour party:"))
    for hero in storage.state["heroes"]:
        element = heroes.hero_element(hero)
        note = ""
        if element == monster["immune"]:
            note = get_text("  ⚠ ตีไม่เข้า!", "  ⚠ can't hurt it!")
        elif element == monster["weak"]:
            note = get_text("  ✦ แพ้ทาง!", "  ✦ hits its weakness!")
        print(f"  {hero['name']:<12} HP {hero['hp']:>3}/{hero['max_hp']:<3} ATK {heroes.hero_attack(hero):<3}"
              f" DEF {heroes.hero_defense(hero):<3} {tr(ELEMENTS[element])}{note}")
    print(get_text(f"  ยาในกระเป๋า: {items.count_potions()}", f"  Potions in bag: {items.count_potions()}"))

    chance = win_chance(monster)
    print(get_text(f"\n🎲 โอกาสชนะโดยประมาณ: {chance:.0f}%", f"\n🎲 Estimated win chance: {chance:.0f}%"))
    if chance < 50:
        print(get_text("   คำแนะนำ: ลองเปลี่ยนอาวุธให้ตรงจุดอ่อน ซื้อเกราะ/ยา พักที่โรงเตี๊ยม หรือฝึกที่ชั้นก่อนๆ",
                       "   Tip: match its weakness, buy armor/potions, rest, or train on earlier floors."))
    return chance


def choose_floor():
    """ให้ผู้เล่นเลือกชั้น: ชั้นที่ผ่านแล้ว (ฝึก ได้ทองครึ่งเดียว) หรือชั้นใหม่ คืนค่าเลขชั้นหรือ None"""
    heading("ลงดันเจี้ยน", "ENTER THE DUNGEON")
    deepest = min(storage.state["floor"], len(MONSTERS))
    floors = list(range(1, deepest + 1))
    for floor in floors:
        monster = MONSTERS[floor - 1]
        if floor < storage.state["floor"]:
            tag = get_text(f"✔ ผ่านแล้ว (ฝึก: {reward_gold(floor)} ทอง)", f"✔ cleared (training: {reward_gold(floor)} gold)")
        else:
            tag = get_text("★ ชั้นใหม่!", "★ new floor!")
        print(f"{floor}. {monster['icon']} {tr(monster['name']):<14} {tag}")
    return choose_from_list(floors, "เลือกชั้น", "Choose a floor")


def apply_battle(floor: int, result: dict) -> list:
    """
    นำผลการต่อสู้มาใช้กับข้อมูลจริง (ใช้ร่วมกันทั้ง Terminal และ GUI)
    คืนค่ารายการข้อความสรุปผล เช่น ทองที่ได้ เลเวลอัป ชั้นที่ปลดล็อก
    """
    monster = MONSTERS[floor - 1]
    new_floor = floor == storage.state["floor"]
    gold = reward_gold(floor)
    messages = []

    # ฮีโร่ที่หมดสติถูกหามกลับมาด้วย HP 1
    for hero, hp in zip(storage.state["heroes"], result["hp"]):
        hero["hp"] = max(1, hp)
    items.use_potions(result["potions"])
    log = storage.state["log"]
    log["battles"] += 1

    if result["won"]:
        log["wins"] += 1
        log["gold_earned"] += gold
        storage.state["gold"] += gold
        messages.append(get_text(f"\n🏆 ชนะ! ได้ {gold} ทอง", f"\n🏆 Victory! +{gold} gold"))
        for hero in storage.state["heroes"]:
            if heroes.gain_xp(hero, monster["xp"]):
                messages.append(get_text(f"⬆  {hero['name']} เลเวลอัปเป็น Lv.{hero['level']}! (HP เต็ม)",
                                         f"⬆  {hero['name']} reached Lv.{hero['level']}! (HP restored)"))
        if new_floor:
            storage.state["floor"] += 1
            if current_monster() is None:
                messages.append(get_text("\n👑 คุณปราบมังกรดำได้สำเร็จ! คุณคือตำนานแห่งดันเจี้ยน!",
                                         "\n👑 You slew the Black Dragon! You are a legend of the dungeon!"))
            else:
                messages.append(get_text(f"🔓 ปลดล็อกชั้น {storage.state['floor']} แล้ว!",
                                         f"🔓 Floor {storage.state['floor']} unlocked!"))
    else:
        log["losses"] += 1
        lost = int(storage.state["gold"] * LOSS_PENALTY)
        storage.state["gold"] -= lost
        messages.append(get_text(f"\nแพ้... ทีมถูกหามกลับเมืองและทำทองหล่นหาย {lost} ทอง",
                                 f"\nDefeat... Your party is carried back to town and lost {lost} gold."))

    storage.save_game()
    return messages


def enter_dungeon() -> None:
    """ลงดันเจี้ยน: เลือกชั้น สอดแนม ยืนยัน ต่อสู้ และรับผล"""
    floor = choose_floor()
    if floor is None:
        return
    monster = MONSTERS[floor - 1]

    print()
    scout(floor)
    if not ask_yes_no("\nลงต่อสู้?", "\nFight?"):
        print(get_text("ถอยกลับเมือง", "You head back to town."))
        return

    result = fight(monster, random.Random(), show=True)

    for message in apply_battle(floor, result):
        print(message)


def adventure_stats() -> dict:
    """
    คำนวณสถิติการผจญภัย (ใช้ร่วมกันทั้ง Terminal และ GUI):
    จำนวนชั้นที่ผ่าน อัตราชนะ และฮีโร่ที่โจมตีแรงที่สุด / อึดที่สุด / เลเวลสูงสุด
    """
    log = storage.state["log"]
    party = storage.state["heroes"]
    return {
        "cleared": min(storage.state["floor"] - 1, len(MONSTERS)),
        "rate": log["wins"] / log["battles"] * 100 if log["battles"] else 0,
        "strongest": max(party, key=heroes.hero_attack),
        "toughest": max(party, key=lambda hero: hero["max_hp"]),
        "highest": max(party, key=lambda hero: (hero["level"], hero["xp"])),
        "power": heroes.party_power(),
    }


def adventure_log() -> None:
    """สรุปสถิติการผจญภัย"""
    heading("บันทึกการผจญภัย", "ADVENTURE LOG")
    log = storage.state["log"]
    stats = adventure_stats()
    cleared = stats["cleared"]
    print(get_text(f"ความคืบหน้า: {'■' * cleared}{'□' * (len(MONSTERS) - cleared)}  ผ่านแล้ว {cleared}/{len(MONSTERS)} ชั้น",
                   f"Progress:  {'■' * cleared}{'□' * (len(MONSTERS) - cleared)}  {cleared}/{len(MONSTERS)} floors cleared"))

    rate = stats["rate"]
    print(get_text(f"\nต่อสู้ {log['battles']} ครั้ง  ชนะ {log['wins']}  แพ้ {log['losses']}  (อัตราชนะ {rate:.0f}%)",
                   f"\nBattles {log['battles']}  Wins {log['wins']}  Losses {log['losses']}  (win rate {rate:.0f}%)"))
    print(get_text(f"ทองที่หาได้ {log['gold_earned']}  ใช้ไป {log['gold_spent']}  มีอยู่ {storage.state['gold']}",
                   f"Gold earned {log['gold_earned']}  spent {log['gold_spent']}  current {storage.state['gold']}"))

    strongest, toughest, highest = stats["strongest"], stats["toughest"], stats["highest"]
    print(get_text(f"\nโจมตีแรงที่สุด: {strongest['name']} (ATK {heroes.hero_attack(strongest)})",
                   f"\nStrongest attacker: {strongest['name']} (ATK {heroes.hero_attack(strongest)})"))
    print(get_text(f"อึดที่สุด: {toughest['name']} (HP สูงสุด {toughest['max_hp']})",
                   f"Toughest: {toughest['name']} (max HP {toughest['max_hp']})"))
    print(get_text(f"เลเวลสูงสุด: {highest['name']} (Lv.{highest['level']})",
                   f"Highest level: {highest['name']} (Lv.{highest['level']})"))

    power = stats["power"]
    print(get_text(f"\nพลังรวมของทีม: ATK {power['atk']}  DEF {power['def']}  HP {power['hp']}/{power['max_hp']}",
                   f"\nParty total: ATK {power['atk']}  DEF {power['def']}  HP {power['hp']}/{power['max_hp']}"))

    monster = current_monster()
    if monster is not None:
        chance = win_chance(monster)
        print(get_text(f"ศัตรูถัดไป: {monster['icon']} {tr(monster['name'])}  โอกาสชนะตอนนี้ ~{chance:.0f}%",
                       f"Next enemy: {monster['icon']} {tr(monster['name'])}  current win chance ~{chance:.0f}%"))
