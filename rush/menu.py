#!/usr/bin/env python3
"""
Menu Module - LAST SHELTER
2 หน้าจอหลัก: หน้าแรก (เริ่ม/เล่นต่อ วิธีเล่น ผลเกม ภาษา) และหน้าเล่นเกมในแต่ละวัน (แดชบอร์ด + คำสั่ง)
Two main screens: the title screen and the in-game day screen (dashboard + actions).
"""

from language import get_text, clear_screen, pause, choose_language
from data import RESOURCES, SKILLS, GOAL_DAY, MAX_CAMP, MAX_HP, tr
from ui import heading, ask_yes_no
import camp
import day
import powers
import storage
import survivors

BACK_TH, BACK_EN = "\nกด Enter เพื่อกลับ...", "\nPress Enter to go back..."


# ---------- หน้าแรก ----------

def display_title() -> None:
    """แสดงหน้าแรก (ข้อ 1 คือเริ่มเล่น/เล่นต่อเสมอ)"""
    state = storage.state
    print("=" * 50)
    print("          🧟   L A S T   S H E L T E R   🧟")
    print(get_text("     รอดให้ถึงวันที่ 15 แล้วเฮลิคอปเตอร์จะมารับ",
                   "     Survive until day 15 for the rescue chopper"))
    print("=" * 50)
    if state["status"] == "playing" and state["day"] > 1:
        print(get_text(f" 1. ▶ เล่นต่อ (วันที่ {state['day']}/{GOAL_DAY})", f" 1. ▶ Continue (day {state['day']}/{GOAL_DAY})"))
    else:
        print(get_text(" 1. ▶ เริ่มเล่น", " 1. ▶ Play"))
    print(get_text(" 2. ✚ เริ่มเกมใหม่", " 2. ✚ New Game"))
    print(get_text(" 3. 📖 วิธีเล่น", " 3. 📖 How to Play"))
    print(get_text(" 4. 🏆 ผลเกมที่ผ่านมา", " 4. 🏆 Past Results"))
    print(get_text(" 5. 🌐 เปลี่ยนภาษา", " 5. 🌐 Change Language"))
    print(get_text(" 0. ออก", " 0. Quit"))


def play() -> None:
    """เล่นต่อจากเซฟ ถ้าเกมเดิมจบแล้วจะเริ่มเกมใหม่ให้อัตโนมัติ"""
    if storage.state["status"] != "playing":
        storage.new_game()
    day_menu()


def new_game() -> None:
    """เริ่มเกมใหม่ (ถามยืนยันก่อนถ้ามีเกมที่เล่นค้างอยู่)"""
    state = storage.state
    if state["status"] == "playing" and state["day"] > 1 and \
            not ask_yes_no(f"มีเกมค้างอยู่ (วันที่ {state['day']}) เริ่มใหม่เลย? ความคืบหน้าเดิมจะหาย",
                           f"You have a game on day {state['day']}. Start over? Progress will be lost."):
        return
    storage.new_game()
    day_menu()


