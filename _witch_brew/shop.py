#!/usr/bin/env python3
"""
Shop Module - WITCH'S BREW
หน้าร้าน: ชั้นวางยา ตั้งราคา ลูกค้าและอาการ แนะนำยา ขาย ปิดร้านจบวัน และบัญชีร้าน
Shop front: shelf, pricing, customers, recommendations, sales, end of day, and accounts.
"""

import random

from language import get_text, clear_screen, pause
from data import RECIPES, SYMPTOMS, CUSTOMERS_PER_DAY, CUSTOMER_NAMES, SHELF_SIZE, tr
from ui import heading, choose_from_list, choose_many, ask_int, ask_yes_no
import brewing
import market
import storage

MAX_PRICE = 999
TWO_SYMPTOMS_CHANCE = 0.3     # โอกาสที่ลูกค้าจะมี 2 อาการ
KNOWN_SYMPTOM_CHANCE = 0.7    # โอกาสที่อาการจะเป็นแบบที่ร้านรักษาได้แล้ว (ที่เหลือต้องค้นพบสูตรลับ)
WRONG_CURE_PENALTY = 5        # ชื่อเสียงที่เสียเมื่อให้ยาผิดอาการ
TURN_AWAY_PENALTY = 2         # ชื่อเสียงที่เสียเมื่อไล่ลูกค้ากลับ/ปิดร้านทั้งที่ยังมีคนรอ
SERVE_BONUS = 3               # ชื่อเสียงที่ได้เมื่อขายสำเร็จ


# ---------- ชั้นวางยาและราคา ----------

def potion_price(recipe: str) -> int:
    """ราคาขายของยา (ราคาที่ตั้งเอง หรือราคาแนะนำ)"""
    return storage.state["prices"].get(recipe, RECIPES[recipe]["price"])


def shelf_items() -> list:
    """สูตรของยาที่มีบนชั้น เรียงตามชื่อ"""
    return sorted((r for r, n in storage.state["shelf"].items() if n > 0), key=brewing.potion_name)


def do_set_price(recipe: str, price: int) -> str:
    """ตั้งราคาขาย คืนข้อความผิดพลาด หรือ "" หากสำเร็จ"""
    # กฎ: ราคาต้องมากกว่า 0 และไม่เกิน MAX_PRICE
    if price <= 0 or price > MAX_PRICE:
        return get_text(f"ราคาต้องอยู่ระหว่าง 1 ถึง {MAX_PRICE}", f"Price must be between 1 and {MAX_PRICE}.")
    storage.state["prices"][recipe] = price
    storage.save_game()
    return ""


def do_discard_potion(recipe: str) -> str:
    """ทิ้งยา 1 ขวด คืนข้อความผิดพลาด หรือ "" หากสำเร็จ"""
    if storage.state["shelf"].get(recipe, 0) <= 0:
        return get_text("ไม่มียานี้บนชั้น", "That potion is not on the shelf.")
    storage.state["shelf"][recipe] -= 1
    if storage.state["shelf"][recipe] == 0:
        del storage.state["shelf"][recipe]
    storage.save_game()
    return ""


# ---------- ลูกค้า ----------

def cheapest_cure_price(symptom: str) -> int:
    """ราคาแนะนำของยาที่ถูกที่สุดที่รักษาอาการนี้ได้ (ใช้คำนวณงบของลูกค้า)"""
    return min(r["price"] for r in RECIPES.values() if symptom in r["cures"])


def curable_symptoms() -> list:
    """อาการที่สูตรในตำรารักษาได้แล้ว"""
    return sorted({s for r in storage.state["known"] for s in RECIPES[r]["cures"]})


def make_customer(rng: random.Random) -> dict:
    """
    สุ่มลูกค้า 1 คน: ชื่อ อาการ (1-2 อย่าง) และงบที่มี (ชื่อเสียงสูง = งบสูงขึ้น)
    อาการส่วนใหญ่เป็นแบบที่ร้านรักษาได้แล้ว ที่เหลือเป็นอาการที่ต้องค้นพบสูตรลับก่อน
    """
    count = 2 if rng.random() < TWO_SYMPTOMS_CHANCE else 1
    symptoms = []
    while len(symptoms) < count:
        pool = curable_symptoms() if rng.random() < KNOWN_SYMPTOM_CHANCE else list(SYMPTOMS)
        symptom = rng.choice(pool)
        if symptom not in symptoms:
            symptoms.append(symptom)
    need = sum(cheapest_cure_price(s) for s in symptoms)
    mood = 0.7 + storage.state["reputation"] / 100 * 0.6
    return {"name": rng.choice(CUSTOMER_NAMES), "symptoms": symptoms,
            "budget": round(need * rng.uniform(1.1, 1.6) * mood)}


