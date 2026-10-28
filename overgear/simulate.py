#!/usr/bin/env python3
"""
Simulate Module - OVERGEAR (ร้านตีอาวุธ)
จำลองเล่นหลายร้อยเกมเพื่อปรับสมดุล เทียบผู้เล่น 2 แบบ (เรียกเฉพาะฟังก์ชัน do_* ไม่มี input/print ของเกม)
 - simple: กดง่ายๆ รับออเดอร์ 2 ใบแรกที่ทำได้ ตีอัตโนมัติ ไม่ลงทุน ไม่ส่งภารกิจ
 - planner: วางแผน เรียงออเดอร์ตามความคุ้ม เล่นมินิเกม ลงทุน ส่งผู้กล้าหาของตำนาน ตีอาวุธให้แชมป์
Balance simulator: plays hundreds of games with two bots and prints the outcome table.

ใช้: python3 simulate.py [จำนวนเกมต่อระดับ]   (ค่าเริ่มต้น 300)
"""

import random
import sys

from data import (DIFFICULTIES, LEGEND_QUESTS, WEAPONS, MATERIALS, CLASSES, FORGE_UPGRADE, APPRENTICE_HIRE,
                  MAX_FORGE_LEVEL, MAX_STOCK, GOAL_DAY, MYTHIC, LEGENDARY, RARE)
import day
import forge
import heroes
import market
import shop
import storage

storage.SAVE_ENABLED = False


# ---------- ตัวช่วยร่วม ----------

def play_manual(mold: str, parts: dict, rng: random.Random) -> dict:
    """ตีด้วยมินิเกมตามท่าที่ suggest_action แนะนำ คืนค่าอาวุธ (หรือ None ถ้าตีไม่ได้)"""
    if forge.do_start_forge(mold, parts, rng):
        return None
    while not forge.forge_done(storage.state["forging"]):
        forge.do_strike(forge.suggest_action(storage.state["forging"]), rng)
    return forge.do_finish_forge(rng)


def buy_list(buy: dict) -> bool:
    """ซื้อของตามรายการ คืนค่า True ถ้าซื้อครบ"""
    return all(not market.do_buy(key, amount) for key, amount in buy.items())


def fulfil(order: dict, accuracy: int, manual: bool, rng: random.Random) -> None:
    """ส่ง/ตีให้ออเดอร์ 1 ใบ ถ้าทำได้วันนี้"""
    state = storage.state
    if order["kind"] == "repair":
        if state["materials"]["iron"] < 1:
            market.do_buy("iron", 1)
        shop.do_repair(order)
        return
    weapon = shop.ready_weapon(order)
    if weapon is None and state["forges_left"] > 0:
        recipe = shop.recommend_recipe(order, accuracy)
        if recipe and buy_list(recipe["buy"]):
            if manual:
                weapon = play_manual(order["type"], recipe["parts"], rng)
            elif not forge.do_auto_forge(order["type"], recipe["parts"], rng):
                weapon = state["weapons"][-1]
    if weapon and not shop.match_order(weapon, order):
        shop.do_deliver(order, weapon)


# ---------- บอทกดง่ายๆ ----------

def simple_turn(rng: random.Random) -> None:
    """รับ 2 ใบแรกที่ทำได้ (ตามลำดับบนกระดาน) ตีอัตโนมัติ ส่งของ วันสุดท้ายตั้งแชมป์คนที่แข็งที่สุด"""
    state = storage.state
    accuracy = forge.auto_accuracy()
    taken = 0
    for order in list(state["board"]):
        if taken >= 2:
            break
        if order["kind"] == "repair" or shop.recommend_recipe(order, accuracy):
            if not shop.do_accept(order):
                taken += 1
    for order in sorted(state["orders"], key=lambda o: o["due"]):
        fulfil(order, accuracy, False, rng)
    if state["day"] == GOAL_DAY and not heroes.champion():
        armed = [h for h in state["heroes"] if heroes.armed(h)]
        if armed:
            heroes.do_set_champion(max(armed, key=heroes.hero_power))


# ---------- บอทวางแผน ----------

LEGENDS = ["star_iron", "ent_heart", "phoenix"]


