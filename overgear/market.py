#!/usr/bin/env python3
"""
Market Module - OVERGEAR (ร้านตีอาวุธ)
ตลาดวัตถุดิบ: ราคาขึ้นลงทุกวันตามข่าว คาราวาน ของที่ผู้กล้านำกลับมาขาย และการขยายคลัง
Material market: daily prices driven by news, caravans, hero loot offers, and storage upgrades.
"""

import random

from language import get_text, clear_screen, pause
from data import MATERIALS, NEWS, SLOTS, SELL_RATE, STORAGE_UPGRADE, MAX_STORAGE, tr
from ui import heading, choose_from_list, ask_int, show_error
import storage

EXPAND_COST = 45          # ขยายคลังครั้งละ


# ---------- ข่าวและราคา ----------

def roll_news(rng: random.Random) -> str:
    """สุ่มข่าวของวันตามน้ำหนักในข้อมูลข่าว"""
    keys = list(NEWS)
    weights = [NEWS[key]["weight"] for key in keys]
    return rng.choices(keys, weights=weights)[0]


def news_value(field: str, default=None):
    """ค่าผลของข่าววันนี้ เช่น news_value('pay', 1.0)"""
    return NEWS[storage.state["news"]].get(field, default)


def available(key: str) -> bool:
    """วันนี้ตลาดมีวัตถุดิบนี้ขายไหม (มิธริลมีเฉพาะวันที่คาราวานมา ของตำนานไม่มีขาย)"""
    info = MATERIALS[key]
    if info["legend"]:
        return False
    return info["market"] or bool(news_value("caravan", False))


def make_prices(rng: random.Random) -> None:
    """สร้างราคาวันนี้ = ราคาฐาน × ความผันผวนตามระดับความยาก × ผลของข่าว"""
    state = storage.state
    state["last_prices"] = dict(state["prices"])
    swing = storage.setting("swing")
    changes = news_value("price", {})
    prices = {}
    for key, info in MATERIALS.items():
        if info["legend"]:
            continue
        factor = 1 + rng.uniform(-swing, swing)
        prices[key] = max(1, round(info["price"] * factor * changes.get(key, 1.0)))
    state["prices"] = prices


def price_today(key: str) -> int:
    """ราคาซื้อวันนี้ (ของตำนานใช้ราคาอ้างอิงในข้อมูล)"""
    return storage.state["prices"].get(key, MATERIALS[key]["price"])


def sell_price(key: str) -> int:
    """ราคาที่ตลาดรับซื้อคืน (ครึ่งราคา)"""
    return max(1, int(price_today(key) * SELL_RATE))


def trend(key: str) -> str:
    """ลูกศรบอกว่าราคาขึ้นหรือลงจากเมื่อวาน"""
    last = storage.state.get("last_prices", {}).get(key)
    now = storage.state["prices"].get(key)
    if last is None or now is None or last == now:
        return " "
    return "▲" if now > last else "▼"


def material_text(key: str) -> str:
    """ชื่อวัตถุดิบพร้อมไอคอน"""
    return f"{MATERIALS[key]['icon']} {tr(MATERIALS[key]['name'])}"


# ---------- ซื้อ / ขาย ----------

def do_buy(key: str, amount: int) -> str:
    """ซื้อวัตถุดิบ คืนข้อความผิดพลาด หรือ "" หากสำเร็จ"""
    if key not in MATERIALS:
        return get_text("ไม่มีวัตถุดิบนี้", "Unknown material.")
    if amount <= 0:
        return get_text("จำนวนต้องมากกว่า 0", "Amount must be above 0.")
    if not available(key):
        return get_text(f"วันนี้ไม่มี{tr(MATERIALS[key]['name'])}ขาย", f"No {tr(MATERIALS[key]['name'])} on sale today.")
    error = storage.check_space(amount) or storage.check_gold(price_today(key) * amount)
    if error:
        return error
    storage.pay(price_today(key) * amount)
    storage.state["materials"][key] += amount
    storage.save_game()
    return ""


def do_sell(key: str, amount: int) -> str:
    """ขายวัตถุดิบคืนตลาดครึ่งราคา (ลบของออกจากคลัง)"""
    if key not in MATERIALS:
        return get_text("ไม่มีวัตถุดิบนี้", "Unknown material.")
    if amount <= 0:
        return get_text("จำนวนต้องมากกว่า 0", "Amount must be above 0.")
    error = storage.check_materials({key: amount})
    if error:
        return error
    storage.state["materials"][key] -= amount
    storage.earn(sell_price(key) * amount)
    storage.save_game()
    return ""


def do_buy_offer(offer: dict) -> str:
    """ซื้อของที่ผู้กล้านำกลับมาขาย (มีวันเดียว)"""
    state = storage.state
    if offer not in state["offers"]:
        return get_text("ไม่มีของชิ้นนี้แล้ว", "That offer is gone.")
    error = storage.check_space(1) or storage.check_gold(offer["price"])
    if error:
        return error
    storage.pay(offer["price"])
    state["materials"][offer["material"]] += 1
    state["offers"].remove(offer)
    if MATERIALS[offer["material"]]["legend"]:
        state["log"]["legends"] += 1
    storage.save_game()
    return ""


def do_expand_storage() -> str:
    """ลงทุนขยายคลังวัตถุดิบ"""
    state = storage.state
    if state["storage"] >= MAX_STORAGE:
        return get_text("คลังใหญ่สุดแล้ว", "Storage is already at maximum.")
    error = storage.check_gold(EXPAND_COST)
    if error:
        return error
    storage.pay(EXPAND_COST)
    state["storage"] += STORAGE_UPGRADE
    storage.save_game()
    return ""