def coverage(recipes: list, symptoms: list) -> float:
    """ยาชุดนี้รักษาอาการของลูกค้าได้กี่ % (0-100)"""
    cured = {s for r in recipes for s in RECIPES[r]["cures"]}
    return sum(1 for s in symptoms if s in cured) / len(symptoms) * 100


def recommend(customer: dict) -> list:
    """
    แนะนำยาบนชั้นสำหรับลูกค้าคนนี้
    คืนค่า [(สูตร, % ที่รักษาได้, ราคา), ...] เรียงจากรักษาได้มากสุด แล้วราคาถูกสุด (ไม่รวมยาที่ไม่ช่วยเลย)
    """
    result = []
    for recipe in shelf_items():
        score = coverage([recipe], customer["symptoms"])
        if score > 0:
            result.append((recipe, score, potion_price(recipe)))
    result.sort(key=lambda item: (-item[1], item[2]))
    return result


def do_serve(customer: dict, recipes: list) -> str:
    """
    ขายยาให้ลูกค้า (ใช้ร่วมกันทั้ง Terminal และ GUI) คืนข้อความผิดพลาด หรือ "" หากขายสำเร็จ
    ลูกค้าที่ซื้อแล้วจะออกจากร้าน ลูกค้าที่ปฏิเสธจะยังรออยู่
    """
    state = storage.state
    for recipe in recipes:
        if state["shelf"].get(recipe, 0) < recipes.count(recipe):
            return get_text("มียาบนชั้นไม่พอ", "Not enough of that potion on the shelf.")

    # กฎ: ยาต้องรักษาครบทุกอาการ ไม่งั้นลูกค้าไม่จ่ายและเสียชื่อเสียง
    if coverage(recipes, customer["symptoms"]) < 100:
        state["reputation"] = max(0, state["reputation"] - WRONG_CURE_PENALTY)
        storage.save_game()
        return get_text(f"😠 {customer['name']}: \"ยานี้ไม่ตรงอาการฉันนะ!\" (ชื่อเสียง -{WRONG_CURE_PENALTY})",
                        f"😠 {customer['name']}: \"This doesn't cure me!\" (reputation -{WRONG_CURE_PENALTY})")
    # กฎ: ราคารวมต้องไม่เกินงบของลูกค้า
    total = sum(potion_price(r) for r in recipes)
    if total > customer["budget"]:
        return get_text(f"💸 {customer['name']}: \"แพงไป! ฉันมีแค่ {customer['budget']} ทอง\" (ราคารวม {total})",
                        f"💸 {customer['name']}: \"Too pricey! I only have {customer['budget']} gold\" (total {total})")

    for recipe in recipes:
        state["shelf"][recipe] -= 1
        if state["shelf"][recipe] == 0:
            del state["shelf"][recipe]
        state["log"]["sold"][recipe] = state["log"]["sold"].get(recipe, 0) + 1
    storage.earn_gold(total)
    state["reputation"] = min(100, state["reputation"] + SERVE_BONUS)
    state["log"]["served"] += 1
    state["customers"].remove(customer)
    storage.save_game()
    return ""


def do_turn_away(customer: dict) -> None:
    """ส่งลูกค้ากลับ (เสียชื่อเสียงเล็กน้อย)"""
    state = storage.state
    state["customers"].remove(customer)
    state["reputation"] = max(0, state["reputation"] - TURN_AWAY_PENALTY)
    state["log"]["turned_away"] += 1
    storage.save_game()


# ---------- วัน ----------

def start_day() -> None:
    """เริ่มวันใหม่: สุ่มราคาตลาด และลูกค้าที่จะมาหน้าร้าน"""
    rng = random.Random()
    market.roll_market(rng)
    storage.state["customers"] = [make_customer(rng) for _ in range(CUSTOMERS_PER_DAY)]
    storage.state["today"] = {"income": 0, "spent": 0}


