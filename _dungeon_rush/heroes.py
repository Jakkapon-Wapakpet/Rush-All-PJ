#!/usr/bin/env python3
"""
Heroes Module - DUNGEON RUSH
จัดการทีมฮีโร่: ดูทีม รับสมัคร เปลี่ยนชื่อ ไล่ออก และพักฟื้นที่โรงเตี๊ยม
Party management: view, recruit, rename, dismiss, and rest at the inn.
"""

from language import get_text, clear_screen, pause
from data import HERO_CLASSES, ITEMS, ELEMENTS, MAX_PARTY, tr
from ui import heading, choose_from_list, ask_yes_no
import storage

# ค่าพักที่โรงเตี๊ยมต่อฮีโร่ 1 คนที่ HP ไม่เต็ม
INN_PRICE = 10
# ความยาวชื่อฮีโร่สูงสุด
MAX_NAME_LENGTH = 12


def class_name(class_key: str) -> str:
    """ชื่ออาชีพตามภาษาปัจจุบัน"""
    return tr(HERO_CLASSES[class_key]["name"])


def find_bag_item(uid):
    """หาไอเทมในกระเป๋าจากเลขประจำไอเทม คืนค่า dict หรือ None หากไม่พบ"""
    for item in storage.state["bag"]:
        if item["uid"] == uid:
            return item
    return None


def equipped_item(hero: dict, slot: str):
    """ข้อมูลไอเทม (จาก ITEMS) ที่ฮีโร่ใส่อยู่ในช่อง 'weapon' หรือ 'armor' หรือ None"""
    item = find_bag_item(hero[slot])
    if item is None:
        return None
    return ITEMS[item["key"]]


def hero_attack(hero: dict) -> int:
    """พลังโจมตีรวม = ATK ของฮีโร่ + ATK ของอาวุธ"""
    weapon = equipped_item(hero, "weapon")
    return hero["atk"] + (weapon["atk"] if weapon else 0)


def hero_defense(hero: dict) -> int:
    """พลังป้องกันรวม = DEF ของฮีโร่ + DEF ของชุดเกราะ"""
    armor = equipped_item(hero, "armor")
    return hero["def"] + (armor["def"] if armor else 0)


def hero_element(hero: dict) -> str:
    """ธาตุของการโจมตี ขึ้นกับอาวุธ (ไม่มีอาวุธ = กายภาพ)"""
    weapon = equipped_item(hero, "weapon")
    return weapon["element"] if weapon else "physical"


def holder_of(uid):
    """ฮีโร่ที่กำลังใส่ไอเทมชิ้นนี้อยู่ หรือ None หากไม่มีใครใส่"""
    for hero in storage.state["heroes"]:
        if uid in (hero["weapon"], hero["armor"]):
            return hero
    return None


def party_power() -> dict:
    """รวมพลังของทั้งทีม: HP ปัจจุบัน, HP สูงสุด, ATK และ DEF"""
    power = {"hp": 0, "max_hp": 0, "atk": 0, "def": 0}
    for hero in storage.state["heroes"]:
        power["hp"] += hero["hp"]
        power["max_hp"] += hero["max_hp"]
        power["atk"] += hero_attack(hero)
        power["def"] += hero_defense(hero)
    return power


def xp_needed(level: int) -> int:
    """XP ที่ต้องใช้เพื่อขึ้นเลเวลถัดไป"""
    return level * 40


def gain_xp(hero: dict, amount: int) -> int:
    """เพิ่ม XP ให้ฮีโร่ เลเวลอัปถ้าครบ และคืนค่าจำนวนเลเวลที่เพิ่มขึ้น"""
    hero["xp"] += amount
    levels = 0
    while hero["xp"] >= xp_needed(hero["level"]):
        hero["xp"] -= xp_needed(hero["level"])
        hero["level"] += 1
        growth = HERO_CLASSES[hero["class"]]["growth"]
        hero["max_hp"] += growth["hp"]
        hero["atk"] += growth["atk"]
        hero["def"] += growth["def"]
        hero["hp"] = hero["max_hp"]
        levels += 1
    return levels


def hp_bar(hp: int, max_hp: int, width: int = 12) -> str:
    """แถบพลังชีวิต เช่น ████████░░░░"""
    filled = round(width * hp / max_hp) if max_hp else 0
    return "█" * filled + "░" * (width - filled)


def print_hero(number: int, hero: dict) -> None:
    """แสดงข้อมูลฮีโร่ 1 คน"""
    weapon = equipped_item(hero, "weapon")
    armor = equipped_item(hero, "armor")
    weapon_text = tr(weapon["name"]) if weapon else get_text("มือเปล่า", "bare hands")
    armor_text = tr(armor["name"]) if armor else get_text("ไม่มีเกราะ", "no armor")

    print(f"\n{number}. {hero['name']}  [{class_name(hero['class'])} Lv.{hero['level']}]"
          f"  XP {hero['xp']}/{xp_needed(hero['level'])}")
    print(f"   HP  {hp_bar(hero['hp'], hero['max_hp'])} {hero['hp']}/{hero['max_hp']}")
    print(f"   ATK {hero_attack(hero):<3} ({weapon_text}, {tr(ELEMENTS[hero_element(hero)])})")
    print(f"   DEF {hero_defense(hero):<3} ({armor_text})")


