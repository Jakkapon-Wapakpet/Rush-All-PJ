#!/usr/bin/env python3
"""
Day Module - OVERGEAR (ร้านตีอาวุธ)
เริ่มเกม เริ่มเช้าวันใหม่ จบวัน (ออเดอร์หมดเวลา ผู้กล้าออกล่า ค่าใช้จ่าย) และฉากจบมังกรบุกวันที่ 30
Game start, morning, end of day, and the day-30 dragon finale.
"""

import random

from language import get_text, clear_screen
from data import (GOAL_DAY, NEWS, GRADES, MYTHIC, GARRISON_RATE, CHAMPION_RATE, HERO_RATE, MYTHIC_CHAMPION, ENDINGS,
                  APPRENTICE_WAGE, tr)
from ui import heading, ask_yes_no, bar
import forge
import heroes
import market
import shop
import storage


# ---------- เริ่มเกม / เริ่มวัน ----------

def start_game(rng: random.Random = None) -> None:
    """เกมใหม่: ผู้กล้า 2 คนแรก ข่าว ราคา และกระดานวันแรก"""
    rng = rng or random.Random()
    state = storage.state
    state["heroes"] = [heroes.make_hero(rng, 1)]
    state["heroes"].append(heroes.make_hero(rng, 2))
    state["news"] = "calm"
    state["rumor"] = market.roll_news(rng)
    market.make_prices(rng)
    state["forges_left"] = forge.forges_per_day()
    shop.fill_board(rng)


def start_morning(rng: random.Random, report: list) -> None:
    """เช้าวันใหม่: ข่าวลือกลายเป็นข่าวจริง สุ่มข่าวลือใหม่ ราคาใหม่ ผู้กล้ามา/ไป และกระดานใหม่"""
    state = storage.state
    state["news"] = state["rumor"]
    state["rumor"] = market.roll_news(rng)
    market.make_prices(rng)
    state["forges_left"] = forge.forges_per_day()
    heroes.morning_heroes(rng, report)
    shop.fill_board(rng)


def daily_cost() -> int:
    """ค่าใช้จ่ายรายวัน = ค่าถ่าน/ค่าเช่าตามระดับความยาก + ค่าจ้างลูกมือ"""
    return storage.setting("upkeep") + (APPRENTICE_WAGE if storage.state["apprentice"] else 0)


def pay_upkeep(report: list) -> None:
    """จ่ายค่าใช้จ่ายรายวัน ถ้าเงินไม่พอ: ค้างจ่าย เสียชื่อเสียง (และลูกมือลาออก)"""
    state = storage.state
    cost = daily_cost()
    if state["gold"] >= cost:
        storage.pay(cost)
        return
    storage.pay(state["gold"])
    storage.add_fame(-2)
    report.append(get_text("💸 เงินไม่พอจ่ายค่าเช่า/ค่าถ่าน! ชื่อเสียง -2", "💸 Couldn't pay rent and coal! Fame -2"))
    if state["apprentice"]:
        state["apprentice"] = False
        report.append(get_text("🧑‍🔧 ลูกมือไม่ได้ค่าจ้าง เลยลาออกไป", "🧑‍🔧 Your unpaid apprentice quit."))


# ---------- ฉากจบ: มังกรบุก ----------

def defense_breakdown() -> dict:
    """
    พลังป้องกันหมู่บ้าน = อาวุธในคลังทหาร × 0.4 + ผู้กล้าที่ถืออาวุธเรา + แชมป์ × 2
    (แชมป์ถืออาวุธเทพนิยาย ได้อีก ×2)
    """
    state = storage.state
    garrison = round(sum(weapon["power"] for weapon in state["garrison"]) * GARRISON_RATE)
    champ = heroes.champion()
    champ_power = 0
    mythic = False
    if champ and heroes.armed(champ):
        mythic = champ["weapon"]["grade"] == MYTHIC
        champ_power = round(heroes.hero_power(champ) * CHAMPION_RATE * (MYTHIC_CHAMPION if mythic else 1))
    others = sum(heroes.hero_power(h) for h in state["heroes"] if heroes.armed(h) and h is not champ)
    hero_part = round(others * HERO_RATE)
    return {"garrison": garrison, "heroes": hero_part, "champion": champ_power, "mythic": mythic,
            "total": garrison + hero_part + champ_power}


def dragon_power() -> int:
    """พลังมังกรตามระดับความยาก"""
    return storage.setting("dragon")


def ending_grade(ratio: float) -> tuple:
    """เทียบพลังป้องกัน/พลังมังกรกับเกณฑ์ฉากจบ คืนค่า (ดาว, ชื่อฉากจบ)"""
    for need, stars, title in ENDINGS:
        if ratio >= need:
            return stars, title
    return 0, ENDINGS[-1][2]


