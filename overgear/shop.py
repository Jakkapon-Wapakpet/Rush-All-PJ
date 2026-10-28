#!/usr/bin/env python3
"""
Shop Module - OVERGEAR (ร้านตีอาวุธ)
กระดานออเดอร์และลูกค้า: สร้างออเดอร์ รับ ส่ง ซ่อม ยกเลิก ตรวจสเปก แนะนำสูตรกำไรสูงสุด
เรียงออเดอร์ตามความคุ้ม คาดการณ์เงินสด และขาย/บริจาคอาวุธจากชั้นวาง
Order board and customers: create, accept, deliver, repair, cancel, spec checks, best-recipe advice.
"""

import random

from language import get_text, clear_screen, pause
from data import (CUSTOMERS, CUSTOMER_NAMES, WEAPONS, MATERIALS, GRADES, CLASSES, BOARD_SIZE, MAX_ORDERS, LATE_FAME,
                  CANCEL_FAME, WALKIN_RATE, RIVAL_IMMUNE_FAME, COMMON, EPIC, LEGENDARY, tr)
from ui import heading, choose_from_list, ask_yes_no, show_error
import forge
import heroes
import market
import storage


# ---------- สร้างออเดอร์ ----------

def pay_factor(mold: str) -> float:
    """ผลของข่าวต่อค่าจ้าง: อาวุธที่คนต้องการจ่ายแพงขึ้น, คู่แข่งตัดราคาทำให้ลูกค้าต่อราคา (ชื่อเสียงสูงไม่โดน)"""
    news_pay = market.news_value("pay", 1.0)
    demand = market.news_value("demand")
    if news_pay < 1 and storage.state["fame"] >= RIVAL_IMMUNE_FAME:
        return 1.0
    if demand and demand != mold:
        return 1.0
    return news_pay


def order_pay(mold: str, grade: int, kind: str, specs: int, rng: random.Random) -> int:
    """ค่าจ้าง = มูลค่าแม่พิมพ์ × ตัวคูณเกรด × ตัวคูณลูกค้า × สุ่ม × ข่าว + 10% ต่อสเปกพิเศษ"""
    base = WEAPONS[mold]["value"] * GRADES[grade]["price"] * CUSTOMERS[kind]["pay"]
    return max(5, round(base * rng.uniform(0.9, 1.25) * pay_factor(mold) * (1 + 0.1 * specs)))


def pick_grade(kind: str, rng: random.Random) -> int:
    """เกรดขั้นต่ำของออเดอร์: ตามชนิดลูกค้า และยิ่งหลายวันลูกค้ายิ่งต้องการของดีขึ้น"""
    day = storage.state["day"]
    grade = CUSTOMERS[kind]["grade"]
    if kind in ("villager", "merchant", "guard") and day >= 10 and rng.random() < 0.35:
        grade += 1
    if kind == "guard" and day >= 20 and rng.random() < 0.3:
        grade += 1
    if kind == "noble" and day >= 15 and rng.random() < 0.25:
        grade = LEGENDARY
    return min(grade, LEGENDARY)


