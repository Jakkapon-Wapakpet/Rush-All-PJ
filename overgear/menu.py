#!/usr/bin/env python3
"""
Menu Module - OVERGEAR (ร้านตีอาวุธ)
หน้าแรก (เริ่ม/เล่นต่อ วิธีเล่น ผลเกม ภาษา) และหน้าร้านในแต่ละวัน (แดชบอร์ด + คำสั่ง)
พร้อมเมนูชั้นวางอาวุธ การลงทุน และอื่นๆ
Title screen, the daily shop screen, the weapon rack, investments, and more.
"""

from language import get_text, clear_screen, pause, choose_language
from data import (DIFFICULTIES, GOAL_DAY, NEWS, WEAPONS, MAX_STOCK, MAX_FORGE_LEVEL, FORGE_UPGRADE,
                  APPRENTICE_HIRE, APPRENTICE_WAGE, MAX_STORAGE, STORAGE_UPGRADE, tr)
from ui import heading, ask_yes_no, choose_from_list, show_error, bar
import day
import forge
import heroes
import market
import shop
import storage

BACK_TH, BACK_EN = "\nกด Enter เพื่อกลับ...", "\nPress Enter to go back..."


# ---------- หน้าแรก ----------

def display_title() -> None:
    """แสดงหน้าแรก (ข้อ 1 คือเริ่มเล่น/เล่นต่อเสมอ)"""
    state = storage.state
    print("=" * 56)
    print("              ⚒   O V E R G E A R   ⚒")
    print(get_text("   ร้านตีอาวุธร้านสุดท้าย - อีก 30 วันมังกรจะบุกหมู่บ้าน",
                   "   The last forge - the dragon comes in 30 days"))
    print(get_text("     \"ดาบทุกเล่มที่ขายไป จะกลับมา... หรือไม่กลับมา\"",
                   "     \"Every blade you sell comes back... or doesn't.\""))
    print("=" * 56)
    if state["status"] == "playing" and state["started"]:
        level = tr(DIFFICULTIES[state["difficulty"]]["name"])
        print(get_text(f" 1. ▶ เล่นต่อ (วันที่ {state['day']}/{GOAL_DAY}, ระดับ{level})",
                       f" 1. ▶ Continue (day {state['day']}/{GOAL_DAY}, {level})"))
    else:
        print(get_text(" 1. ▶ เริ่มเล่น", " 1. ▶ Play"))
    print(get_text(" 2. ✚ เริ่มเกมใหม่", " 2. ✚ New Game"))
    print(get_text(" 3. 📖 วิธีเล่น", " 3. 📖 How to Play"))
    print(get_text(" 4. 🏆 ผลเกมที่ผ่านมา", " 4. 🏆 Past Results"))
    print(get_text(" 5. 🌐 เปลี่ยนภาษา", " 5. 🌐 Change Language"))
    print(get_text(" 0. ออก", " 0. Quit"))


def choose_difficulty():
    """เลือกระดับความยาก คืนค่า key หรือ None ถ้ายกเลิก"""
    heading("เลือกระดับความยาก", "CHOOSE DIFFICULTY")
    keys = list(DIFFICULTIES)
    for number, key in enumerate(keys, start=1):
        info = DIFFICULTIES[key]
        print(f"{number}. {info['icon']} {tr(info['name']):<12} {tr(info['about'])}")
    return choose_from_list(keys, "เลือกระดับ", "Choose a level")


def play() -> None:
    """เล่นต่อจากเซฟ ถ้ายังไม่เคยเริ่มหรือเกมเดิมจบแล้ว จะให้เลือกระดับแล้วเริ่มเกมใหม่"""
    if storage.state["status"] != "playing" or not storage.state["started"]:
        level = choose_difficulty()
        if level is None:
            return
        start(level)
    day_menu()


def start(level: str) -> None:
    """เริ่มเกมใหม่ตามระดับที่เลือก แล้วจดว่าผู้เล่นเริ่มเกมแล้ว (เซฟที่สร้างอัตโนมัติยังไม่นับ)"""
    storage.new_game(level)
    storage.state["started"] = True
    storage.save_game()