def planner_invest() -> None:
    """ลงทุนเมื่อเงินเหลือพอ: ลูกมือก่อน แล้วอัปเกรดเตา แม่พิมพ์ และคลัง"""
    state = storage.state
    if not state["apprentice"] and state["gold"] >= APPRENTICE_HIRE + 40 and state["day"] <= 25:
        forge.do_hire()
    level = state["forge_level"]
    if level < MAX_FORGE_LEVEL and state["gold"] >= FORGE_UPGRADE[level + 1] + 50 and state["day"] <= 26:
        forge.do_upgrade_forge()
    for mold in ("spear", "hammer"):
        if mold not in state["molds"] and state["gold"] >= WEAPONS[mold]["mold"] + 80 and state["day"] <= 20:
            forge.do_buy_mold(mold)
    if state["storage"] < 30 and state["gold"] >= market.EXPAND_COST + 150:
        market.do_expand_storage()


def planner_offers() -> None:
    """ซื้อของที่ผู้กล้านำมาขาย: ของตำนานและมิธริลก่อน"""
    state = storage.state
    for offer in sorted(state["offers"], key=lambda o: -MATERIALS[o["material"]]["points"]):
        key = offer["material"]
        wanted = MATERIALS[key]["legend"] or key == "mithril"
        if wanted and state["gold"] >= offer["price"] + 20:
            market.do_buy_offer(offer)


def planner_orders(rng: random.Random) -> None:
    """รับออเดอร์ที่คุ้มที่สุดตามแรงที่เหลือ แล้วตีด้วยมินิเกม"""
    state = storage.state
    accuracy = 8
    capacity = state["forges_left"] + 1 - len(state["orders"])
    for order in shop.sorted_board(accuracy):
        if capacity <= 0:
            break
        if shop.order_worth(order, accuracy) > 0 and not shop.do_accept(order):
            capacity -= 1
    for order in sorted(state["orders"], key=lambda o: o["due"]):
        fulfil(order, accuracy, True, rng)


def best_champion() -> dict:
    """ผู้กล้าที่เหมาะเป็นแชมป์: เลเวลสูงสุดที่ถืออาวุธเรา"""
    armed = [h for h in storage.state["heroes"] if h["weapon"]]
    return max(armed, key=lambda h: (h["level"], heroes.hero_power(h))) if armed else None


def champion_mold(hero: dict) -> str:
    """แบบอาวุธที่แชมป์ชอบและเรามีแม่พิมพ์"""
    for mold in CLASSES[hero["class"]]["likes"]:
        if mold in storage.state["molds"]:
            return mold
    return "sword"


def planner_champion(rng: random.Random) -> None:
    """ตั้งแชมป์ ส่งผู้กล้าหาของตำนาน และตีอาวุธเกรดสูงสุดที่ทำได้ให้แชมป์"""
    state = storage.state
    champ = heroes.champion()
    if champ is None or state["day"] % 5 == 0:
        pick = best_champion()
        if pick:
            heroes.do_set_champion(pick)
            champ = pick
    # ส่งผู้กล้าที่ไม่ใช่แชมป์และโอกาสชนะสูงไปหาวัตถุดิบตำนานที่ยังขาด
    for key, quest in LEGEND_QUESTS.items():
        if state["materials"][quest["material"]] > 0 or any(h["task"] == key for h in state["heroes"]):
            continue
        for hero in state["heroes"]:
            if hero is champ or hero["task"] != "hunt" or not heroes.armed(hero) or hero["rest"]:
                continue
            if heroes.win_chance(heroes.hero_power(hero), heroes.threat_of(quest["threat"])) >= 0.75:
                heroes.do_set_task(hero, key)
                break
    if champ is None:
        return
    # ช่วงท้ายให้แชมป์พักเพื่อไม่ให้ตายก่อนวันที่ 30
    champ["task"] = "rest" if state["day"] >= 25 else champ["task"]
    if state["forges_left"] <= 0 or len(state["weapons"]) >= MAX_STOCK:
        return
    have = [key for key in LEGENDS if state["materials"][key] > 0]
    current = champ["weapon"]["grade"] if champ["weapon"] else -1
    mold = champion_mold(champ)
    parts = None
    if len(have) == 3 and state["forge_level"] >= MAX_FORGE_LEVEL and current < MYTHIC:
        parts = {"blade": "star_iron", "handle": "ent_heart", "gem": "phoenix"}
    elif have and current < LEGENDARY and state["day"] >= 18:
        blade = "star_iron" if "star_iron" in have else "mithril"
        if blade == "mithril" and state["materials"]["mithril"] < WEAPONS[mold]["blade"]:
            if not market.available("mithril"):
                return
            market.do_buy("mithril", WEAPONS[mold]["blade"] - state["materials"]["mithril"])
        handle = "ent_heart" if "ent_heart" in have else "ironwood"
        gem = "phoenix" if "phoenix" in have else "ruby"
        for key in (handle, gem):
            if state["materials"][key] < 1:
                market.do_buy(key, 1)
        parts = {"blade": blade, "handle": handle, "gem": gem}
    if parts and not forge.check_forge(mold, parts):
        weapon = play_manual(mold, parts, rng)
        if weapon and weapon["grade"] > current:
            heroes.do_give_weapon(champ, weapon)