def how_to_play_text() -> str:
    """ข้อความวิธีเล่น (ใช้ร่วมกันทั้ง Terminal และ GUI)"""
    return get_text(
        f"🎯 เป้าหมาย: พาผู้รอดชีวิตให้รอดถึงจบวันที่ {GOAL_DAY} ยิ่งรอดเยอะ ยิ่งได้ดาวเยอะ (สูงสุด ⭐⭐⭐)\n"
        "\n📅 ในแต่ละวัน\n"
        "  1. มอบงานให้ทุกคน (กด ⚡ จัดงานอัตโนมัติ ได้)\n"
        "       🎒 หาเสบียง  🛡 เฝ้ายาม  ✚ รักษา  💤 พักผ่อน\n"
        "  2. สร้างสิ่งก่อสร้างด้วยเศษวัสดุ เช่น แนวกั้น แปลงผัก ถังเก็บน้ำ\n"
        "  3. ตัดสินใจที่ประตู: รับ / ไม่รับ / ตรวจร่างกายก่อน\n"
        "  4. จบวัน → กลางคืนซอมบี้อาจบุก\n"
        "\n📜 กฎสำคัญ\n"
        "  • ทุกคนกินอาหาร 1 + ดื่มน้ำ 1 ต่อวัน ถ้าไม่พอจะเสีย HP\n"
        "  • HP ต่ำกว่า 40 ออกไปหาเสบียง/เฝ้ายามไม่ได้\n"
        "  • ติดเชื้อแล้วต้องได้ยาภายใน 2 วัน ไม่งั้นกลายเป็นซอมบี้!\n"
        "  • คนติดเชื้อขึ้นเฮลิคอปเตอร์ไม่ได้\n"
        "  • ซอมบี้มี 5 เลเวล ยิ่งหลายวันยิ่งเก่ง และราชาซอมบี้บุกคืนสุดท้ายแน่นอน\n"
        "\n⚡ ทุกคนมีพลังพิเศษ เลเวลขึ้นเมื่อทำงาน (ทำงานที่ตรงกับพลังได้ XP x2)",
        f"🎯 Goal: keep your survivors alive through day {GOAL_DAY}. More survivors = more stars (max ⭐⭐⭐)\n"
        "\n📅 Each day\n"
        "  1. Give everyone a job (or press ⚡ Auto-assign)\n"
        "       🎒 Scavenge  🛡 Guard  ✚ Heal  💤 Rest\n"
        "  2. Build with scrap: barricade, garden, rain collector...\n"
        "  3. Decide at the gate: let in / turn away / inspect first\n"
        "  4. End the day → zombies may attack at night\n"
        "\n📜 Key rules\n"
        "  • Everyone eats 1 food + drinks 1 water a day, or loses HP\n"
        "  • Below 40 HP you can't scavenge or guard\n"
        "  • The infected need medicine within 2 days or they turn!\n"
        "  • Infected survivors can't board the helicopter\n"
        "  • Zombies come in 5 levels and get stronger; the Zombie King attacks on the last night\n"
        "\n⚡ Everyone has a power that levels up by working (matching job = x2 XP)")


def how_to_play() -> None:
    """หน้าวิธีเล่น"""
    clear_screen()
    heading("วิธีเล่น", "HOW TO PLAY")
    print(how_to_play_text())
    pause(BACK_TH, BACK_EN)


def history_summary(history: list) -> dict:
    """สรุปประวัติผลเกม: จำนวนเกม ชนะกี่เกม ผลดีที่สุด และค่าเฉลี่ยคนที่รอด"""
    wins = [game for game in history if game["status"] == "won"]
    best = max(history, key=lambda game: (game["stars"], game["rescued"]), default=None)
    return {
        "games": len(history),
        "wins": len(wins),
        "best": best,
        "average": sum(game["rescued"] for game in history) / len(history) if history else 0,
    }


def past_results() -> None:
    """หน้าผลเกมที่ผ่านมา"""
    clear_screen()
    heading("ผลเกมที่ผ่านมา", "PAST RESULTS")
    history = storage.load_history()
    if not history:
        print(get_text("ยังไม่มีเกมที่เล่นจบ ลองเล่นให้จบสักเกมนะ!", "No finished games yet. Go survive one!"))
        pause(BACK_TH, BACK_EN)
        return

    summary = history_summary(history)
    best = summary["best"]
    print(get_text(f"เล่นจบ {summary['games']} เกม   รอดถึงเฮลิคอปเตอร์ {summary['wins']} เกม   "
                   f"เฉลี่ยรอด {summary['average']:.1f} คน/เกม",
                   f"Finished {summary['games']}   rescued {summary['wins']}   "
                   f"average {summary['average']:.1f} survivor(s)/game"))
    print(get_text(f"🏆 ดีที่สุด: เกมที่ {best['game']}  {'⭐' * best['stars'] or '☠'}  รอด {best['rescued']} คน",
                   f"🏆 Best: game {best['game']}  {'⭐' * best['stars'] or '☠'}  {best['rescued']} rescued"))

    print(get_text("\n10 เกมล่าสุด:", "\nLast 10 games:"))
    for game in reversed(history[-10:]):
        if game["status"] == "won":
            result = get_text(f"{'⭐' * game['stars'] or '—'}  รอด {game['rescued']} คน",
                              f"{'⭐' * game['stars'] or '—'}  {game['rescued']} rescued")
        else:
            result = get_text(f"☠ ล่มสลายวันที่ {game['day']}", f"☠ Fell on day {game['day']}")
        print(get_text(f"  เกมที่ {game['game']:>3}  {result}   (เสียชีวิต {game['deaths']}, รับคนเพิ่ม {game['joined']})",
                       f"  Game {game['game']:>3}  {result}   (died {game['deaths']}, joined {game['joined']})"))
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
            print(get_text("บันทึกแล้ว อย่าเปิดประตูให้ใครนะ 🧟", "Saved. Don't open the door for anyone 🧟"))
            break
        else:
            print(get_text("ไม่มีเมนูนี้", "Invalid option."))
            pause(BACK_TH, BACK_EN)