def do_final_battle(rng: random.Random) -> dict:
    """มังกรบุก! (พลังมังกรแกว่ง ±10%) คืนผลฉากจบและตั้งสถานะเกม"""
    state = storage.state
    defense = defense_breakdown()
    dragon = round(dragon_power() * rng.uniform(0.9, 1.1))
    ratio = defense["total"] / dragon
    stars, title = ending_grade(ratio)
    slayer = defense["mythic"] and ratio >= 1.0
    state["status"] = "won" if stars > 0 else "lost"
    ending = {"defense": defense["total"], "dragon": dragon, "ratio": round(ratio, 2), "stars": stars,
              "title": title, "slayer": slayer, "parts": defense}
    state["ending"] = ending
    storage.record_result(ending)
    return ending


def ending_lines(ending: dict) -> list:
    """ข้อความเล่าฉากจบ"""
    parts = ending["parts"]
    lines = [get_text("🐉 รุ่งเช้าวันที่ 30 เงามังกรบดบังดวงอาทิตย์...", "🐉 At dawn of day 30, a dragon blots out the sun..."),
             get_text(f"   🛡 ทหารรักษาเมือง {parts['garrison']}   ⚔ ผู้กล้า {parts['heroes']}   👑 แชมป์ {parts['champion']}",
                      f"   🛡 Garrison {parts['garrison']}   ⚔ Heroes {parts['heroes']}   👑 Champion {parts['champion']}"),
             get_text(f"   พลังป้องกัน {ending['defense']} vs พลังมังกร {ending['dragon']}",
                      f"   Defense {ending['defense']} vs dragon {ending['dragon']}"),
             f"   [{bar(min(ending['defense'], ending['dragon']), ending['dragon'], 30)}] {ending['ratio']:.0%}",
             "",
             "   " + "⭐" * ending["stars"] + "☆" * (3 - ending["stars"]) + "  " + tr(ending["title"])]
    if ending["slayer"]:
        lines.append(get_text("   🔴🐉 แชมป์ฟันมังกรขาดด้วยอาวุธเทพนิยาย! ชื่อร้านของคุณจะถูกขับขานไปอีกร้อยปี!",
                              "   🔴🐉 The champion slew the dragon with a MYTHIC blade! Bards will sing of your forge!"))
    elif parts["mythic"]:
        lines.append(get_text("   แชมป์ถืออาวุธเทพนิยาย แต่หมู่บ้านต้านไม่พอจะปราบมังกร",
                              "   The champion bore a Mythic weapon, but the village wasn't strong enough."))
    return lines


# ---------- จบวัน ----------

def do_end_day(rng: random.Random = None) -> dict:
    """
    จบวันและคำนวณผลทั้งหมด (ใช้ร่วมกันทั้ง Terminal และ GUI / สคริปต์จำลอง)
    คืนค่า {"lines": [ข้อความเล่าเหตุการณ์], "status": ..., "ending": ผลฉากจบหรือ None}
    """
    rng = rng or random.Random()
    state = storage.state
    report = []

    # เหล็กที่ค้างบนทั่งต้องตีให้จบก่อนปิดร้าน
    if state["forging"]:
        weapon = forge.do_finish_forge(rng)
        report.append(get_text("⚒ ตีชิ้นที่ค้างให้จบ: ", "⚒ Finished the piece on the anvil: ") + forge.weapon_label(weapon))

    shop.expire_orders(report)
    heroes.night_hunts(rng, report)
    pay_upkeep(report)
    state["log"]["days"].append({"day": state["day"], "gold": state["gold"], "fame": state["fame"],
                                 "defense": defense_breakdown()["total"], "news": state["news"]})

    ending = None
    if state["day"] >= GOAL_DAY:
        ending = do_final_battle(rng)
        report.extend(ending_lines(ending))
    else:
        state["day"] += 1
        start_morning(rng, report)
    storage.save_game()
    return {"lines": report, "status": state["status"], "ending": ending}