def new_game() -> None:
    """เริ่มเกมใหม่ (ถามยืนยันก่อนถ้ามีเกมที่เล่นค้างอยู่)"""
    state = storage.state
    if state["status"] == "playing" and state["started"] and \
            not ask_yes_no(f"มีเกมค้างอยู่ (วันที่ {state['day']}) เริ่มใหม่เลย? ความคืบหน้าเดิมจะหาย",
                           f"You have a game on day {state['day']}. Start over? Progress will be lost."):
        return
    level = choose_difficulty()
    if level is None:
        return
    start(level)
    day_menu()


def how_to_play_text() -> str:
    """ข้อความวิธีเล่น"""
    return get_text(
        "คุณคือช่างตีเหล็กคนสุดท้ายของหมู่บ้านชายแดน อีก 30 วันมังกรจะบุก\n"
        "หาเงิน สร้างชื่อเสียง ติดอาวุธให้ทหารและผู้กล้า แล้วตีอาวุธปราบมังกรให้แชมป์\n\n"
        "ในแต่ละวัน:\n"
        " 1. 📋 กระดานออเดอร์: ลูกค้า 4 คน รับได้ตามแรง (ตีได้วันละ 2 ครั้ง ลูกมือ +1)\n"
        " 2. 🛒 ตลาด: ราคาขึ้นลงทุกวัน ดูข่าวลือพรุ่งนี้เพื่อตุนของให้ถูกจังหวะ\n"
        " 3. 🔥 ตีอาวุธ: ใบมีด + ด้าม + เครื่องประดับ แล้วตีขณะเหล็กยังร้อน (6-8 = สมบูรณ์แบบ)\n"
        " 4. ส่งของ: ได้เงิน + ชื่อเสียง ส่งช้าหรือยกเลิก = เสียชื่อ\n"
        " 5. 🌙 กลางคืน ผู้กล้าที่ถืออาวุธของเราออกล่า รอด → ชื่อเสียง + ของหายาก, ตาย → เสียชื่อ\n\n"
        "เกรด 5 ระดับ: ⚪ธรรมดา 🔵แรร์ 🟣อีปิค 🟠ตำนาน 🔴เทพนิยาย\n"
        " - เหล็กได้สูงสุดแรร์, เงินอีปิค, มิธริลตำนาน, เหล็กดาวตกเทพนิยาย\n"
        " - ตำนานต้องมีวัตถุดิบตำนาน 1 ชิ้น (ได้จากผู้กล้าที่รอดกลับมาเท่านั้น)\n"
        " - เทพนิยายต้องใช้ของตำนาน 3 ชิ้น + เตาเลเวล 4 + ตีสมบูรณ์แบบทุกจังหวะ\n"
        " - ตีวิกฤต 5%: เกรดขึ้นอีก 1 ขั้น (ไม่เกินเพดาน)\n\n"
        "วันที่ 30 มังกรบุก: พลังป้องกัน = อาวุธของทหาร ×0.4 + ผู้กล้าที่ถืออาวุธเรา + แชมป์ ×2\n"
        "แชมป์ถืออาวุธเทพนิยาย = พลัง ×2 และอาจปราบมังกรได้!",
        "You are the last blacksmith of a border village. A dragon attacks in 30 days.\n"
        "Earn gold, build fame, arm the guard and the heroes, then forge a dragon-slayer for your champion.\n\n"
        "Each day:\n"
        " 1. 📋 Order board: 4 customers; you can forge twice a day (+1 with an apprentice)\n"
        " 2. 🛒 Market: prices move daily; read tomorrow's rumor to stock up at the right time\n"
        " 3. 🔥 Forge: blade + handle + ornament, then strike while the iron is hot (6-8 = perfect)\n"
        " 4. Deliver: gold + fame; late or cancelled orders cost fame\n"
        " 5. 🌙 At night heroes hunt with your weapons. Survive → fame + rare loot, die → fame loss\n\n"
        "5 grades: ⚪Common 🔵Rare 🟣Epic 🟠Legendary 🔴Mythic\n"
        " - Iron caps at Rare, Silver Epic, Mithril Legendary, Star Iron Mythic\n"
        " - Legendary needs 1 legend material (only from heroes who come back alive)\n"
        " - Mythic needs 3 legend materials + a level-4 forge + every strike perfect\n"
        " - Critical forge 5%: one grade higher (never above the cap)\n\n"
        "Day 30 the dragon comes: defense = garrison weapons ×0.4 + heroes with our weapons + champion ×2\n"
        "A champion with a Mythic weapon counts ×2 and may slay the dragon!")