def planner_spare(rng: random.Random) -> None:
    """แรงที่เหลือ: ติดอาวุธให้ผู้กล้าที่ไม่มีอาวุธ ช่วงท้ายตีอาวุธเงินบริจาคทหาร"""
    state = storage.state
    for hero in state["heroes"]:
        if not hero["weapon"] and state["weapons"]:
            heroes.do_give_weapon(hero, max(state["weapons"], key=lambda w: w["power"]))
    if state["day"] < 18:
        return
    while state["forges_left"] > 0 and len(state["weapons"]) < MAX_STOCK and state["gold"] >= 80:
        parts = {"blade": "silver", "handle": "ironwood", "gem": "runestone"}
        if shop.shopping_list("sword", parts) is None or not buy_list(shop.shopping_list("sword", parts)):
            break
        weapon = play_manual("sword", parts, rng)
        if weapon is None:
            break
        shop.do_donate(weapon)


def planner_turn(rng: random.Random) -> None:
    """1 วันของบอทวางแผน"""
    planner_offers()
    planner_invest()
    planner_champion(rng)
    planner_orders(rng)
    planner_spare(rng)
    for weapon in list(storage.state["weapons"]):
        if storage.state["day"] >= 26 and weapon["grade"] >= RARE:
            shop.do_donate(weapon)


# ---------- ลูปจำลอง ----------

def play_game(level: str, bot, seed: int) -> dict:
    """เล่น 1 เกมจนจบด้วยบอทที่กำหนด คืนค่าผลฉากจบ"""
    rng = random.Random(seed)
    storage.new_game(level, rng)
    while storage.state["status"] == "playing":
        bot(rng)
        day.do_end_day(rng)
    ending = dict(storage.state["ending"])
    ending["deaths"] = storage.state["log"]["deaths"]
    ending["gold"] = storage.state["gold"]
    ending["best"] = storage.state["log"]["best"]["grade"] if storage.state["log"]["best"] else -1
    return ending


def summarize(results: list) -> dict:
    """รวมผล: % ของแต่ละจำนวนดาว, % ปราบมังกร, ค่าเฉลี่ยผู้กล้าตายและเงิน, % ที่ตีได้ตำนาน/เทพนิยาย"""
    total = len(results)
    stars = [sum(1 for r in results if r["stars"] == s) / total for s in range(4)]
    return {"stars": stars, "slayer": sum(r["slayer"] for r in results) / total,
            "deaths": sum(r["deaths"] for r in results) / total, "gold": sum(r["gold"] for r in results) / total,
            "legendary": sum(1 for r in results if r["best"] >= LEGENDARY) / total,
            "mythic": sum(1 for r in results if r["best"] >= MYTHIC) / total,
            "ratio": sum(r["ratio"] for r in results) / total}


def main() -> None:
    """จำลองทุกระดับ × บอท 2 แบบ แล้วพิมพ์ตาราง Markdown"""
    games = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 300
    bots = {"simple": simple_turn, "planner": planner_turn}
    print("| level | bot | 0* | 1* | 2* | 3* | slayer | defense/dragon | hero deaths | gold | legendary | mythic |")
    print("| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for level in DIFFICULTIES:
        for name, bot in bots.items():
            results = [play_game(level, bot, seed) for seed in range(games)]
            s = summarize(results)
            stars = " | ".join(f"{p:.0%}" for p in s["stars"])
            print(f"| {level} | {name} | {stars} | {s['slayer']:.0%} | {s['ratio']:.2f} | {s['deaths']:.1f} | "
                  f"{s['gold']:.0f} | {s['legendary']:.0%} | {s['mythic']:.0%} |")


if __name__ == "__main__":
    main()