def end_day() -> None:
    """เมนู Terminal: ยืนยัน (ถ้ายังมีงานค้าง) แล้วจบวันและแสดงรายงาน"""
    state = storage.state
    due_today = [o for o in state["orders"] if o["due"] <= state["day"]]
    if due_today and not ask_yes_no(f"มีออเดอร์ครบกำหนดวันนี้ {len(due_today)} ใบที่ยังไม่ส่ง (จะเสียชื่อเสียง) จบวันเลย?",
                                    f"{len(due_today)} order(s) due today aren't delivered (fame loss). End day anyway?"):
        return
    if state["forges_left"] > 0 and not due_today and \
            not ask_yes_no(f"ยังตีได้อีก {state['forges_left']} ครั้ง จบวันเลย?",
                           f"You can still forge {state['forges_left']} time(s). End the day?"):
        return
    if state["day"] >= GOAL_DAY and not heroes.champion() and \
            not ask_yes_no("ยังไม่ได้แต่งตั้งแชมป์สู้มังกร! สู้เลย?", "No champion appointed for the dragon! Fight anyway?"):
        return
    clear_screen()
    heading(f"คืนที่ {state['day']}", f"NIGHT {state['day']}")
    result = do_end_day()
    for line in result["lines"] or [get_text("คืนนี้เงียบสงบ", "A quiet night.")]:
        print(" " + line)
    if result["status"] == "playing":
        news = NEWS[state["news"]]
        print(get_text(f"\n☀ เช้าวันที่ {state['day']}: {news['icon']} {tr(news['name'])} - {tr(news['about'])}",
                       f"\n☀ Morning of day {state['day']}: {news['icon']} {tr(news['name'])} - {tr(news['about'])}"))
        if state["offers"]:
            print(get_text(f"   ⚔ มีผู้กล้านำของมาขาย {len(state['offers'])} ชิ้นที่ตลาด (วันนี้วันเดียว)",
                           f"   ⚔ {len(state['offers'])} hero loot offer(s) at the market today"))
    else:
        print(get_text("\n🏁 เกมจบแล้ว! ดูสรุปได้ที่ 🏆 ผลเกมที่ผ่านมา", "\n🏁 Game over! See 🏆 Past Results."))


# ---------- สถิติร้าน ----------

def shop_stats() -> dict:
    """สรุปสถิติของร้าน: อัตราผู้กล้ารอด เกรดที่ตีได้ เงินสูงสุด และวันที่เงินมากที่สุด"""
    log = storage.state["log"]
    days = log["days"]
    richest = max(days, key=lambda d: d["gold"]) if days else None
    return {"forged": log["forged"], "grades": list(log["grades"]), "crits": log["crits"],
            "delivered": log["delivered"], "late": log["late"], "repairs": log["repairs"],
            "win_rate": log["wins"] / log["hunts"] if log["hunts"] else 0, "deaths": log["deaths"],
            "legends": log["legends"], "earned": log["earned"], "spent": log["spent"],
            "richest": richest, "best": log["best"]}


def shop_log() -> None:
    """แสดงบันทึกร้าน (สถิติ + กราฟเงินและพลังป้องกันรายวัน)"""
    state = storage.state
    stats = shop_stats()
    heading("บันทึกร้าน", "SHOP LOG")
    grades = "  ".join(f"{GRADES[i]['icon']}{count}" for i, count in enumerate(stats["grades"]))
    print(get_text(f" ตีอาวุธ {stats['forged']} ชิ้น: {grades}   ตีวิกฤต {stats['crits']} ครั้ง",
                   f" Forged {stats['forged']}: {grades}   critical forges {stats['crits']}"))
    print(get_text(f" ส่งของ {stats['delivered']}  ซ่อม {stats['repairs']}  ส่งไม่ทัน {stats['late']}",
                   f" Delivered {stats['delivered']}  repaired {stats['repairs']}  late {stats['late']}"))
    print(get_text(f" ผู้กล้าชนะ {stats['win_rate']:.0%} ของการล่า  ตาย {stats['deaths']} คน  ได้ของตำนาน {stats['legends']} ชิ้น",
                   f" Heroes won {stats['win_rate']:.0%} of hunts  died {stats['deaths']}  legend materials {stats['legends']}"))
    print(get_text(f" รายรับรวม {stats['earned']}  รายจ่ายรวม {stats['spent']}",
                   f" Total income {stats['earned']}  total spending {stats['spent']}"))
    if stats["best"]:
        best = stats["best"]
        print(get_text(f" อาวุธดีที่สุด: {forge.WEAPONS[best['type']]['icon']} {GRADES[best['grade']]['icon']}"
                       f"{tr(GRADES[best['grade']]['name'])} พลัง {best['power']} (วันที่ {best['day']})",
                       f" Best weapon: {forge.WEAPONS[best['type']]['icon']} {GRADES[best['grade']]['icon']}"
                       f"{tr(GRADES[best['grade']]['name'])} PWR {best['power']} (day {best['day']})"))
    days = state["log"]["days"][-10:]
    if days:
        top = max(max(d["gold"] for d in days), 1)
        print(get_text("\n 💰 เงินตอนจบวัน (10 วันล่าสุด):", "\n 💰 Gold at end of day (last 10):"))
        for entry in days:
            print(f"   {entry['day']:>2} {bar(entry['gold'], top, 20)} {entry['gold']}")
    defense = defense_breakdown()
    print(get_text(f"\n 🐉 พลังป้องกันตอนนี้ {defense['total']} vs มังกร ~{dragon_power()}",
                   f"\n 🐉 Defense now {defense['total']} vs dragon ~{dragon_power()}"))