def do_end_day() -> dict:
    """
    ปิดร้าน: ลูกค้าที่ยังรออยู่กลับบ้าน (เสียชื่อเสียง) จดสรุปของวัน แล้วเริ่มวันใหม่
    คืนค่าสรุปของวันที่เพิ่งจบ
    """
    state = storage.state
    left = len(state["customers"])
    state["reputation"] = max(0, state["reputation"] - TURN_AWAY_PENALTY * left)
    state["log"]["turned_away"] += left

    summary = {"day": state["day"], "income": state["today"]["income"], "spent": state["today"]["spent"],
               "left": left}
    state["log"]["daily"].append(summary)
    state["day"] += 1
    start_day()
    storage.save_game()
    return summary


# ---------- สถิติ ----------

def reputation_stars() -> str:
    """ชื่อเสียงแบบดาว 5 ดวง"""
    stars = int(storage.state["reputation"] / 20 + 0.5)
    return "★" * stars + "☆" * (5 - stars)


def shop_report() -> dict:
    """
    คำนวณสถิติร้าน (ใช้ร่วมกันทั้ง Terminal และ GUI):
    กำไรรวม รายได้เฉลี่ยต่อวัน วันที่ขายดีที่สุด ยาขายดีที่สุด และอัตราการขายสำเร็จ
    """
    log = storage.state["log"]
    days = log["daily"]
    visitors = log["served"] + log["turned_away"]
    best_day = max(days, key=lambda d: d["income"]) if days else None
    best_seller = max(log["sold"], key=log["sold"].get) if log["sold"] else None
    return {
        "profit": log["income"] - log["spent"],
        "average": sum(d["income"] for d in days) / len(days) if days else 0,
        "best_day": best_day,
        "best_seller": best_seller,
        "serve_rate": log["served"] / visitors * 100 if visitors else 0,
    }


# ---------- เมนู Terminal ----------

def print_shelf() -> list:
    """แสดงยาบนชั้น คืนค่ารายการสูตรตามลำดับที่แสดง"""
    items = shelf_items()
    if not items:
        print(get_text("ชั้นวางว่างเปล่า ไปปรุงยาที่หม้อก่อน", "The shelf is empty. Brew something first."))
        return items
    for number, recipe in enumerate(items, start=1):
        cost = brewing.recipe_cost(recipe)
        price = potion_price(recipe)
        print(get_text(f"{number}. {brewing.potion_name(recipe):<16} x{storage.state['shelf'][recipe]}   "
                       f"ราคา {price:>3}   ต้นทุนวันนี้ {cost:>3}   กำไร {price - cost:>4}   ({brewing.cures_text(recipe)})",
                       f"{number}. {brewing.potion_name(recipe):<16} x{storage.state['shelf'][recipe]}   "
                       f"price {price:>3}   cost {cost:>3}   profit {price - cost:>4}   ({brewing.cures_text(recipe)})"))
    return items


def view_shelf() -> None:
    """ดูชั้นวางยา"""
    heading(f"ชั้นวางยา   {brewing.shelf_count()}/{SHELF_SIZE}", f"POTION SHELF   {brewing.shelf_count()}/{SHELF_SIZE}")
    print_shelf()


def set_price() -> None:
    """ตั้งราคาขายยา"""
    heading("ตั้งราคา", "SET PRICES")
    items = print_shelf()
    if not items:
        return
    recipe = choose_from_list(items, "เลือกยา", "Choose a potion")
    if recipe is None:
        return
    price = ask_int("ราคาใหม่", "New price", 1, MAX_PRICE)
    if price is None:
        return
    error = do_set_price(recipe, price)
    if not error and price < brewing.recipe_cost(recipe):
        print(get_text("⚠ ราคานี้ต่ำกว่าต้นทุน ขายแล้วขาดทุนนะ!", "⚠ That's below cost. You'll lose money!"))
    print(error or get_text(f"ตั้งราคา {brewing.potion_name(recipe)} เป็น {price} ทองแล้ว",
                            f"{brewing.potion_name(recipe)} now costs {price} gold."))


def discard_potion() -> None:
    """ทิ้งยา 1 ขวด"""
    heading("ทิ้งยา", "DISCARD A POTION")
    items = print_shelf()
    if not items:
        return
    recipe = choose_from_list(items, "เลือกยา", "Choose a potion")
    if recipe is None:
        return
    print(do_discard_potion(recipe) or get_text("ทิ้งแล้ว 1 ขวด", "Discarded one bottle."))


