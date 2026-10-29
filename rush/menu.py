#!/usr/bin/env python3
"""
Menu Module - GHOST REALM (มิติผี)
2 หน้าจอหลัก: หน้าแรก (เริ่ม/เล่นต่อ วิธีเล่น ผลเกม ภาษา) และหน้าเล่นเกมในแต่ละวัน (แดชบอร์ด + คำสั่ง)
Two main screens: the title screen and the in-game day screen (dashboard + actions).
"""

from language import get_text, clear_screen, pause, choose_language
from data import (RESOURCES, SKILLS, DIFFICULTIES, COUNTERS, LIGHTS, VOWS, MAX_PEOPLE, MAX_HP, MAX_GRUDGE,
                  TICKET_PIECES, tr)
from ui import heading, ask_yes_no, choose_from_list, show_banner
import sala
import day
import realm
import storage
import survivors

BACK_TH, BACK_EN = "\nกด Enter เพื่อกลับ...", "\nPress Enter to go back..."


# ---------- หน้าแรก ----------

def display_title() -> None:
    """แสดงหน้าแรก (ข้อ 1 คือเริ่มเล่น/เล่นต่อเสมอ)"""
    state = storage.state
    print("=" * 62)
    show_banner()
    print()
    print(get_text("                    👻   มิ ติ ผี   👻", "              👻   G H O S T   R E A L M   👻"))
    print(get_text(f"             รอดให้ครบ {storage.goal_day()} วัน แล้วประตูมิติจะเปิด",
                   f"           Survive {storage.goal_day()} days until the portal opens"))
    print("=" * 62)
    if state["status"] == "playing" and state["day"] > 1:
        level = tr(DIFFICULTIES[state["difficulty"]]["name"])
        print(get_text(f" 1. ▶ เล่นต่อ (วันที่ {state['day']}/{storage.goal_day()}, ระดับ{level})",
                       f" 1. ▶ Continue (day {state['day']}/{storage.goal_day()}, {level})"))
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
        duration = get_text(f"{info['days']} วัน", f"{info['days']} days")
        print(f"{number}. {info['icon']} {tr(info['name']):<8} ({duration}) {tr(info['about'])}")
    return choose_from_list(keys, "เลือกระดับ", "Choose a level")


def play() -> None:
    """เล่นต่อจากเซฟ ถ้าเกมเดิมจบแล้วจะให้เลือกระดับแล้วเริ่มเกมใหม่"""
    if storage.state["status"] != "playing":
        level = choose_difficulty()
        if level is None:
            return
        storage.new_game(level)
    day_menu()


def new_game() -> None:
    """เริ่มเกมใหม่ (ถามยืนยันก่อนถ้ามีเกมที่เล่นค้างอยู่)"""
    state = storage.state
    if state["status"] == "playing" and state["day"] > 1 and \
            not ask_yes_no(f"มีเกมค้างอยู่ (วันที่ {state['day']}) เริ่มใหม่เลย? ความคืบหน้าเดิมจะหาย",
                           f"You have a game on day {state['day']}. Start over? Progress will be lost."):
        return
    level = choose_difficulty()
    if level is None:
        return
    storage.new_game(level)
    day_menu()