def how_to_play() -> None:
    """หน้าวิธีเล่น"""
    clear_screen()
    heading("วิธีเล่น", "HOW TO PLAY")
    print(how_to_play_text())
    pause(BACK_TH, BACK_EN)


def history_summary(history: list) -> dict:
    """สรุปประวัติ: จำนวนเกม เกมที่หมู่บ้านรอด ผลดีที่สุด (ดาว แล้วพลังป้องกัน) และดาวเฉลี่ย"""
    if not history:
        return {"played": 0, "won": 0, "best": None, "average": 0.0, "slayers": 0}
    best = max(history, key=lambda game: (game["stars"], game.get("defense", 0)))
    return {"played": len(history), "won": sum(1 for game in history if game["stars"] > 0), "best": best,
            "average": sum(game["stars"] for game in history) / len(history),
            "slayers": sum(1 for game in history if game.get("slayer"))}


def past_results() -> None:
    """แสดงผลเกมที่ผ่านมา และฉากจบของเกมล่าสุด"""
    clear_screen()
    heading("ผลเกมที่ผ่านมา", "PAST RESULTS")
    state = storage.state
    if state["ending"] and state["status"] != "playing":
        for line in day.ending_lines(state["ending"]):
            print(line)
        print()
    history = storage.load_history()
    if not history:
        print(get_text("ยังไม่มีเกมที่เล่นจบ", "No finished games yet."))
        pause(BACK_TH, BACK_EN)
        return
    for game in history[-10:]:
        level = DIFFICULTIES.get(game.get("difficulty"), DIFFICULTIES["normal"])
        slayer = " 🐉" if game.get("slayer") else ""
        stars = "⭐" * game["stars"] + "☆" * (3 - game["stars"])
        print(get_text(f" เกม {game['game']:>2} {level['icon']} {stars}{slayer}  ป้องกัน {game.get('defense', 0)}"
                       f"/{game.get('dragon', 0)}  เงิน {game.get('gold', 0)}  ผู้กล้าตาย {game.get('deaths', 0)}",
                       f" Game {game['game']:>2} {level['icon']} {stars}{slayer}  defense {game.get('defense', 0)}"
                       f"/{game.get('dragon', 0)}  gold {game.get('gold', 0)}  heroes lost {game.get('deaths', 0)}"))
    summary = history_summary(history)
    print(get_text(f"\n เล่นจบ {summary['played']} เกม  หมู่บ้านรอด {summary['won']} เกม  ดาวเฉลี่ย {summary['average']:.1f}"
                   f"  ปราบมังกร {summary['slayers']} ครั้ง",
                   f"\n Played {summary['played']}  village saved {summary['won']}  average stars {summary['average']:.1f}"
                   f"  dragons slain {summary['slayers']}"))
    pause(BACK_TH, BACK_EN)


def title_menu() -> None:
    """ลูปหน้าแรก วนรับคำสั่งจนกว่าผู้เล่นจะเลือกออก"""
    actions = {"1": play, "2": new_game, "3": how_to_play, "4": past_results, "5": choose_language}
    while True:
        clear_screen()
        display_title()
        choice = input(get_text("\nเลือก: ", "\nChoose: ")).strip()
        if choice in actions:
            actions[choice]()
        elif choice == "0":
            storage.save_game()
            print(get_text("บันทึกแล้ว ไฟในเตายังอุ่นอยู่ ⚒", "Saved. The forge stays warm ⚒"))
            break
        else:
            print(get_text("ไม่มีเมนูนี้", "Invalid option."))
            pause(BACK_TH, BACK_EN)


# ---------- หน้าร้าน (แต่ละวัน) ----------