def make_order(kind: str, rng: random.Random, hero: dict = None) -> dict:
    """สร้างออเดอร์ 1 ใบ (สเปก: แบบอาวุธ เกรดขั้นต่ำ คมขั้นต่ำ น้ำหนักไม่เกิน กำหนดส่ง ค่าจ้าง)"""
    state = storage.state
    picky = storage.setting("picky")
    if hero:
        # ผู้กล้าส่วนใหญ่ขอแบบที่ร้านทำได้ แต่บางครั้งก็ขอแบบที่ต้องซื้อแม่พิมพ์ก่อน
        likes = CLASSES[hero["class"]]["likes"]
        owned = [mold for mold in likes if mold in state["molds"]]
        mold = rng.choice(owned if owned and rng.random() < 0.75 else likes)
        grade = min(EPIC, COMMON + (hero["level"] - 1) // 3)
        customer = dict(hero["name"])
    else:
        types = CUSTOMERS[kind]["types"]
        demand = market.news_value("demand")
        if demand in types and rng.random() < 0.5:
            mold = demand
        else:
            mold = rng.choice(types)
        grade = pick_grade(kind, rng)
        customer = dict(rng.choice(CUSTOMER_NAMES[kind]))
    base = WEAPONS[mold]
    min_sharp, max_weight = 0, 0
    if kind != "merchant" and rng.random() < 0.45 + 0.2 * picky:
        min_sharp = base["sharp"] + rng.randint(1, 3) + picky + (2 if grade >= EPIC else 0)
    if kind != "merchant" and rng.random() < 0.25 + 0.2 * picky:
        max_weight = max(1, base["weight"] + rng.choice([0, 1]) - picky)
    specs = (1 if min_sharp else 0) + (1 if max_weight else 0)
    due = state["day"] + rng.randint(3, 5) if kind == "noble" else state["day"] + rng.randint(2, 4)
    fame = CUSTOMERS[kind]["fame"] + (1 if grade >= EPIC else 0)
    return {"id": storage.next_id(), "kind": kind, "customer": customer, "hero": hero["id"] if hero else None,
            "type": mold, "min_grade": grade, "min_sharp": min_sharp, "max_weight": max_weight,
            "pay": order_pay(mold, grade, kind, specs, rng), "fame": fame, "due": due}


def make_repair(hero: dict) -> dict:
    """คำขอซ่อมอาวุธที่หักของผู้กล้า (ค่าซ่อม 35% ของมูลค่า)"""
    weapon = hero["weapon"]
    return {"id": storage.next_id(), "kind": "repair", "customer": dict(hero["name"]), "hero": hero["id"],
            "type": weapon["type"], "min_grade": weapon["grade"], "min_sharp": 0, "max_weight": 0,
            "pay": max(8, round(weapon["value"] * CUSTOMERS["repair"]["pay"])), "fame": CUSTOMERS["repair"]["fame"],
            "due": storage.state["day"] + 2}


def fill_board(rng: random.Random) -> None:
    """
    ตอนเช้าสร้างกระดานใหม่: ผู้กล้าที่ไม่มีอาวุธ/อาวุธหักมาก่อน (ถ้ายังไม่มีออเดอร์ค้าง)
    แล้วสุ่มลูกค้าทั่วไปจนครบ 4 คน (ขุนนาง VIP มาเฉพาะเมื่อชื่อเสียงถึง)
    """
    state = storage.state
    board = []
    waiting = {order["hero"] for order in state["orders"] if order.get("hero")}
    for hero in state["heroes"]:
        if len(board) >= BOARD_SIZE - 1 or hero["id"] in waiting or heroes.armed(hero):
            continue
        board.append(make_repair(hero) if hero["weapon"] else make_order("hero", rng, hero))
    kinds = [kind for kind, info in CUSTOMERS.items() if info["weight"] > 0]
    if state["fame"] < storage.setting("vip_fame"):
        kinds.remove("noble")
    weights = [CUSTOMERS[kind]["weight"] for kind in kinds]
    while len(board) < BOARD_SIZE:
        board.append(make_order(rng.choices(kinds, weights=weights)[0], rng))
    state["board"] = board


# ---------- ตรวจสเปกและส่งของ ----------

def spec_text(order: dict) -> str:
    """สเปกของออเดอร์เป็นข้อความสั้น"""
    grade = GRADES[order["min_grade"]]
    text = f"{WEAPONS[order['type']]['icon']} {tr(WEAPONS[order['type']]['name'])} {grade['icon']}{tr(grade['name'])}+"
    if order["min_sharp"]:
        text += get_text(f" คม {order['min_sharp']}+", f" sharp {order['min_sharp']}+")
    if order["max_weight"]:
        text += get_text(f" หนัก≤{order['max_weight']}", f" weight≤{order['max_weight']}")
    return text


def order_line(order: dict) -> str:
    """ออเดอร์ 1 บรรทัด: ลูกค้า สเปก ค่าจ้าง กำหนดส่ง"""
    info = CUSTOMERS[order["kind"]]
    left = order["due"] - storage.state["day"]
    due = get_text("ส่งวันนี้!", "due TODAY!") if left == 0 else get_text(f"อีก {left} วัน", f"{left} days")
    if order["kind"] == "repair":
        what = get_text(f"ซ่อม {WEAPONS[order['type']]['icon']} {tr(WEAPONS[order['type']]['name'])} (เหล็ก 1)",
                        f"Repair {WEAPONS[order['type']]['icon']} {tr(WEAPONS[order['type']]['name'])} (1 iron)")
    else:
        what = spec_text(order)
    return (f"{info['icon']} {tr(order['customer'])} [{tr(info['name'])}] {what} → "
            f"💰{order['pay']} ⭐+{order['fame']}  ({due})")


def match_order(weapon: dict, order: dict) -> str:
    """ตรวจว่าอาวุธตรงสเปกออเดอร์ไหม คืนเหตุผลที่ไม่ผ่าน หรือ "" ถ้าผ่าน"""
    if weapon["type"] != order["type"]:
        return get_text(f"ลูกค้าต้องการ{tr(WEAPONS[order['type']]['name'])}",
                        f"The customer wants a {tr(WEAPONS[order['type']]['name'])}.")
    if weapon["grade"] < order["min_grade"]:
        return get_text(f"เกรดไม่ถึง (ต้อง{tr(GRADES[order['min_grade']]['name'])}ขึ้นไป)",
                        f"Grade too low (needs {tr(GRADES[order['min_grade']]['name'])}+).")
    if order["min_sharp"] and weapon["sharp"] < order["min_sharp"]:
        return get_text(f"คมไม่พอ (ต้อง {order['min_sharp']} ได้ {weapon['sharp']})",
                        f"Not sharp enough (needs {order['min_sharp']}, has {weapon['sharp']}).")
    if order["max_weight"] and weapon["weight"] > order["max_weight"]:
        return get_text(f"หนักเกิน (ไม่เกิน {order['max_weight']} แต่หนัก {weapon['weight']})",
                        f"Too heavy (max {order['max_weight']}, is {weapon['weight']}).")
    return ""


def do_accept(order: dict) -> str:
    """รับออเดอร์จากกระดาน (รับค้างได้ไม่เกิน 5 ใบ)"""
    state = storage.state
    if order not in state["board"]:
        return get_text("ออเดอร์นี้ไม่อยู่บนกระดานแล้ว", "That order is no longer on the board.")
    if len(state["orders"]) >= MAX_ORDERS:
        return get_text(f"รับออเดอร์ค้างได้ไม่เกิน {MAX_ORDERS} ใบ", f"You can hold at most {MAX_ORDERS} orders.")
    state["board"].remove(order)
    state["orders"].append(order)
    storage.save_game()
    return ""


def do_deliver(order: dict, weapon: dict) -> str:
    """
    ส่งอาวุธตามออเดอร์: ได้เงิน + ชื่อเสียง (เกรดเกินสเปก ได้โบนัสขั้นละ +10% และ +1 ชื่อเสียง)
    ผู้กล้า -> ถืออาวุธนี้ออกล่า, ทหาร -> เข้าคลังอาวุธป้องกันเมือง
    """
    state = storage.state
    if order not in state["orders"]:
        return get_text("ยังไม่ได้รับออเดอร์นี้", "You haven't accepted that order.")
    if order["kind"] == "repair":
        return get_text("ออเดอร์ซ่อมต้องใช้เมนูซ่อม", "Use repair for repair orders.")
    if weapon not in state["weapons"]:
        return get_text("ไม่มีอาวุธชิ้นนี้บนชั้นวาง", "That weapon is not on the rack.")
    error = match_order(weapon, order)
    if error:
        return error
    hero = heroes.find_hero(order["hero"]) if order["hero"] else None
    if order["kind"] == "hero" and hero is None:
        state["orders"].remove(order)
        return get_text("ผู้กล้าคนนี้ไม่อยู่แล้ว ออเดอร์ถูกยกเลิก", "That hero is gone; the order was dropped.")

    extra = weapon["grade"] - order["min_grade"]
    state["weapons"].remove(weapon)
    state["orders"].remove(order)
    storage.earn(round(order["pay"] * (1 + 0.1 * extra)))
    storage.add_fame(order["fame"] + extra)
    state["log"]["delivered"] += 1
    if hero:
        hero["weapon"] = weapon
        hero["idle"] = 0
    elif order["kind"] == "guard":
        state["garrison"].append(weapon)
    storage.save_game()
    return ""


def do_repair(order: dict) -> str:
    """ซ่อมอาวุธของผู้กล้า: ใช้เหล็ก 1 ชิ้น + แรงตี 1 ครั้ง ความทนทานกลับมาเต็ม"""
    state = storage.state
    if order not in state["orders"] or order["kind"] != "repair":
        return get_text("ไม่ใช่ออเดอร์ซ่อมที่รับไว้", "That is not an accepted repair order.")
    hero = heroes.find_hero(order["hero"])
    if hero is None or not hero["weapon"]:
        state["orders"].remove(order)
        return get_text("เจ้าของอาวุธไม่อยู่แล้ว ออเดอร์ถูกยกเลิก", "The owner is gone; the order was dropped.")
    if state["forges_left"] <= 0:
        return get_text("วันนี้ตีครบแล้ว จบวันก่อน", "No forging left today.")
    error = storage.check_materials({"iron": 1})
    if error:
        return error
    state["materials"]["iron"] -= 1
    state["forges_left"] -= 1
    hero["weapon"]["dur"] = hero["weapon"]["max_dur"]
    hero["idle"] = 0
    state["orders"].remove(order)
    storage.earn(order["pay"])
    storage.add_fame(order["fame"])
    state["log"]["repairs"] += 1
    storage.save_game()
    return ""


def do_cancel(order: dict) -> str:
    """ยกเลิกออเดอร์ที่รับไว้ (ลบออเดอร์ เสียชื่อเสียง)"""
    state = storage.state
    if order not in state["orders"]:
        return get_text("ยังไม่ได้รับออเดอร์นี้", "You haven't accepted that order.")
    state["orders"].remove(order)
    storage.add_fame(-CANCEL_FAME)
    state["log"]["cancelled"] += 1
    storage.save_game()
    return ""


def expire_orders(report: list) -> None:
    """จบวัน: ออเดอร์ที่ถึงกำหนดแต่ยังไม่ส่ง = ส่งช้า เสียชื่อเสียง"""
    state = storage.state
    for order in list(state["orders"]):
        if order["due"] <= state["day"]:
            state["orders"].remove(order)
            storage.add_fame(-LATE_FAME)
            state["log"]["late"] += 1
            report.append(get_text(f"⌛ ส่งไม่ทัน: {tr(order['customer'])} ไม่พอใจ (ชื่อเสียง -{LATE_FAME})",
                                   f"⌛ Missed deadline: {tr(order['customer'])} is upset (fame -{LATE_FAME})"))


# ---------- ขาย / บริจาคอาวุธจากชั้นวาง ----------

def walkin_price(weapon: dict) -> int:
    """พ่อค้าเร่รับซื้ออาวุธ 60% ของมูลค่า"""
    return max(1, round(weapon["value"] * WALKIN_RATE))


def do_sell_weapon(weapon: dict) -> str:
    """ขายอาวุธบนชั้นวางให้พ่อค้าเร่ (ลบออกจากชั้นวาง)"""
    state = storage.state
    if weapon not in state["weapons"]:
        return get_text("ไม่มีอาวุธชิ้นนี้บนชั้นวาง", "That weapon is not on the rack.")
    state["weapons"].remove(weapon)
    storage.earn(walkin_price(weapon))
    storage.save_game()
    return ""


def do_donate(weapon: dict) -> str:
    """บริจาคอาวุธให้ทหารรักษาเมือง (เพิ่มพลังป้องกันตอนมังกรบุก ชื่อเสียง +1)"""
    state = storage.state
    if weapon not in state["weapons"]:
        return get_text("ไม่มีอาวุธชิ้นนี้บนชั้นวาง", "That weapon is not on the rack.")
    state["weapons"].remove(weapon)
    state["garrison"].append(weapon)
    storage.add_fame(1)
    storage.save_game()
    return ""


# ---------- อัลกอริทึม: แนะนำสูตร เรียงความคุ้ม คาดการณ์เงินสด ----------

def unit_value(key: str) -> int:
    """มูลค่าต่อชิ้นที่ใช้คิดต้นทุน: ราคาตลาดวันนี้ (ของตำนานคิดราคาอ้างอิงสูง เพราะหายาก)"""
    return market.price_today(key)


def recipe_options(mold: str) -> list:
    """สูตรที่เป็นไปได้ทั้งหมดของอาวุธแบบนี้ (ใบมีด × ด้าม × เครื่องประดับหรือไม่ใส่)"""
    blades = [key for key, info in MATERIALS.items() if info["slot"] == "blade"]
    handles = [key for key, info in MATERIALS.items() if info["slot"] == "handle"]
    gems = [None] + [key for key, info in MATERIALS.items() if info["slot"] == "gem"]
    return [{"blade": b, "handle": h, "gem": g} for b in blades for h in handles for g in gems]


def shopping_list(mold: str, parts: dict) -> dict:
    """วัตถุดิบที่ยังขาดต้องซื้อเพิ่ม คืนค่า None ถ้าของที่ขาดไม่มีขายวันนี้"""
    state = storage.state
    buy = {}
    for key, amount in forge.materials_for(mold, parts).items():
        missing = amount - state["materials"][key]
        if missing > 0:
            if not market.available(key):
                return None
            buy[key] = missing
    return buy


def recommend_recipe(order: dict, accuracy: int) -> dict:
    """
    แนะนำสูตรกำไรสูงสุดสำหรับออเดอร์: ลองทุกสูตร เก็บเฉพาะที่ (1) มีของหรือซื้อได้วันนี้และเงินพอ
    (2) เกรดที่คาดว่าจะได้ถึงสเปก (3) คม/น้ำหนักผ่าน แล้วเลือกต้นทุนต่ำสุด (เท่ากันเลือกพลังสูงกว่า)
    คืนค่า {"parts", "buy", "cost", "profit", "grade", "power"} หรือ None ถ้าทำไม่ได้
    """
    state = storage.state
    mold = order["type"]
    if mold not in state["molds"]:
        return None
    best = None
    for parts in recipe_options(mold):
        buy = shopping_list(mold, parts)
        if buy is None:
            continue
        buy_cost = sum(market.price_today(key) * amount for key, amount in buy.items())
        if buy_cost > state["gold"] or storage.check_space(sum(buy.values())):
            continue
        grade = forge.expected_grade(parts, accuracy)
        stats = forge.weapon_stats(mold, parts, grade, accuracy, state["forge_level"])
        trial = dict(stats, type=mold, grade=grade)
        if match_order(trial, order):
            continue
        cost = sum(unit_value(key) * amount for key, amount in forge.materials_for(mold, parts).items())
        option = {"parts": parts, "buy": buy, "cost": cost, "profit": order["pay"] - cost, "grade": grade,
                  "power": stats["power"]}
        if best is None or (cost, -stats["power"]) < (best["cost"], -best["power"]):
            best = option
    return best


def ready_weapon(order: dict) -> dict:
    """อาวุธบนชั้นวางที่ส่งออเดอร์นี้ได้ (เลือกเกรดต่ำสุดที่ผ่าน เพื่อเก็บของดีไว้)"""
    fits = [w for w in storage.state["weapons"] if not match_order(w, order)]
    return min(fits, key=lambda w: (w["grade"], w["power"])) if fits else None


def order_worth(order: dict, accuracy: int) -> float:
    """
    ความคุ้มของออเดอร์ = กำไร + ชื่อเสียง × 6 + โบนัสผู้กล้า/ทหาร (อาวุธไปช่วยตอนจบ)
    ทำไม่ได้ = -9999 (ไปอยู่ท้ายรายการ)
    """
    if order["kind"] == "repair":
        return order["pay"] - market.price_today("iron") + order["fame"] * 6 + 10
    if ready_weapon(order):
        profit = order["pay"]
    else:
        recipe = recommend_recipe(order, accuracy)
        if recipe is None:
            return -9999
        profit = recipe["profit"]
    bonus = {"hero": 12, "guard": 8}.get(order["kind"], 0)
    return profit + order["fame"] * 6 + bonus


def sorted_board(accuracy: int) -> list:
    """ออเดอร์บนกระดานเรียงจากคุ้มที่สุด (เรียงแบบเลือกค่าสูงสุดทีละตัว)"""
    remaining = list(storage.state["board"])
    result = []
    while remaining:
        best = remaining[0]
        for order in remaining:
            if order_worth(order, accuracy) > order_worth(best, accuracy):
                best = order
        result.append(best)
        remaining.remove(best)
    return result


def cash_forecast(days: int = 5) -> list:
    """
    คาดการณ์เงินสดล่วงหน้า: เงินตอนนี้ + ค่าจ้างออเดอร์ที่ครบกำหนดในวันนั้น − ค่าใช้จ่ายรายวัน
    คืนค่า list ของ (วัน, เงินคาดการณ์)
    """
    state = storage.state
    from day import daily_cost      # import ตรงนี้เพื่อไม่ให้ import วนกัน
    gold = state["gold"]
    result = []
    for offset in range(days):
        day = state["day"] + offset
        gold += sum(order["pay"] for order in state["orders"] if order["due"] == day)
        gold -= daily_cost()
        result.append((day, gold))
    return result


# ---------- เมนู Terminal ----------

def show_board(accuracy: int) -> list:
    """แสดงกระดานลูกค้าวันนี้เรียงตามความคุ้ม คืนค่า list ตามลำดับที่แสดง"""
    board = sorted_board(accuracy)
    print(get_text("\n📋 ลูกค้ารอบนกระดาน (เรียงจากคุ้มที่สุด):", "\n📋 Customers on the board (best value first):"))
    if not board:
        print(get_text("   (ว่าง พรุ่งนี้มีลูกค้าใหม่)", "   (empty - new customers tomorrow)"))
    for number, order in enumerate(board, start=1):
        worth = order_worth(order, accuracy)
        mark = get_text("  ✖ ทำไม่ได้ตอนนี้", "  ✖ can't make now") if worth <= -9999 else ""
        print(f" {number}. {order_line(order)}{mark}")
    return board


def show_orders() -> None:
    """แสดงออเดอร์ที่รับไว้ พร้อมบอกว่ามีอาวุธพร้อมส่งหรือยัง"""
    state = storage.state
    print(get_text(f"\n📦 ออเดอร์ที่รับไว้ ({len(state['orders'])}/{MAX_ORDERS}):",
                   f"\n📦 Accepted orders ({len(state['orders'])}/{MAX_ORDERS}):"))
    if not state["orders"]:
        print(get_text("   (ยังไม่มี)", "   (none)"))
    for number, order in enumerate(state["orders"], start=1):
        ready = ""
        if order["kind"] != "repair" and ready_weapon(order):
            ready = get_text("  ✔ มีของพร้อมส่ง", "  ✔ ready to deliver")
        print(f" {number}. {order_line(order)}{ready}")


def cant_make_reason(order: dict) -> str:
    """เหตุผลที่ยังทำออเดอร์นี้ไม่ได้ตอนนี้ (หรือ "" ถ้าทำได้)"""
    if order["kind"] == "repair" or ready_weapon(order) or recommend_recipe(order, 8):
        return ""
    if order["type"] not in storage.state["molds"]:
        return get_text(f"ยังไม่มีแม่พิมพ์{tr(WEAPONS[order['type']]['name'])} (ซื้อได้ที่เมนูลงทุน)",
                        f"No {tr(WEAPONS[order['type']]['name'])} mold yet (buy one in Invest).")
    return get_text("วัตถุดิบที่ต้องใช้ไม่มีขายวันนี้ หรือเงิน/คลังไม่พอ",
                    "Needed materials aren't sold today, or not enough gold/storage.")


def accept_menu(board: list) -> None:
    """รับออเดอร์จากกระดาน (ถ้ายังทำไม่ได้ จะบอกเหตุผลและถามยืนยันก่อน)"""
    order = choose_from_list(board, "เลือกออเดอร์ที่จะรับ", "Choose an order to accept")
    if order is None:
        return
    reason = cant_make_reason(order)
    if reason and not ask_yes_no(f"⚠ {reason} รับไว้ก่อนไหม", f"⚠ {reason} Accept anyway"):
        return
    if not show_error(do_accept(order)):
        print(get_text("✔ รับออเดอร์แล้ว", "✔ Order accepted."))


def deliver_menu() -> None:
    """ส่งของ / ซ่อมให้ออเดอร์ที่รับไว้"""
    state = storage.state
    order = choose_from_list(state["orders"], "เลือกออเดอร์ที่จะส่ง", "Choose an order to fulfil")
    if order is None:
        return
    if order["kind"] == "repair":
        if not show_error(do_repair(order)):
            print(get_text(f"🔧 ซ่อมเสร็จ ได้ {order['pay']} ทอง", f"🔧 Repaired for {order['pay']} gold."))
        return
    if not state["weapons"]:
        print(get_text("ชั้นวางว่าง ตีอาวุธก่อน (ข้อ 2 ตีตามสูตรแนะนำ)", "The rack is empty. Forge first (option 2)."))
        return
    for number, weapon in enumerate(state["weapons"], start=1):
        verdict = match_order(weapon, order)
        print(f" {number}. {forge.weapon_label(weapon)}  " + ("✔" if not verdict else "✖ " + verdict))
    weapon = choose_from_list(state["weapons"], "เลือกอาวุธ", "Choose a weapon")
    if weapon and not show_error(do_deliver(order, weapon)):
        print(get_text("✔ ส่งของแล้ว ลูกค้าพอใจ!", "✔ Delivered. Happy customer!"))
        if order["kind"] == "hero":
            print(get_text("   ผู้กล้าจะถืออาวุธนี้ออกล่าคืนนี้", "   The hero will hunt with it tonight."))
        elif order["kind"] == "guard":
            print(get_text("   อาวุธเข้าคลังทหาร ช่วยป้องกันหมู่บ้านวันที่ 30", "   It joins the garrison for day 30."))


def forge_for_order_menu() -> None:
    """ตีให้ออเดอร์ด้วยสูตรแนะนำ: ซื้อของที่ขาดให้อัตโนมัติแล้วเข้าเตา"""
    state = storage.state
    choices = [order for order in state["orders"] if order["kind"] != "repair"]
    order = choose_from_list(choices, "เลือกออเดอร์ที่จะตีให้", "Choose an order to forge for")
    if order is None:
        return
    recipe = recommend_recipe(order, 8)
    if recipe is None:
        print(get_text("✖ ยังไม่มีสูตรที่ทำได้ (ไม่มีแม่พิมพ์ เงินไม่พอ หรือวัตถุดิบที่ต้องใช้ไม่มีขายวันนี้)",
                       "✖ No workable recipe (missing mold, gold, or materials not sold today)."))
        return
    parts = recipe["parts"]
    names = " + ".join(market.material_text(key) for key in forge.part_list(parts))
    print(get_text(f"💡 สูตรแนะนำ: {names}  ต้นทุน {recipe['cost']}  กำไร ~{recipe['profit']}",
                   f"💡 Best recipe: {names}  cost {recipe['cost']}  profit ~{recipe['profit']}"))
    if recipe["buy"]:
        shopping = ", ".join(f"{market.material_text(k)} x{n}" for k, n in recipe["buy"].items())
        print(get_text(f"   ต้องซื้อเพิ่ม: {shopping}", f"   Need to buy: {shopping}"))
        if not ask_yes_no("ซื้อของที่ขาดเลยไหม", "Buy the missing materials now"):
            return
        for key, amount in recipe["buy"].items():
            if show_error(market.do_buy(key, amount)):
                return
    forge.forge_flow(order["type"], parts)


def orders_menu() -> None:
    """ลูปเมนูกระดานออเดอร์"""
    while True:
        clear_screen()
        heading("กระดานออเดอร์", "ORDER BOARD")
        state = storage.state
        print(get_text(f" วันที่ {state['day']}  💰 {state['gold']}  ⭐ {state['fame']}  ตีได้อีก {state['forges_left']} ครั้ง",
                       f" Day {state['day']}  💰 {state['gold']}  ⭐ {state['fame']}  {state['forges_left']} forgings left"))
        board = show_board(8)
        show_orders()
        print("-" * 60)
        print(get_text("1. รับออเดอร์   2. ตีตามสูตรแนะนำ   3. ส่งของ/ซ่อม   4. ยกเลิกออเดอร์   0. กลับ",
                       "1. Accept   2. Forge best recipe   3. Deliver/repair   4. Cancel an order   0. Back"))
        choice = input(get_text("\nเลือก: ", "\nChoose: ")).strip()
        if choice == "0":
            return
        if choice == "1":
            accept_menu(board)
        elif choice == "2":
            forge_for_order_menu()
        elif choice == "3":
            deliver_menu()
        elif choice == "4":
            order = choose_from_list(state["orders"], "เลือกออเดอร์ที่จะยกเลิก", "Choose an order to cancel")
            if order and ask_yes_no(f"ยกเลิกแล้วจะเสียชื่อเสียง {CANCEL_FAME} แน่ใจ?",
                                    f"Cancelling costs {CANCEL_FAME} fame. Sure?"):
                if not show_error(do_cancel(order)):
                    print(get_text("ยกเลิกแล้ว", "Cancelled."))
        else:
            print(get_text("ไม่มีเมนูนี้", "Invalid option."))
        pause("\nกด Enter...", "\nPress Enter...")