# ---------- เมนู Terminal ----------

def show_market() -> list:
    """แสดงตารางราคาวันนี้ คืนค่า list ของวัตถุดิบที่ซื้อได้วันนี้ (ตามลำดับหมายเลข)"""
    state = storage.state
    news = NEWS[state["news"]]
    rumor = NEWS[state["rumor"]]
    heading("ตลาดวัตถุดิบ", "MATERIAL MARKET")
    print(get_text(f" ข่าววันนี้: {news['icon']} {tr(news['name'])} - {tr(news['about'])}",
                   f" Today: {news['icon']} {tr(news['name'])} - {tr(news['about'])}"))
    print(get_text(f" ข่าวลือพรุ่งนี้: {rumor['icon']} {tr(rumor['name'])}",
                   f" Rumor for tomorrow: {rumor['icon']} {tr(rumor['name'])}"))
    print(get_text(f" 💰 {state['gold']} ทอง   📦 คลัง {storage.stored()}/{state['storage']}",
                   f" 💰 {state['gold']} gold   📦 Storage {storage.stored()}/{state['storage']}"))
    print("-" * 60)
    print(get_text("    วัตถุดิบ             ส่วน          มี   ราคา", "    Material             Part        Have  Price"))
    buyable = [key for key in MATERIALS if available(key)]
    for number, key in enumerate(buyable, start=1):
        slot = tr(SLOTS[MATERIALS[key]["slot"]])
        print(f" {number:>2}. {material_text(key):<18} {slot:<12} {state['materials'][key]:>3}  "
              f"{price_today(key):>4} {trend(key)}")
    others = [key for key in MATERIALS if not available(key) and state["materials"][key]]
    for key in others:
        print(f"     {material_text(key):<18} {tr(SLOTS[MATERIALS[key]['slot']]):<12} "
              f"{state['materials'][key]:>3}  {get_text('ไม่มีขาย', 'n/a')}")
    if state["offers"]:
        print(get_text("\n ⚔ ผู้กล้านำของกลับมาขาย (วันนี้วันเดียว):", "\n ⚔ Heroes selling loot (today only):"))
        for offer in state["offers"]:
            print(f"   - {material_text(offer['material'])} {offer['price']} "
                  f"{get_text('ทอง จาก', 'gold from')} {tr(offer['hero'])}")
    return buyable


def buy_menu(buyable: list) -> None:
    """ซื้อวัตถุดิบจากตลาด"""
    key = choose_from_list(buyable, "เลือกวัตถุดิบที่จะซื้อ", "Choose a material to buy")
    if key is None:
        return
    state = storage.state
    most = min(state["gold"] // price_today(key), state["storage"] - storage.stored())
    if most <= 0:
        show_error(storage.check_space(1) or storage.check_gold(price_today(key)))
        return
    amount = ask_int("ซื้อกี่ชิ้น", "How many", 1, most)
    if amount is None:
        return
    if not show_error(do_buy(key, amount)):
        print(get_text(f"✔ ซื้อ{tr(MATERIALS[key]['name'])} {amount} ชิ้น เหลือ {state['gold']} ทอง",
                       f"✔ Bought {amount} {tr(MATERIALS[key]['name'])}. {state['gold']} gold left."))


def sell_menu() -> None:
    """ขายวัตถุดิบคืนตลาด"""
    state = storage.state
    owned = [key for key in MATERIALS if state["materials"][key] > 0]
    if not owned:
        print(get_text("คลังว่าง", "Storage is empty."))
        return
    for number, key in enumerate(owned, start=1):
        print(f" {number}. {material_text(key)} x{state['materials'][key]} "
              f"({get_text('รับซื้อ', 'buys at')} {sell_price(key)})")
    key = choose_from_list(owned, "เลือกวัตถุดิบที่จะขาย", "Choose a material to sell")
    if key is None:
        return
    amount = ask_int("ขายกี่ชิ้น", "How many", 1, state["materials"][key])
    if amount is None:
        return
    if not show_error(do_sell(key, amount)):
        print(get_text(f"✔ ขายแล้ว ได้ {sell_price(key) * amount} ทอง", f"✔ Sold for {sell_price(key) * amount} gold."))


def offer_menu() -> None:
    """ซื้อของจากผู้กล้า"""
    offers = storage.state["offers"]
    if not offers:
        print(get_text("วันนี้ไม่มีผู้กล้านำของมาขาย", "No hero loot for sale today."))
        return
    for number, offer in enumerate(offers, start=1):
        print(f" {number}. {material_text(offer['material'])} - {offer['price']} {get_text('ทอง', 'gold')} "
              f"({tr(offer['hero'])})")
    offer = choose_from_list(offers, "เลือกของ", "Choose an offer")
    if offer and not show_error(do_buy_offer(offer)):
        print(get_text("✔ ซื้อแล้ว", "✔ Bought."))


def market_menu() -> None:
    """ลูปเมนูตลาด"""
    while True:
        clear_screen()
        buyable = show_market()
        print("-" * 60)
        print(get_text("1. ซื้อ   2. ขาย   3. ซื้อของจากผู้กล้า   0. กลับ",
                       "1. Buy   2. Sell   3. Buy hero loot   0. Back"))
        choice = input(get_text("\nเลือก: ", "\nChoose: ")).strip()
        if choice == "0":
            return
        if choice == "1":
            buy_menu(buyable)
        elif choice == "2":
            sell_menu()
        elif choice == "3":
            offer_menu()
        else:
            print(get_text("ไม่มีเมนูนี้", "Invalid option."))
        pause("\nกด Enter...", "\nPress Enter...")