def display_dashboard() -> None:
    """แดชบอร์ดของวันนี้: เงิน ชื่อเสียง เตา ข่าว ออเดอร์ที่ใกล้กำหนด ผู้กล้า และการเตรียมรับมังกร"""
    state = storage.state
    level = DIFFICULTIES[state["difficulty"]]
    left = GOAL_DAY - state["day"]
    print("=" * 64)
    print(get_text(f"  ⚒ OVERGEAR   วันที่ {state['day']}/{GOAL_DAY}   🐉 อีก {left} วัน   {level['icon']} {tr(level['name'])}",
                   f"  ⚒ OVERGEAR   Day {state['day']}/{GOAL_DAY}   🐉 in {left} days   {level['icon']} {tr(level['name'])}"))
    print("=" * 64)
    apprentice = get_text("มีลูกมือ", "apprentice") if state["apprentice"] else get_text("ไม่มีลูกมือ", "no apprentice")
    print(get_text(f" 💰 {state['gold']} ทอง   ⭐ ชื่อเสียง {state['fame']}   🔥 เตา Lv{state['forge_level']} ({apprentice})",
                   f" 💰 {state['gold']} gold   ⭐ Fame {state['fame']}   🔥 Forge Lv{state['forge_level']} ({apprentice})"))
    print(get_text(f" ⚒ ตีได้อีก {state['forges_left']} ครั้ง   🗡 ชั้นวาง {len(state['weapons'])}/{MAX_STOCK}   "
                   f"📦 คลัง {storage.stored()}/{state['storage']}   ค่าใช้จ่าย/วัน {day.daily_cost()}",
                   f" ⚒ {state['forges_left']} forgings left   🗡 Rack {len(state['weapons'])}/{MAX_STOCK}   "
                   f"📦 Storage {storage.stored()}/{state['storage']}   daily cost {day.daily_cost()}"))
    news, rumor = NEWS[state["news"]], NEWS[state["rumor"]]
    print(get_text(f" 📰 {news['icon']} {tr(news['name'])} - {tr(news['about'])}   (พรุ่งนี้: {rumor['icon']} {tr(rumor['name'])})",
                   f" 📰 {news['icon']} {tr(news['name'])} - {tr(news['about'])}   (tomorrow: {rumor['icon']} {tr(rumor['name'])})"))
    print("-" * 64)
    if state["orders"]:
        for order in sorted(state["orders"], key=lambda o: o["due"])[:3]:
            print("  " + shop.order_line(order))
        if len(state["orders"]) > 3:
            print(get_text(f"  ... และอีก {len(state['orders']) - 3} ใบ", f"  ... and {len(state['orders']) - 3} more"))
    else:
        print(get_text("  ยังไม่ได้รับออเดอร์ ไปดูที่กระดาน", "  No orders yet. Check the board."))
    armed = sum(1 for h in state["heroes"] if heroes.armed(h))
    champ = heroes.champion()
    champ_text = tr(champ["name"]) if champ else get_text("ยังไม่มี", "none")
    print(get_text(f" ⚔ ผู้กล้า {len(state['heroes'])} คน (ถืออาวุธเรา {armed})   👑 แชมป์: {champ_text}",
                   f" ⚔ Heroes {len(state['heroes'])} ({armed} with our weapons)   👑 Champion: {champ_text}"))
    defense = day.defense_breakdown()["total"]
    dragon = day.dragon_power()
    print(get_text(f" 🛡 ป้องกัน [{bar(min(defense, dragon), dragon, 20)}] {defense} / มังกร ~{dragon}",
                   f" 🛡 Defense [{bar(min(defense, dragon), dragon, 20)}] {defense} / dragon ~{dragon}"))
    print("-" * 64)
    print(get_text(" 1. 📋 กระดานออเดอร์ (รับ / ตีตามสูตร / ส่ง)", " 1. 📋 Order board (accept / forge / deliver)"))
    print(get_text(" 2. 🛒 ตลาด", " 2. 🛒 Market"))
    print(get_text(" 3. 🔥 ตีอาวุธ (เลือกสูตรเอง)", " 3. 🔥 Forge (custom recipe)"))
    print(get_text(" 4. 🗡 ชั้นวางอาวุธ", " 4. 🗡 Weapon rack"))
    print(get_text(" 5. ⚔ ผู้กล้า", " 5. ⚔ Heroes"))
    print(get_text(" 6. 🏗 ลงทุน", " 6. 🏗 Invest"))
    print(get_text(" 7. 🌙 จบวัน", " 7. 🌙 End day"))
    print(get_text(" 8. ⋯ อื่นๆ (บันทึกร้าน / คาดการณ์)", " 8. ⋯ More (shop log / forecast)"))
    print(get_text(" 0. พักเกม (กลับหน้าแรก)", " 0. Pause (back to title)"))