def how_to_play_text() -> str:
    """ข้อความวิธีเล่น (ใช้ร่วมกันทั้ง Terminal และ GUI)"""
    return get_text(
        f"👻 เรื่องย่อ: เพื่อน 3 คนไปเที่ยวงานฮาโลวีน แล้วเดินเข้าบ้านผีสิงด้วยบัตรฟรีจากคนที่ไม่มีเงา...\n"
        "   ตอนนี้ทุกคนติดอยู่ในมิติผี ต้องหลบอยู่ในศาลาเก่า\n"
        f"🎯 เป้าหมาย: รอดให้ครบ {storage.goal_day()} วัน แล้วประตูมิติจะเปิด ยิ่งพากลับไปได้เยอะ ยิ่งได้ดาวเยอะ (สูงสุด ⭐⭐⭐)\n"
        "\n📅 ในแต่ละวัน\n"
        "  1. มอบงานให้ทุกคน (กด ⚡ จัดงานอัตโนมัติ ได้)\n"
        "       🎒 หาของ  🛡 เฝ้ายาม  ✚ ประพรมน้ำมนต์  💤 พักผ่อน\n"
        "  2. สร้างสิ่งก่อสร้างด้วยธูปเทียน เช่น สายสิญจน์ แปลงผัก ศาลพระภูมิ\n"
        "  3. ตัดสินใจที่ประตู: รับ / ไม่รับ / ส่องดูเงาก่อน\n"
        "  4. จบวัน → กลางคืนผีอาจบุก\n"
        "\n📜 กฎสำคัญ\n"
        "  • ทุกคนกินอาหาร 1 + ดื่มน้ำ 1 ต่อวัน ถ้าไม่พอจะเสีย HP\n"
        "  • HP ต่ำกว่า 40 ออกไปหาของ/เฝ้ายามไม่ได้\n"
        "  • ถูกผีสิงแล้วต้องได้น้ำมนต์ภายใน 2 วัน ไม่งั้นกลายเป็นผี!\n"
        "  • คนที่ถูกผีสิงผ่านประตูมิติกลับบ้านไม่ได้\n"
        "  • ผีมี 5 เลเวล ยิ่งหลายวันยิ่งดุ และเสือสมิงบุกคืนสุดท้ายแน่นอน\n"
        "\n🔥 ระดับปกติและฝันร้าย (เปิดทุกระบบ)\n"
        "  • ออกไปหาของต้องเลือกสถานที่: ตลาด บ่อน้ำ วัดร้าง ป่าช้า (ยิ่งเสี่ยงยิ่งได้ของดี ไปซ้ำของจะลดลง)\n"
        "  • ทุกเช้ามีลางบอกว่าผีตัวไหนจะนำฝูง (ไม่แม่นเสมอ) ถ้ามีคนถูกผีสิง เขาจะกระซิบบอกตัวจริง\n"
        "  • เตรียมของแก้ผีให้ถูกตัว และเลือกไฟ: ดับไฟซ่อน / ตะเกียง / จุดไฟรอบศาลา\n"
        "  • บนบานที่ศาลเจ้าที่ได้ แต่ต้องแก้บนภายใน 3 วัน ไม่งั้นโดนสาป\n"
        "  • ความแค้นของมิติผีเพิ่มเมื่อไปป่าช้า ไล่คนออก หรือผิดคำบน ทำให้ผีเยอะขึ้นและลางหลอกบ่อยขึ้น (ทำบุญเพื่อลด)\n"
        "  • เพื่อนที่ตายอาจกลับมากับฝูงผี และคนแปลกหน้าบางคนเป็นผีปลอมตัวที่เงาดูปกติ\n"
        f"  • เก็บชิ้นส่วนตั๋วครบ {TICKET_PIECES} ชิ้น ประตูบ้านผีสิงจะเปิดให้กลับบ้านก่อน (ดาวพิเศษ +1)",
        f"👻 Story: three friends went to a Halloween fair and took free haunted-house tickets from someone with no shadow...\n"
        "   Now they're trapped in the ghost realm, hiding in an old sala.\n"
        f"🎯 Goal: survive {storage.goal_day()} days until the portal opens. More survivors = more stars (max ⭐⭐⭐)\n"
        "\n📅 Each day\n"
        "  1. Give everyone a job (or press ⚡ Auto-assign)\n"
        "       🎒 Scavenge  🛡 Guard  ✚ Bless  💤 Rest\n"
        "  2. Build with incense: sacred thread, garden, spirit house...\n"
        "  3. Decide at the gate: let in / turn away / check their shadow first\n"
        "  4. End the day → ghosts may attack at night\n"
        "\n📜 Key rules\n"
        "  • Everyone eats 1 food + drinks 1 water a day, or loses HP\n"
        "  • Below 40 HP you can't scavenge or guard\n"
        "  • The possessed need holy water within 2 days or they become ghosts!\n"
        "  • Possessed survivors can't pass through the portal\n"
        "  • Ghosts come in 5 levels and get stronger; the Saming Tiger attacks on the last night\n"
        "\n🔥 Normal and Nightmare (every system on)\n"
        "  • Scavenging means picking a place: market, well, temple, graveyard (riskier = better loot, repeats run dry)\n"
        "  • Each morning an omen hints which ghost leads tonight (not always right); a possessed friend whispers the truth\n"
        "  • Prepare the right counter, and choose the light: lights out / lamp / torches\n"
        "  • Make vows at the spirit shrine, but repay within 3 days or be cursed\n"
        "  • The realm's grudge grows when you visit the graveyard, exile someone, or break a vow (make merit to calm it)\n"
        "  • Fallen friends may return with the horde, and some strangers are ghosts with a normal shadow\n"
        f"  • Collect all {TICKET_PIECES} ticket pieces and the haunted-house door lets you out early (bonus star)")


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
    print(get_text(f"เล่นจบ {summary['games']} เกม   กลับโลกมนุษย์ได้ {summary['wins']} เกม   "
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
            result = get_text(f"☠ ติดอยู่ในมิติผีวันที่ {game['day']}", f"☠ Lost on day {game['day']}")
        if game.get("early"):
            result += get_text(" 🎫 กลับก่อน", " 🎫 early")
        level = tr(DIFFICULTIES[game.get("difficulty", "easy")]["name"])
        print(get_text(f"  เกมที่ {game['game']:>3}  [{level}] {result}   (เสียชีวิต {game['deaths']}, รับคนเพิ่ม {game['joined']})",
                       f"  Game {game['game']:>3}  [{level}] {result}   (died {game['deaths']}, joined {game['joined']})"))
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
            print(get_text("บันทึกแล้ว อย่าเปิดประตูให้ใครนะ 👻", "Saved. Don't open the door for anyone 👻"))
            break
        else:
            print(get_text("ไม่มีเมนูนี้", "Invalid option."))
            pause(BACK_TH, BACK_EN)


# ---------- หน้าเล่นเกม (แต่ละวัน) ----------

def display_dashboard() -> None:
    """แดชบอร์ดของวันนี้: ทรัพยากร + คาดการณ์ และสถานะทุกคนในหน้าเดียว"""
    state = storage.state
    print("=" * 62)
    level = DIFFICULTIES[state["difficulty"]]
    print(get_text(f"  👻 มิติผี   วันที่ {state['day']}/{storage.goal_day()}   👥 {len(state['survivors'])}/{MAX_PEOPLE}   "
                   f"{level['icon']} {tr(level['name'])}",
                   f"  👻 GHOST REALM   Day {state['day']}/{storage.goal_day()}   👥 {len(state['survivors'])}/{MAX_PEOPLE}   "
                   f"{level['icon']} {tr(level['name'])}"))
    print("=" * 62)
    res = state["resources"]
    print(f" {RESOURCES['food']['icon']}{res['food']} ({sala.days_text('food')})   "
          f"{RESOURCES['water']['icon']}{res['water']} ({sala.days_text('water')})   "
          f"{RESOURCES['incense']['icon']}{res['incense']}   {RESOURCES['holy_water']['icon']}{res['holy_water']}")
    if realm.advanced():
        prepared = " ".join(COUNTERS[key]["icon"] for key in state["prepared"]) or "-"
        print(get_text(f" 🌑 แค้น {state['grudge']}/{MAX_GRUDGE}   🎫 ตั๋ว {state['tickets']}/{TICKET_PIECES}   "
                       f"{LIGHTS[state['light']]['icon']} {tr(LIGHTS[state['light']]['name'])}   ของแก้: {prepared}",
                       f" 🌑 Grudge {state['grudge']}/{MAX_GRUDGE}   🎫 Ticket {state['tickets']}/{TICKET_PIECES}   "
                       f"{LIGHTS[state['light']]['icon']} {tr(LIGHTS[state['light']]['name'])}   Counters: {prepared}"))
        if state["vow"]:
            print(get_text(f" 🙏 บน \"{tr(VOWS[state['vow']['wish']]['name'])}\" ไว้ ต้องแก้บนภายในวันที่ {state['vow']['due']}!",
                           f" 🙏 Vow \"{tr(VOWS[state['vow']['wish']]['name'])}\" must be repaid by day {state['vow']['due']}!"))
        if realm.omen_text():
            print(" " + realm.omen_text())
    print("-" * 62)
    for person in state["survivors"]:
        print(f" {person['name']:<9} HP {survivors.hp_bar(person['hp'], 6)} {person['hp']:>3}/{MAX_HP}"
              f"  {survivors.job_text(person)}")
        skills = "  ".join(f"{tr(SKILLS[s])} {survivors.stars(level)}" for s, level in person["skills"].items())
        print(f"           {skills}")
        if person["possessed"]:
            print(f"           {survivors.possession_text(person)}")
    if state["stranger"]:
        print(get_text(f"\n 🚶 {state['stranger']['name']} รออยู่ที่ประตู!", f"\n 🚶 {state['stranger']['name']} is waiting at the gate!"))
    print("-" * 62)
    print(get_text(" 1. ⚡ จัดงานอัตโนมัติ", " 1. ⚡ Auto-assign"))
    print(get_text(" 2. ✍ มอบหมายงานเอง", " 2. ✍ Assign a job"))
    print(get_text(" 3. 🔨 สร้าง", " 3. 🔨 Build"))
    print(get_text(" 4. 🚪 ประตู", " 4. 🚪 Gate"))
    print(get_text(" 5. ▶ จบวัน", " 5. ▶ End day"))
    print(get_text(" 6. ⋯ อื่นๆ", " 6. ⋯ More"))
    if realm.advanced():
        print(get_text(" 7. 🔮 เตรียมรับคืนนี้ (ของแก้ผี / ไฟ)", " 7. 🔮 Prepare for tonight (counters / light)"))
        print(get_text(" 8. 🙏 ศาลเจ้าที่ (บนบาน / แก้บน / ทำบุญ)", " 8. 🙏 Spirit shrine (vow / repay / merit)"))
    print(get_text(" 0. พักเกม (กลับหน้าแรก)", " 0. Pause (back to title)"))


def more_menu() -> None:
    """เมนูอื่นๆ: ข้อมูลละเอียด บันทึก เปลี่ยนชื่อ ไล่ออก"""
    actions = {"1": survivors.view_survivors, "2": sala.view_status, "3": day.shelter_log,
               "4": survivors.rename_survivor, "5": survivors.exile_survivor}
    while True:
        clear_screen()
        heading("อื่นๆ", "MORE")
        print(get_text("1. ดูข้อมูลผู้รอดชีวิตแบบละเอียด", "1. Survivor details"))
        print(get_text("2. สถานะศาลา & คาดการณ์", "2. Sala status & forecast"))
        print(get_text("3. บันทึกศาลา (สถิติ)", "3. Sala log (stats)"))
        print(get_text("4. เปลี่ยนชื่อ", "4. Rename"))
        print(get_text("5. ไล่ออกจากศาลา", "5. Exile"))
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
    actions = {"1": survivors.auto_assign, "2": survivors.assign_job, "3": sala.build,
               "4": survivors.gate, "5": day.end_day}
    advanced_actions = {"7": realm.tonight_menu, "8": realm.shrine_menu}
    # กฎ: เล่นได้เฉพาะตอนเกมยังไม่จบ (ชนะ/แพ้แล้วกลับหน้าแรก)
    while storage.state["status"] == "playing":
        clear_screen()
        display_dashboard()
        choice = input(get_text("\nเลือก: ", "\nChoose: ")).strip()
        if choice in advanced_actions and realm.advanced():
            clear_screen()
            advanced_actions[choice]()
            pause(BACK_TH, BACK_EN)
        elif choice in actions:
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