def view_party() -> None:
    """แสดงฮีโร่ทุกคนในทีม และพลังรวม"""
    heading("ทีมฮีโร่", "YOUR PARTY")
    for number, hero in enumerate(storage.state["heroes"], start=1):
        print_hero(number, hero)

    power = party_power()
    print(f"\n{get_text('พลังรวมของทีม', 'Party total')}:  "
          f"HP {power['hp']}/{power['max_hp']}  ATK {power['atk']}  DEF {power['def']}")
    print(f"{get_text('ทอง', 'Gold')}: {storage.state['gold']}")


def validate_hero_name(name: str) -> str:
    """ตรวจชื่อฮีโร่ คืนข้อความผิดพลาด หรือ "" หากใช้ได้"""
    if not name:
        return get_text("ชื่อห้ามว่าง", "Name cannot be empty.")
    if len(name) > MAX_NAME_LENGTH:
        return get_text(f"ชื่อยาวได้ไม่เกิน {MAX_NAME_LENGTH} ตัวอักษร",
                        f"Name must be at most {MAX_NAME_LENGTH} characters.")
    for hero in storage.state["heroes"]:
        if hero["name"].lower() == name.lower():
            return get_text("มีฮีโร่ชื่อนี้อยู่แล้ว", "A hero with this name already exists.")
    return ""


def check_party_space() -> str:
    """กฎ: ทีมมีได้ไม่เกิน MAX_PARTY คน คืนข้อความผิดพลาด หรือ "" หากยังรับเพิ่มได้"""
    if len(storage.state["heroes"]) >= MAX_PARTY:
        return get_text(f"ทีมเต็มแล้ว (สูงสุด {MAX_PARTY} คน)", f"Your party is full (max {MAX_PARTY}).")
    return ""


def do_recruit(class_key: str, name: str) -> str:
    """รับฮีโร่เข้าทีม (ใช้ร่วมกันทั้ง Terminal และ GUI) คืนข้อความผิดพลาด หรือ "" หากสำเร็จ"""
    info = HERO_CLASSES[class_key]
    error = check_party_space() or storage.check_gold(info["cost"]) or validate_hero_name(name)
    if error:
        return error

    storage.state["heroes"].append({
        "name": name, "class": class_key, "level": 1, "xp": 0,
        "hp": info["hp"], "max_hp": info["hp"], "atk": info["atk"], "def": info["def"],
        "weapon": None, "armor": None,
    })
    storage.spend_gold(info["cost"])
    storage.save_game()
    return ""


def recruit_hero() -> None:
    """รับสมัครฮีโร่ใหม่เข้าทีม"""
    heading("รับสมัครฮีโร่", "RECRUIT A HERO")
    error = check_party_space()
    if error:
        print(error)
        return

    class_keys = list(HERO_CLASSES)
    for number, key in enumerate(class_keys, start=1):
        info = HERO_CLASSES[key]
        print(f"{number}. {tr(info['name']):<8} {info['cost']:>3} {get_text('ทอง', 'gold')}"
              f"   HP {info['hp']}  ATK {info['atk']}  DEF {info['def']}   - {tr(info['about'])}")
    print(f"\n{get_text('ทองที่มี', 'Your gold')}: {storage.state['gold']}")

    class_key = choose_from_list(class_keys, "เลือกอาชีพ", "Choose a class")
    if class_key is None:
        return

    # ตรวจทองก่อนถามชื่อ จะได้ไม่ต้องพิมพ์ชื่อเปล่าๆ
    error = storage.check_gold(HERO_CLASSES[class_key]["cost"])
    if error:
        print(error)
        return

    name = input(get_text("ตั้งชื่อฮีโร่: ", "Hero name: ")).strip()
    error = do_recruit(class_key, name)
    if error:
        print(error)
        return
    print(get_text(f"{name} เข้าร่วมทีมแล้ว!", f"{name} joined your party!"))


def do_rename(hero: dict, name: str) -> str:
    """เปลี่ยนชื่อฮีโร่ คืนข้อความผิดพลาด หรือ "" หากสำเร็จ"""
    error = validate_hero_name(name)
    if error:
        return error
    hero["name"] = name
    storage.save_game()
    return ""


def rename_hero() -> None:
    """เปลี่ยนชื่อฮีโร่"""
    heading("เปลี่ยนชื่อฮีโร่", "RENAME A HERO")
    for number, hero in enumerate(storage.state["heroes"], start=1):
        print(f"{number}. {hero['name']} ({class_name(hero['class'])})")

    hero = choose_from_list(storage.state["heroes"], "เลือกฮีโร่", "Choose a hero")
    if hero is None:
        return

    old_name = hero["name"]
    name = input(get_text("ชื่อใหม่: ", "New name: ")).strip()
    error = do_rename(hero, name)
    if error:
        print(error)
        return
    print(get_text(f"เปลี่ยนชื่อ {old_name} เป็น {name} แล้ว", f"{old_name} is now called {name}."))


