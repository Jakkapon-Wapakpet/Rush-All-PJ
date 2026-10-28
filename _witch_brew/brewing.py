#!/usr/bin/env python3
"""
Brewing Module - WITCH'S BREW
หม้อปรุงยา: ผสมสมุนไพร 2-3 อย่าง ตรวจสูตร ค้นพบสูตรลับ หม้อระเบิด และตำรายา
Cauldron: mix 2-3 herbs, match recipes, discover secrets, explosions, and the recipe book.
"""

from language import get_text, clear_screen, pause
from data import HERBS, RECIPES, SYMPTOMS, FORBIDDEN, SHELF_SIZE, EXPLOSION_COST, tr
from ui import heading, choose_many
import market
import storage


def potion_name(recipe: str) -> str:
    """ชื่อยาตามภาษาปัจจุบัน"""
    return tr(RECIPES[recipe]["name"])


def cures_text(recipe: str) -> str:
    """อาการที่ยานี้รักษาได้ เช่น 'ไอ, ตัวร้อน'"""
    return ", ".join(tr(SYMPTOMS[s]) for s in RECIPES[recipe]["cures"])


def shelf_count() -> int:
    """จำนวนขวดยาทั้งหมดบนชั้น"""
    return sum(storage.state["shelf"].values())


def find_recipe(herbs: list):
    """หาสูตรที่ใช้สมุนไพรชุดนี้พอดี (ลำดับไม่สำคัญ) คืนค่าชื่อสูตร หรือ None หากไม่ตรงสูตรไหน"""
    for key, recipe in RECIPES.items():
        if sorted(recipe["herbs"]) == sorted(herbs):
            return key
    return None


def forbidden_pair(herbs: list):
    """คู่สมุนไพรต้องห้ามที่อยู่ในชุดนี้ หรือ None หากปลอดภัย"""
    for first, second in FORBIDDEN:
        if first in herbs and second in herbs:
            return first, second
    return None


def recipe_cost(recipe: str) -> int:
    """ต้นทุนของยา 1 ขวด ตามราคาสมุนไพรวันนี้"""
    return sum(market.herb_price(herb) for herb in RECIPES[recipe]["herbs"])


def can_brew_count(recipe: str) -> int:
    """ปรุงยาสูตรนี้ได้กี่ขวดจากสมุนไพรในคลังตอนนี้"""
    stock = storage.state["herbs"]
    return min(stock.get(herb, 0) for herb in RECIPES[recipe]["herbs"])


def brewable_now() -> list:
    """สูตรที่รู้แล้วและปรุงได้ตอนนี้ คืนค่า [(สูตร, จำนวนขวดที่ปรุงได้), ...] เรียงจากได้มากสุด"""
    result = []
    for recipe in storage.state["known"]:
        count = can_brew_count(recipe)
        if count > 0:
            result.append((recipe, count))
    result.sort(key=lambda pair: pair[1], reverse=True)
    return result


def book_progress() -> tuple:
    """ความคืบหน้าของตำรา (รู้แล้วกี่สูตร, ทั้งหมดกี่สูตร)"""
    return len(storage.state["known"]), len(RECIPES)