# ---------- ชั้นวางอาวุธ ----------

def show_rack() -> None:
    """แสดงอาวุธบนชั้นวาง และอาวุธในคลังทหาร"""
    state = storage.state
    heading("ชั้นวางอาวุธ", "WEAPON RACK")
    if not state["weapons"]:
        print(get_text(" ชั้นวางว่าง", " The rack is empty."))
    for number, weapon in enumerate(state["weapons"], start=1):
        print(f" {number}. {forge.weapon_label(weapon)}")
        print(f"    {forge.weapon_detail(weapon)}")
    garrison = state["garrison"]
    total = sum(w["power"] for w in garrison)
    print(get_text(f"\n 🛡 คลังทหารรักษาเมือง: {len(garrison)} ชิ้น พลังรวม {total}",
                   f"\n 🛡 Town garrison: {len(garrison)} weapons, total power {total}"))


def engrave_menu() -> None:
    """สลักชื่ออาวุธ"""
    weapon = choose_from_list(storage.state["weapons"], "เลือกอาวุธ", "Choose a weapon")
    if weapon is None:
        return
    text = input(get_text("ชื่อที่จะสลัก (ไม่เกิน 14 ตัว): ", "Name to engrave (max 14): "))
    if not show_error(forge.do_engrave(weapon, text)):
        print(get_text("✔ สลักชื่อแล้ว", "✔ Engraved."))


def sell_weapon_menu() -> None:
    """ขายอาวุธให้พ่อค้าเร่"""
    weapon = choose_from_list(storage.state["weapons"], "เลือกอาวุธที่จะขาย", "Choose a weapon to sell")
    if weapon and ask_yes_no(f"ขายได้ {shop.walkin_price(weapon)} ทอง ขายเลย?",
                             f"Sell for {shop.walkin_price(weapon)} gold?"):
        if not show_error(shop.do_sell_weapon(weapon)):
            print(get_text("✔ ขายแล้ว", "✔ Sold."))


def melt_menu() -> None:
    """หลอมอาวุธคืนเป็นโลหะ"""
    weapon = choose_from_list(storage.state["weapons"], "เลือกอาวุธที่จะหลอม", "Choose a weapon to melt")
    if weapon is None:
        return
    back = ", ".join(f"{market.material_text(k)} x{n}" for k, n in forge.melt_return(weapon).items())
    if ask_yes_no(f"หลอมแล้วได้ {back} คืน แน่ใจ?", f"Melting returns {back}. Sure?"):
        if not show_error(forge.do_melt(weapon)):
            print(get_text("✔ หลอมแล้ว", "✔ Melted down."))


def donate_menu() -> None:
    """บริจาคอาวุธให้ทหารรักษาเมือง"""
    weapon = choose_from_list(storage.state["weapons"], "เลือกอาวุธที่จะบริจาค", "Choose a weapon to donate")
    if weapon and not show_error(shop.do_donate(weapon)):
        print(get_text("🛡 ทหารขอบคุณ! พลังป้องกันหมู่บ้านเพิ่มขึ้น (ชื่อเสียง +1)",
                       "🛡 The guard thanks you! Village defense up (fame +1)"))


def rack_menu() -> None:
    """ลูปเมนูชั้นวางอาวุธ (ดู / สลักชื่อ / ขาย / หลอม / บริจาค)"""
    actions = {"1": engrave_menu, "2": sell_weapon_menu, "3": melt_menu, "4": donate_menu}
    while True:
        clear_screen()
        show_rack()
        print("-" * 60)
        print(get_text("1. สลักชื่อ   2. ขายให้พ่อค้าเร่   3. หลอมคืน   4. บริจาคให้ทหาร   0. กลับ",
                       "1. Engrave   2. Sell to peddler   3. Melt down   4. Donate to guard   0. Back"))
        choice = input(get_text("\nเลือก: ", "\nChoose: ")).strip()
        if choice == "0":
            return
        if choice in actions:
            actions[choice]()
        else:
            print(get_text("ไม่มีเมนูนี้", "Invalid option."))
        pause("\nกด Enter...", "\nPress Enter...")


