#!/usr/bin/env python3
"""
Market Module - WITCH'S BREW
ตลาดสมุนไพร: ราคาขึ้นลงทุกวัน ซื้อเข้าคลัง ทิ้งของ และหาของที่ถูกกว่าปกติ
Herb market: daily prices, buying, discarding, and today's bargains.
"""

import random

from language import get_text, clear_screen, pause
from data import HERBS, tr
from ui import heading, choose_from_list, ask_int
import storage

MAX_BUY = 20      # ซื้อได้ครั้งละไม่เกินกี่ชิ้น


def herb_label(key: str) -> str:
    """ชื่อสมุนไพรพร้อมไอคอน"""
    return f"{HERBS[key]['icon']} {tr(HERBS[key]['name'])}"


def roll_market(rng: random.Random) -> None:
    """สุ่มราคาสมุนไพรของวันนี้ (70% - 140% ของราคาพื้นฐาน)"""
    storage.state["market"] = {
        key: max(1, round(info["price"] * rng.uniform(0.7, 1.4))) for key, info in HERBS.items()
    }


def herb_price(key: str) -> int:
    """ราคาสมุนไพรวันนี้"""
    return storage.state["market"].get(key, HERBS[key]["price"])


def price_change(key: str) -> int:
    """ราคาวันนี้ต่างจากราคาปกติกี่ % (ติดลบ = ถูกกว่าปกติ)"""
    return round((herb_price(key) - HERBS[key]["price"]) / HERBS[key]["price"] * 100)


def bargains() -> list:
    """สมุนไพรที่ถูกกว่าปกติวันนี้ เรียงจากลดมากสุด"""
    cheap = [key for key in HERBS if price_change(key) < 0]
    cheap.sort(key=price_change)
    return cheap


def do_buy_herb(key: str, amount: int) -> str:
    """ซื้อสมุนไพรเข้าคลัง (ใช้ร่วมกันทั้ง Terminal และ GUI) คืนข้อความผิดพลาด หรือ "" หากสำเร็จ"""
    # กฎ: จำนวนต้องเป็นบวก
    if amount <= 0:
        return get_text("จำนวนต้องมากกว่า 0", "Amount must be more than 0.")
    # กฎ: ทองต้องพอ
    cost = herb_price(key) * amount
    error = storage.check_gold(cost)
    if error:
        return error

    storage.state["herbs"][key] = storage.state["herbs"].get(key, 0) + amount
    storage.spend_gold(cost)
    storage.save_game()
    return ""


def do_discard_herb(key: str, amount: int) -> str:
    """ทิ้งสมุนไพรออกจากคลัง คืนข้อความผิดพลาด หรือ "" หากสำเร็จ"""
    have = storage.state["herbs"].get(key, 0)
    if amount <= 0 or amount > have:
        return get_text(f"มี {tr(HERBS[key]['name'])} แค่ {have} ชิ้น", f"You only have {have}.")
    storage.state["herbs"][key] = have - amount
    if storage.state["herbs"][key] == 0:
        del storage.state["herbs"][key]
    storage.save_game()
    return ""


def print_market() -> list:
    """แสดงราคาสมุนไพรวันนี้และจำนวนในคลัง คืนค่ารายการสมุนไพรตามลำดับที่แสดง"""
    keys = list(HERBS)
    print(get_text(f"{'':4}{'สมุนไพร':<18}{'ราคาวันนี้':>10}{'เทียบปกติ':>12}{'ในคลัง':>8}",
                   f"{'':4}{'Herb':<18}{'Today':>10}{'vs usual':>12}{'Stock':>8}"))
    for number, key in enumerate(keys, start=1):
        change = price_change(key)
        trend = f"▼{-change}%" if change < 0 else (f"▲{change}%" if change > 0 else "  -")
        print(f"{number:>2}. {herb_label(key):<18}{herb_price(key):>8} {get_text('ทอง', 'g'):<3}"
              f"{trend:>9}{storage.state['herbs'].get(key, 0):>8}")
    return keys


def view_market() -> None:
    """ดูราคาวันนี้และของลดราคา"""
    heading(f"ตลาดสมุนไพร วันที่ {storage.state['day']}", f"HERB MARKET - DAY {storage.state['day']}")
    print_market()
    cheap = bargains()
    if cheap:
        print(get_text("\n💰 ของถูกวันนี้: ", "\n💰 Today's bargains: ")
              + ", ".join(f"{tr(HERBS[k]['name'])} ({price_change(k)}%)" for k in cheap[:3]))
    print(f"\n{get_text('ทอง', 'Gold')}: {storage.state['gold']}")


def buy_herb() -> None:
    """ซื้อสมุนไพร"""
    heading("ซื้อสมุนไพร", "BUY HERBS")
    keys = print_market()
    print(f"\n{get_text('ทอง', 'Gold')}: {storage.state['gold']}")
    key = choose_from_list(keys, "เลือกสมุนไพร", "Choose a herb")
    if key is None:
        return
    amount = ask_int("จำนวน", "Amount", 1, MAX_BUY)
    if amount is None:
        return

    error = do_buy_herb(key, amount)
    if error:
        print(error)
        return
    print(get_text(f"ซื้อ {herb_label(key)} x{amount} แล้ว (เหลือ {storage.state['gold']} ทอง)",
                   f"Bought {herb_label(key)} x{amount}. ({storage.state['gold']} gold left)"))


def discard_herb() -> None:
    """ทิ้งสมุนไพรที่ไม่ใช้"""
    heading("ทิ้งสมุนไพร", "DISCARD HERBS")
    keys = [key for key in HERBS if storage.state["herbs"].get(key, 0) > 0]
    if not keys:
        print(get_text("คลังว่างเปล่า", "Your storeroom is empty."))
        return
    for number, key in enumerate(keys, start=1):
        print(f"{number}. {herb_label(key)} x{storage.state['herbs'][key]}")
    key = choose_from_list(keys, "เลือกสมุนไพร", "Choose a herb")
    if key is None:
        return
    amount = ask_int("จำนวนที่จะทิ้ง", "Amount to discard", 1, storage.state["herbs"][key])
    if amount is None:
        return
    error = do_discard_herb(key, amount)
    print(error or get_text("ทิ้งแล้ว", "Discarded."))


def market_menu() -> None:
    """เมนูตลาดสมุนไพร"""
    actions = {"1": view_market, "2": buy_herb, "3": discard_herb}
    while True:
        clear_screen()
        heading(f"ตลาดสมุนไพร   (ทอง {storage.state['gold']})", f"HERB MARKET   (gold {storage.state['gold']})")
        print(get_text("1. ดูราคาวันนี้", "1. Today's Prices"))
        print(get_text("2. ซื้อสมุนไพร", "2. Buy Herbs"))
        print(get_text("3. ทิ้งสมุนไพร", "3. Discard Herbs"))
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