def shelf_menu() -> None:
    """เมนูชั้นวางยา"""
    actions = {"1": view_shelf, "2": set_price, "3": discard_potion}
    while True:
        clear_screen()
        heading("ชั้นวางยา", "POTION SHELF")
        print(get_text("1. ดูยาบนชั้น", "1. View Shelf"))
        print(get_text("2. ตั้งราคา", "2. Set Prices"))
        print(get_text("3. ทิ้งยา", "3. Discard a Potion"))
        print(get_text("0. กลับ", "0. Back"))

        choice = input(get_text("\nเลือก: ", "\nChoose: ")).strip()
        if choice == "0":
            return
        clear_screen()
        if choice in actions:
            actions[choice]()
        else:
            print(get_text("ไม่มีเมนูนี้", "Invalid option."))
        pause(prompt_th="\nกด Enter เพื่อกลับ...", prompt_en="\nPress Enter to go back...")


def symptoms_text(customer: dict) -> str:
    """อาการของลูกค้า เช่น 'ไอ + ตัวร้อน'"""
    return " + ".join(tr(SYMPTOMS[s]) for s in customer["symptoms"])


def serve_customer(customer: dict) -> None:
    """ดูแลลูกค้า 1 คน: ดูอาการ ดูยาที่แนะนำ แล้วเลือกยาให้ (1-2 ขวด) หรือส่งกลับ"""
    heading(f"ลูกค้า: {customer['name']}", f"CUSTOMER: {customer['name']}")
    print(get_text(f"🤒 อาการ: {symptoms_text(customer)}", f"🤒 Symptoms: {symptoms_text(customer)}"))
    print(get_text(f"💰 งบ: {customer['budget']} ทอง", f"💰 Budget: {customer['budget']} gold"))

    tips = recommend(customer)
    if tips:
        print(get_text("\n💡 ยาบนชั้นที่ช่วยได้:", "\n💡 Potions that can help:"))
        for recipe, score, price in tips:
            print(get_text(f"   {brewing.potion_name(recipe):<16} รักษาได้ {score:.0f}%   ราคา {price}",
                           f"   {brewing.potion_name(recipe):<16} cures {score:.0f}%   price {price}"))
    else:
        print(get_text("\n💡 ยังไม่มียาบนชั้นที่รักษาอาการนี้ได้ ลองไปปรุงก่อนแล้วค่อยกลับมา",
                       "\n💡 Nothing on the shelf helps. Go brew something, then come back."))

    print(get_text("\n1. ขายยา   2. ส่งกลับบ้าน (ชื่อเสียง -2)   0. ให้รอก่อน",
                   "\n1. Sell potions   2. Send away (reputation -2)   0. Ask them to wait"))
    choice = input(get_text("เลือก: ", "Choose: ")).strip()
    if choice == "1":
        print()
        items = print_shelf()
        if not items:
            return
        recipes = choose_many(items, "เลือกยา 1-2 ขวด", "Choose 1-2 potions", 2)
        if recipes is None:
            return
        total = sum(potion_price(r) for r in recipes)
        error = do_serve(customer, recipes)
        print(error or get_text(f"😊 {customer['name']}: \"ขอบคุณมากจ้ะ!\" (+{total} ทอง, ชื่อเสียง +{SERVE_BONUS})",
                                f"😊 {customer['name']}: \"Thank you so much!\" (+{total} gold, reputation +{SERVE_BONUS})"))
    elif choice == "2":
        do_turn_away(customer)
        print(get_text(f"{customer['name']} เดินกลับบ้านไปอย่างผิดหวัง...", f"{customer['name']} leaves, disappointed..."))
    elif choice != "0":
        print(get_text("ไม่มีตัวเลือกนี้", "Invalid option."))