# ---------- ลงทุน ----------

def invest_menu() -> None:
    """ลงทุน: อัปเกรดเตา จ้าง/เลิกจ้างลูกมือ ซื้อแม่พิมพ์ ขยายคลัง"""
    while True:
        clear_screen()
        state = storage.state
        heading("ลงทุน", "INVEST")
        print(get_text(f" 💰 {state['gold']} ทอง\n", f" 💰 {state['gold']} gold\n"))
        if state["forge_level"] < MAX_FORGE_LEVEL:
            cost = FORGE_UPGRADE[state["forge_level"] + 1]
            print(get_text(f" 1. 🔥 อัปเกรดเตา Lv{state['forge_level']} → Lv{state['forge_level'] + 1} ({cost} ทอง)"
                           f"  คุณภาพ +2 มินิเกม +1 จังหวะ",
                           f" 1. 🔥 Upgrade forge Lv{state['forge_level']} → Lv{state['forge_level'] + 1} ({cost} gold)"
                           f"  quality +2, +1 mini-game move"))
        else:
            print(get_text(" 1. 🔥 เตาเลเวลสูงสุดแล้ว (ปลดล็อกเทพนิยาย)", " 1. 🔥 Forge at max level (Mythic unlocked)"))
        if state["apprentice"]:
            print(get_text(f" 2. 🧑‍🔧 เลิกจ้างลูกมือ (ประหยัด {APPRENTICE_WAGE} ทอง/วัน)",
                           f" 2. 🧑‍🔧 Dismiss apprentice (save {APPRENTICE_WAGE} gold/day)"))
        else:
            print(get_text(f" 2. 🧑‍🔧 จ้างลูกมือ ({APPRENTICE_HIRE} ทอง + {APPRENTICE_WAGE}/วัน) ตีได้ +1 ครั้ง/วัน",
                           f" 2. 🧑‍🔧 Hire apprentice ({APPRENTICE_HIRE} gold + {APPRENTICE_WAGE}/day) +1 forging/day"))
        print(get_text(" 3. 🗿 ซื้อแม่พิมพ์อาวุธ", " 3. 🗿 Buy a weapon mold"))
        if state["storage"] < MAX_STORAGE:
            print(get_text(f" 4. 📦 ขยายคลัง +{STORAGE_UPGRADE} ช่อง ({market.EXPAND_COST} ทอง)",
                           f" 4. 📦 Expand storage +{STORAGE_UPGRADE} ({market.EXPAND_COST} gold)"))
        else:
            print(get_text(" 4. 📦 คลังใหญ่สุดแล้ว", " 4. 📦 Storage at max"))
        print(get_text(" 0. กลับ", " 0. Back"))
        choice = input(get_text("\nเลือก: ", "\nChoose: ")).strip()
        if choice == "0":
            return
        if choice == "1":
            if not show_error(forge.do_upgrade_forge()):
                print(get_text(f"✔ เตาเลเวล {state['forge_level']} แล้ว!", f"✔ Forge is now level {state['forge_level']}!"))
        elif choice == "2":
            if state["apprentice"]:
                if ask_yes_no("เลิกจ้างลูกมือ?", "Dismiss the apprentice?") and not show_error(forge.do_fire()):
                    print(get_text("ลูกมือกลับบ้านไปแล้ว", "The apprentice went home."))
            elif not show_error(forge.do_hire()):
                print(get_text("✔ ได้ลูกมือแล้ว!", "✔ Apprentice hired!"))
        elif choice == "3":
            missing = [mold for mold in WEAPONS if mold not in state["molds"]]
            if not missing:
                print(get_text("มีแม่พิมพ์ครบทุกแบบแล้ว", "You own every mold."))
            else:
                for number, mold in enumerate(missing, start=1):
                    print(f" {number}. {WEAPONS[mold]['icon']} {tr(WEAPONS[mold]['name'])} - {WEAPONS[mold]['mold']}")
                mold = choose_from_list(missing, "เลือกแม่พิมพ์", "Choose a mold")
                if mold and not show_error(forge.do_buy_mold(mold)):
                    print(get_text("✔ ได้แม่พิมพ์ใหม่แล้ว", "✔ New mold acquired."))
        elif choice == "4":
            if not show_error(market.do_expand_storage()):
                print(get_text(f"✔ คลังขยายเป็น {state['storage']} ช่อง", f"✔ Storage is now {state['storage']}."))
        else:
            print(get_text("ไม่มีเมนูนี้", "Invalid option."))
        pause("\nกด Enter...", "\nPress Enter...")