# ---------- หน้าเล่นเกม (แต่ละวัน) ----------

def display_dashboard() -> None:
    """แดชบอร์ดของวันนี้: ทรัพยากร + คาดการณ์ และสถานะทุกคนในหน้าเดียว"""
    state = storage.state
    print("=" * 62)
    print(get_text(f"  🧟 LAST SHELTER   วันที่ {state['day']}/{GOAL_DAY}   👥 {len(state['survivors'])}/{MAX_CAMP}",
                   f"  🧟 LAST SHELTER   Day {state['day']}/{GOAL_DAY}   👥 {len(state['survivors'])}/{MAX_CAMP}"))
    print("=" * 62)
    res = state["resources"]
    print(f" {RESOURCES['food']['icon']}{res['food']} ({camp.days_text('food')})   "
          f"{RESOURCES['water']['icon']}{res['water']} ({camp.days_text('water')})   "
          f"{RESOURCES['scrap']['icon']}{res['scrap']}   {RESOURCES['medicine']['icon']}{res['medicine']}")
    print("-" * 62)
    for person in state["survivors"]:
        print(f" {person['name']:<9} HP {survivors.hp_bar(person['hp'], 6)} {person['hp']:>3}/{MAX_HP}"
              f"  {survivors.job_label(person['job']):<16} {powers.power_label(person)}")
        skills = "  ".join(f"{tr(SKILLS[s])} {survivors.stars(level)}" for s, level in person["skills"].items())
        print(f"           {skills}")
        if person["infected"]:
            print(f"           {survivors.infection_text(person)}")
    if state["wanderer"]:
        print(get_text(f"\n 🚶 {state['wanderer']['name']} รออยู่ที่ประตู!", f"\n 🚶 {state['wanderer']['name']} is waiting at the gate!"))
    print("-" * 62)
    print(get_text(" 1. ⚡ จัดงานอัตโนมัติ", " 1. ⚡ Auto-assign"))
    print(get_text(" 2. ✍ มอบหมายงานเอง", " 2. ✍ Assign a job"))
    print(get_text(" 3. 🔨 สร้าง", " 3. 🔨 Build"))
    print(get_text(" 4. 🚪 ประตู", " 4. 🚪 Gate"))
    print(get_text(" 5. ▶ จบวัน", " 5. ▶ End day"))
    print(get_text(" 6. ⋯ อื่นๆ", " 6. ⋯ More"))
    print(get_text(" 0. พักเกม (กลับหน้าแรก)", " 0. Pause (back to title)"))


def more_menu() -> None:
    """เมนูอื่นๆ: ข้อมูลละเอียด บันทึก เปลี่ยนชื่อ ไล่ออก"""
    actions = {"1": survivors.view_survivors, "2": camp.view_status, "3": day.camp_log,
               "4": survivors.rename_survivor, "5": survivors.exile_survivor}
    while True:
        clear_screen()
        heading("อื่นๆ", "MORE")
        print(get_text("1. ดูข้อมูลผู้รอดชีวิตแบบละเอียด", "1. Survivor details"))
        print(get_text("2. สถานะศูนย์ & คาดการณ์", "2. Shelter status & forecast"))
        print(get_text("3. บันทึกศูนย์พักพิง (สถิติ)", "3. Shelter log (stats)"))
        print(get_text("4. เปลี่ยนชื่อ", "4. Rename"))
        print(get_text("5. ไล่ออกจากศูนย์", "5. Exile"))
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
    """ลูปหน้าเล่นเกม วนจนกว่าผู้เล่นจะพักเกม หรือเกมจบ"""
    actions = {"1": survivors.auto_assign, "2": survivors.assign_job, "3": camp.build,
               "4": survivors.gate, "5": day.end_day}
    # กฎ: เล่นได้เฉพาะตอนเกมยังไม่จบ (ชนะ/แพ้แล้วกลับหน้าแรก)
    while storage.state["status"] == "playing":
        clear_screen()
        display_dashboard()
        choice = input(get_text("\nเลือก: ", "\nChoose: ")).strip()
        if choice in actions:
            clear_screen()
            actions[choice]()
            pause(BACK_TH, BACK_EN)
        elif choice == "6":
            more_menu()
        elif choice == "0":
            storage.save_game()
            return
        else:
            print(get_text("ไม่มีเมนูนี้", "Invalid option."))
            pause(BACK_TH, BACK_EN)