def front_counter() -> None:
    """หน้าร้าน: เลือกลูกค้าที่รออยู่มาดูแล"""
    while True:
        clear_screen()
        customers = storage.state["customers"]
        heading(f"หน้าร้าน   ลูกค้ารอ {len(customers)} คน", f"SHOP FRONT   {len(customers)} waiting")
        if not customers:
            print(get_text("ไม่มีลูกค้ารอแล้ว ปิดร้านเพื่อไปวันถัดไปได้เลย", "No one is waiting. Close the shop to start a new day."))
            pause(prompt_th="\nกด Enter เพื่อกลับ...", prompt_en="\nPress Enter to go back...")
            return
        for number, customer in enumerate(customers, start=1):
            print(get_text(f"{number}. {customer['name']:<12} อาการ: {symptoms_text(customer):<22} งบ {customer['budget']}",
                           f"{number}. {customer['name']:<12} {symptoms_text(customer):<24} budget {customer['budget']}"))
        customer = choose_from_list(customers, "\nเลือกลูกค้า", "\nChoose a customer")
        if customer is None:
            return
        clear_screen()
        serve_customer(customer)
        pause(prompt_th="\nกด Enter เพื่อไปต่อ...", prompt_en="\nPress Enter to continue...")


def end_day() -> None:
    """ปิดร้านและไปวันถัดไป"""
    heading("ปิดร้าน", "CLOSE SHOP")
    waiting = len(storage.state["customers"])
    if waiting and not ask_yes_no(f"ยังมีลูกค้ารออยู่ {waiting} คน ปิดร้านเลย? (ชื่อเสียง -{TURN_AWAY_PENALTY * waiting})",
                                  f"{waiting} customer(s) still waiting. Close anyway? (reputation -{TURN_AWAY_PENALTY * waiting})"):
        print(get_text("ยังไม่ปิดร้าน", "The shop stays open."))
        return

    summary = do_end_day()
    print(get_text(f"\n🌙 จบวันที่ {summary['day']}", f"\n🌙 End of day {summary['day']}"))
    print(get_text(f"   รายได้ {summary['income']}   รายจ่าย {summary['spent']}   กำไร {summary['income'] - summary['spent']}",
                   f"   Income {summary['income']}   Spent {summary['spent']}   Profit {summary['income'] - summary['spent']}"))
    print(get_text(f"\n🌅 เช้าวันที่ {storage.state['day']}: ลูกค้าใหม่ {len(storage.state['customers'])} คนกำลังมา ราคาตลาดเปลี่ยนแล้ว",
                   f"\n🌅 Day {storage.state['day']}: {len(storage.state['customers'])} new customers are coming. Market prices changed."))


def accounts() -> None:
    """บัญชีร้าน: สรุปสถิติทั้งหมด"""
    heading("บัญชีร้าน", "SHOP ACCOUNTS")
    log = storage.state["log"]
    report = shop_report()
    known, total = brewing.book_progress()

    print(get_text(f"วันที่ {storage.state['day']}   ทอง {storage.state['gold']}   ชื่อเสียง {reputation_stars()} ({storage.state['reputation']})",
                   f"Day {storage.state['day']}   Gold {storage.state['gold']}   Reputation {reputation_stars()} ({storage.state['reputation']})"))
    print(get_text(f"\nรายได้รวม {log['income']}   รายจ่ายรวม {log['spent']}   กำไรสุทธิ {report['profit']}",
                   f"\nTotal income {log['income']}   spent {log['spent']}   net profit {report['profit']}"))
    print(get_text(f"รายได้เฉลี่ยต่อวัน {report['average']:.1f} ทอง", f"Average income per day: {report['average']:.1f} gold"))
    if report["best_day"]:
        print(get_text(f"วันที่ขายดีที่สุด: วันที่ {report['best_day']['day']} ({report['best_day']['income']} ทอง)",
                       f"Best day: day {report['best_day']['day']} ({report['best_day']['income']} gold)"))
    print(get_text(f"\nลูกค้าที่ขายสำเร็จ {log['served']} คน   ส่งกลับ {log['turned_away']} คน   (อัตราสำเร็จ {report['serve_rate']:.0f}%)",
                   f"\nCustomers served {log['served']}   sent away {log['turned_away']}   (success rate {report['serve_rate']:.0f}%)"))
    if report["best_seller"]:
        print(get_text(f"ยาขายดีที่สุด: {brewing.potion_name(report['best_seller'])} ({log['sold'][report['best_seller']]} ขวด)",
                       f"Best seller: {brewing.potion_name(report['best_seller'])} ({log['sold'][report['best_seller']]} sold)"))
    print(get_text(f"ปรุงสำเร็จ {log['brewed']} ขวด   หม้อระเบิด {log['explosions']} ครั้ง   ตำรา {known}/{total} สูตร",
                   f"Brewed {log['brewed']}   explosions {log['explosions']}   recipe book {known}/{total}"))