def do_brew(herbs: list) -> dict:
    """
    ปรุงยาจากสมุนไพรที่เลือก (ใช้ร่วมกันทั้ง Terminal และ GUI)
    คืนค่า {"kind": ..., "recipe": ..., "message": ...}
      kind = "error"    ผิดกฎ ยังไม่ได้ใช้สมุนไพร
             "explode"  ผสมของต้องห้าม หม้อระเบิด
             "fail"     ไม่ตรงสูตร ยาเสีย
             "success"  ได้ยาตามสูตรที่รู้แล้ว
             "discover" ค้นพบสูตรลับใหม่!
    """
    state = storage.state

    # กฎ: ต้องใช้สมุนไพร 2-3 อย่างที่ไม่ซ้ำกัน
    if len(herbs) < 2 or len(herbs) > 3 or len(set(herbs)) != len(herbs):
        return {"kind": "error", "recipe": None,
                "message": get_text("ต้องใช้สมุนไพร 2-3 อย่างที่ไม่ซ้ำกัน", "Use 2-3 different herbs.")}
    # กฎ: สมุนไพรในคลังต้องพอ
    for herb in herbs:
        if state["herbs"].get(herb, 0) < 1:
            return {"kind": "error", "recipe": None,
                    "message": get_text(f"ไม่มี {tr(HERBS[herb]['name'])} ในคลัง",
                                        f"No {tr(HERBS[herb]['name'])} in stock.")}
    # กฎ: ชั้นวางยาต้องมีที่ว่าง
    if shelf_count() >= SHELF_SIZE:
        return {"kind": "error", "recipe": None,
                "message": get_text(f"ชั้นวางเต็ม ({SHELF_SIZE} ขวด) ขายหรือทิ้งยาก่อน",
                                    f"The shelf is full ({SHELF_SIZE}). Sell or discard potions first.")}

    # ใช้สมุนไพร (ไม่ว่าผลจะออกมาแบบไหน)
    for herb in herbs:
        state["herbs"][herb] -= 1
        if state["herbs"][herb] == 0:
            del state["herbs"][herb]

    # กฎ: ผสมของต้องห้าม = หม้อระเบิด เสียค่าซ่อมหม้อ
    pair = forbidden_pair(herbs)
    if pair:
        repair = min(EXPLOSION_COST, state["gold"])
        storage.spend_gold(repair)
        state["log"]["explosions"] += 1
        storage.save_game()
        return {"kind": "explode", "recipe": None, "message": get_text(
            f"💥 ตู้ม!! {tr(HERBS[pair[0]]['name'])} กับ {tr(HERBS[pair[1]]['name'])} เข้ากันไม่ได้! เสียค่าซ่อมหม้อ {repair} ทอง",
            f"💥 BOOM!! {tr(HERBS[pair[0]]['name'])} and {tr(HERBS[pair[1]]['name'])} don't mix! Repairs cost {repair} gold.")}

    recipe = find_recipe(herbs)
    if recipe is None:
        storage.save_game()
        return {"kind": "fail", "recipe": None, "message": get_text(
            "🫧 ได้ของเหลวสีเทาขุ่นๆ... ไม่ตรงสูตรไหนเลย สมุนไพรเสียไปแล้ว",
            "🫧 You get a murky grey liquid... It matches no recipe. The herbs are wasted.")}

    state["shelf"][recipe] = state["shelf"].get(recipe, 0) + 1
    state["log"]["brewed"] += 1
    if recipe not in state["known"]:
        state["known"].append(recipe)
        storage.save_game()
        return {"kind": "discover", "recipe": recipe, "message": get_text(
            f"✨ ค้นพบสูตรลับ: {potion_name(recipe)}! (รักษา: {cures_text(recipe)}) บันทึกลงตำราแล้ว",
            f"✨ Secret recipe discovered: {potion_name(recipe)}! (cures: {cures_text(recipe)}) Added to your book.")}

    storage.save_game()
    return {"kind": "success", "recipe": recipe, "message": get_text(
        f"🧪 ปรุง {potion_name(recipe)} สำเร็จ! วางบนชั้นแล้ว", f"🧪 Brewed {potion_name(recipe)}! It's on the shelf.")}