# ---------- อื่นๆ ----------

def forecast() -> None:
    """คาดการณ์เงินสด 5 วัน และพลังป้องกันเทียบมังกร"""
    heading("คาดการณ์", "FORECAST")
    print(get_text(" 💰 เงินสดคาดการณ์ (ค่าจ้างออเดอร์ที่ครบกำหนด − ค่าใช้จ่ายรายวัน):",
                   " 💰 Cash forecast (orders due − daily costs):"))
    for when, gold in shop.cash_forecast(5):
        warn = get_text("  ⚠ ติดลบ!", "  ⚠ negative!") if gold < 0 else ""
        print(get_text(f"   วันที่ {when:>2}: {gold}{warn}", f"   Day {when:>2}: {gold}{warn}"))
    parts = day.defense_breakdown()
    print(get_text(f"\n 🐉 ถ้ามังกรมาวันนี้: ทหาร {parts['garrison']} + ผู้กล้า {parts['heroes']} + แชมป์ {parts['champion']}"
                   f" = {parts['total']} vs {day.dragon_power()}",
                   f"\n 🐉 If the dragon came today: garrison {parts['garrison']} + heroes {parts['heroes']} + champion "
                   f"{parts['champion']} = {parts['total']} vs {day.dragon_power()}"))
    stars, title = day.ending_grade(parts["total"] / day.dragon_power())
    print("   " + "⭐" * stars + "☆" * (3 - stars) + "  " + tr(title))


def more_menu() -> None:
    """เมนูอื่นๆ: บันทึกร้าน คาดการณ์ วิธีเล่น"""
    actions = {"1": day.shop_log, "2": forecast, "3": lambda: print(how_to_play_text())}
    while True:
        clear_screen()
        heading("อื่นๆ", "MORE")
        print(get_text("1. บันทึกร้าน (สถิติ + กราฟ)", "1. Shop log (stats + graph)"))
        print(get_text("2. คาดการณ์เงินสดและพลังป้องกัน", "2. Cash & defense forecast"))
        print(get_text("3. วิธีเล่น", "3. How to play"))
        print(get_text("0. กลับ", "0. Back"))
        choice = input(get_text("\nเลือก: ", "\nChoose: ")).strip()
        if choice == "0":
            return
        clear_screen()
        if choice in actions:
            actions[choice]()
        else:
            print(get_text("ไม่มีเมนูนี้", "Invalid option."))
        pause(BACK_TH, BACK_EN)


def day_menu() -> None:
    """ลูปหน้าร้าน วนจนกว่าผู้เล่นจะพักเกม หรือเกมจบ"""
    loops = {"1": shop.orders_menu, "2": market.market_menu, "4": rack_menu, "5": heroes.heroes_menu,
             "6": invest_menu, "8": more_menu}
    once = {"3": forge.forge_menu, "7": day.end_day}
    # กฎ: เล่นได้เฉพาะตอนเกมยังไม่จบ (จบแล้วกลับหน้าแรก)
    while storage.state["status"] == "playing":
        clear_screen()
        display_dashboard()
        choice = input(get_text("\nเลือก: ", "\nChoose: ")).strip()
        if choice in loops:
            loops[choice]()
        elif choice in once:
            clear_screen()
            once[choice]()
            pause(BACK_TH, BACK_EN)
        elif choice == "0":
            storage.save_game()
            return
        else:
            print(get_text("ไม่มีเมนูนี้", "Invalid option."))
            pause(BACK_TH, BACK_EN)