def check_can_dismiss() -> str:
    """กฎ: ทีมต้องเหลือฮีโร่อย่างน้อย 1 คน คืนข้อความผิดพลาด หรือ "" หากไล่ออกได้"""
    if len(storage.state["heroes"]) <= 1:
        return get_text("ไล่ออกไม่ได้ ทีมต้องมีฮีโร่อย่างน้อย 1 คน", "You cannot dismiss your last hero.")
    return ""


def do_dismiss(hero: dict) -> str:
    """ไล่ฮีโร่ออก (ไอเทมที่ใส่อยู่กลับเข้ากระเป๋า) คืนข้อความผิดพลาด หรือ "" หากสำเร็จ"""
    error = check_can_dismiss()
    if error:
        return error
    storage.state["heroes"].remove(hero)
    storage.save_game()
    return ""


def dismiss_hero() -> None:
    """ไล่ฮีโร่ออกจากทีม (ไอเทมที่ใส่อยู่จะกลับเข้ากระเป๋า)"""
    heading("ไล่ฮีโร่ออก", "DISMISS A HERO")
    error = check_can_dismiss()
    if error:
        print(error)
        return

    for number, hero in enumerate(storage.state["heroes"], start=1):
        print(f"{number}. {hero['name']} ({class_name(hero['class'])} Lv.{hero['level']})")

    hero = choose_from_list(storage.state["heroes"], "เลือกฮีโร่", "Choose a hero")
    if hero is None:
        return

    if not ask_yes_no(f"ยืนยันไล่ {hero['name']} ออก? ไม่ได้รับทองคืน", f"Dismiss {hero['name']}? No refund."):
        print(get_text("ยกเลิก", "Cancelled."))
        return

    error = do_dismiss(hero)
    if error:
        print(error)
        return
    print(get_text(f"{hero['name']} ออกจากทีมแล้ว ไอเทมที่ใส่อยู่กลับเข้ากระเป๋า",
                   f"{hero['name']} left. Their equipment went back to the bag."))


def tired_heroes() -> list:
    """ฮีโร่ที่ HP ไม่เต็ม"""
    return [hero for hero in storage.state["heroes"] if hero["hp"] < hero["max_hp"]]


def inn_cost() -> int:
    """ค่าพักโรงเตี๊ยม = INN_PRICE x จำนวนฮีโร่ที่ HP ไม่เต็ม"""
    return INN_PRICE * len(tired_heroes())


def do_rest() -> str:
    """พักฟื้น HP ทุกคน คืนข้อความผิดพลาด หรือ "" หากสำเร็จ"""
    if not tired_heroes():
        return get_text("ทุกคน HP เต็มอยู่แล้ว", "Everyone is already at full HP.")
    cost = inn_cost()
    # กฎ: ทองต้องพอจ่ายค่าพัก
    error = storage.check_gold(cost)
    if error:
        return error

    for hero in tired_heroes():
        hero["hp"] = hero["max_hp"]
    storage.spend_gold(cost)
    storage.save_game()
    return ""


def rest_at_inn() -> None:
    """พักที่โรงเตี๊ยม: จ่ายทองเพื่อฟื้น HP ให้เต็มทุกคน"""
    heading("โรงเตี๊ยม", "THE INN")
    tired = tired_heroes()
    if not tired:
        print(get_text("ทุกคน HP เต็มอยู่แล้ว", "Everyone is already at full HP."))
        return

    for hero in tired:
        print(f"- {hero['name']}: HP {hero['hp']}/{hero['max_hp']}")
    print(get_text(f"\nค่าพัก {INN_PRICE} ทองต่อคน รวม {inn_cost()} ทอง (มี {storage.state['gold']})",
                   f"\n{INN_PRICE} gold per hero, {inn_cost()} gold total (you have {storage.state['gold']})"))
    error = storage.check_gold(inn_cost())
    if error:
        print(error)
        return

    if not ask_yes_no("พักผ่อน?", "Rest?"):
        print(get_text("ยกเลิก", "Cancelled."))
        return

    error = do_rest()
    print(error or get_text("ทุกคนพักผ่อนจน HP เต็มแล้ว", "Your party is fully rested."))


def party_menu() -> None:
    """เมนูทีมฮีโร่"""
    actions = {"1": view_party, "2": recruit_hero, "3": rename_hero, "4": dismiss_hero}

    while True:
        clear_screen()
        heading("ทีมฮีโร่", "PARTY")
        print(get_text("1. ดูทีม", "1. View Party"))
        print(get_text("2. รับสมัครฮีโร่", "2. Recruit a Hero"))
        print(get_text("3. เปลี่ยนชื่อฮีโร่", "3. Rename a Hero"))
        print(get_text("4. ไล่ฮีโร่ออก", "4. Dismiss a Hero"))
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