def brew() -> None:
    """เลือกสมุนไพรจากคลังมาใส่หม้อ"""
    heading("หม้อปรุงยา", "THE CAULDRON")
    keys = [key for key in HERBS if storage.state["herbs"].get(key, 0) > 0]
    if len(keys) < 2:
        print(get_text("สมุนไพรในคลังไม่พอ ไปซื้อที่ตลาดก่อน (ต้องมีอย่างน้อย 2 อย่าง)",
                       "Not enough herbs. Visit the market first (you need at least 2 kinds)."))
        return
    for number, key in enumerate(keys, start=1):
        print(f"{number}. {market.herb_label(key)} x{storage.state['herbs'][key]}")
    print(get_text(f"\nชั้นวางยา: {shelf_count()}/{SHELF_SIZE}", f"\nShelf: {shelf_count()}/{SHELF_SIZE}"))

    herbs = choose_many(keys, "เลือกสมุนไพร 2-3 อย่าง", "Choose 2-3 herbs", 3)
    if herbs is None:
        return
    print(get_text("\n🔮 กำลังคน... ", "\n🔮 Stirring... ") + " + ".join(market.herb_label(h) for h in herbs))
    print(do_brew(herbs)["message"])


def show_brewable() -> None:
    """แสดงสูตรที่ปรุงได้ทันทีจากของในคลัง"""
    heading("ตอนนี้ปรุงอะไรได้บ้าง", "WHAT CAN I BREW NOW?")
    options = brewable_now()
    if not options:
        print(get_text("ยังปรุงสูตรที่รู้จักไม่ได้เลย ลองดูตำราแล้วไปซื้อสมุนไพร",
                       "You can't brew any known recipe yet. Check the book and buy herbs."))
        return
    for recipe, count in options:
        herbs = " + ".join(market.herb_label(h) for h in RECIPES[recipe]["herbs"])
        print(get_text(f"• {potion_name(recipe):<16} ได้ {count} ขวด   ({herbs})",
                       f"• {potion_name(recipe):<16} x{count}   ({herbs})"))


def view_book() -> None:
    """ตำรายา: สูตรที่รู้แล้ว และคำใบ้ของสูตรลับที่ยังไม่ค้นพบ"""
    known, total = book_progress()
    heading(f"ตำรายา   {known}/{total} สูตร", f"RECIPE BOOK   {known}/{total}")
    print(get_text("ความคืบหน้า: ", "Progress: ") + "■" * known + "□" * (total - known))

    for recipe, info in RECIPES.items():
        if recipe in storage.state["known"]:
            herbs = " + ".join(market.herb_label(h) for h in info["herbs"])
            print(f"\n📖 {potion_name(recipe)}  ({get_text('รักษา', 'cures')}: {cures_text(recipe)})")
            print(f"   {herbs}")
            print(get_text(f"   ต้นทุนวันนี้ {recipe_cost(recipe)} ทอง · ราคาแนะนำ {info['price']} ทอง",
                           f"   cost today {recipe_cost(recipe)} gold · suggested price {info['price']} gold"))
        else:
            # คำใบ้: บอกจำนวนสมุนไพร และเปิดเผยสมุนไพร 1 อย่าง
            hint = tr(HERBS[info["herbs"][0]]["name"])
            print(get_text(f"\n🔒 ??? (รักษา: {cures_text(recipe)})",
                           f"\n🔒 ??? (cures: {cures_text(recipe)})"))
            print(get_text(f"   คำใบ้: ใช้สมุนไพร {len(info['herbs'])} อย่าง หนึ่งในนั้นคือ {hint}",
                           f"   Hint: {len(info['herbs'])} herbs, one of them is {hint}"))
    print(get_text("\n⚠ ระวัง: สมุนไพรบางคู่เข้ากันไม่ได้ ผสมแล้วหม้อระเบิด!",
                   "\n⚠ Careful: some herbs don't mix. The cauldron will explode!"))


def cauldron_menu() -> None:
    """เมนูหม้อปรุงยา"""
    actions = {"1": brew, "2": show_brewable}
    while True:
        clear_screen()
        heading("หม้อปรุงยา", "THE CAULDRON")
        print(get_text("1. ปรุงยา", "1. Brew"))
        print(get_text("2. ตอนนี้ปรุงอะไรได้บ้าง", "2. What Can I Brew Now?"))
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
