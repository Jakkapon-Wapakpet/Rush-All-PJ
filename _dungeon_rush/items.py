#!/usr/bin/env python3
"""
Items Module - DUNGEON RUSH
ร้านค้าและกระเป๋า: ดู/กรอง/เรียงสินค้า ซื้อ ขาย สวมใส่ ถอด และจัดอันดับไอเทมที่คุ้มที่สุด
Shop and bag: browse, buy, sell, equip, unequip, and rank best-value items.
"""

from language import get_text, clear_screen, pause
from data import ITEMS, ELEMENTS, HERO_CLASSES, BAG_SIZE, tr
from ui import heading, choose_from_list, ask_yes_no
import heroes
import storage

# ขายคืนได้ครึ่งราคา
SELL_RATE = 0.5

ITEM_TYPES = {
    "weapon": {"th": "อาวุธ", "en": "Weapon"},
    "armor": {"th": "เกราะ", "en": "Armor"},
    "potion": {"th": "ยา", "en": "Potion"},
}


def item_power(key: str) -> int:
    """ค่าพลังหลักของไอเทม: ATK ของอาวุธ, DEF ของเกราะ, HP ที่ฟื้นของยา"""
    item = ITEMS[key]
    return item.get("atk", item.get("def", item.get("heal", 0)))


def describe_item(key: str) -> str:
    """ข้อความสรุปค่าสถานะของไอเทม 1 บรรทัด"""
    item = ITEMS[key]
    if item["type"] == "weapon":
        stat = f"ATK +{item['atk']} {tr(ELEMENTS[item['element']])}"
    elif item["type"] == "armor":
        stat = f"DEF +{item['def']}"
    else:
        stat = get_text(f"ฟื้น HP {item['heal']} อัตโนมัติ", f"heals {item['heal']} HP automatically")
    users = ", ".join(tr(HERO_CLASSES[c]["name"]) for c in item["classes"])
    return f"{stat:<18} Lv.{item['level']}  [{users}]"


def shop_items(type_filter: str = "all", sort_by: str = "price", affordable_only: bool = False) -> list:
    """
    รายการรหัสสินค้าในร้าน หลังกรองและเรียงลำดับแล้ว
      type_filter     = 'all' / 'weapon' / 'armor' / 'potion'
      sort_by         = 'price' (ถูก -> แพง) / 'power' (แรง -> อ่อน) / 'level' (ต่ำ -> สูง)
      affordable_only = แสดงเฉพาะของที่ทองพอซื้อ
    """
    keys = []
    for key, item in ITEMS.items():
        if type_filter != "all" and item["type"] != type_filter:
            continue
        if affordable_only and item["price"] > storage.state["gold"]:
            continue
        keys.append(key)

    if sort_by == "power":
        keys.sort(key=lambda k: -item_power(k))
    elif sort_by == "level":
        keys.sort(key=lambda k: (ITEMS[k]["level"], ITEMS[k]["price"]))
    else:
        keys.sort(key=lambda k: ITEMS[k]["price"])
    return keys


def best_value_items(limit: int = 5) -> list:
    """จัดอันดับอาวุธ/เกราะที่คุ้มที่สุด (ค่าพลังต่อ 100 ทอง) คืนค่า [(รหัส, ความคุ้ม), ...]"""
    ranking = []
    for key, item in ITEMS.items():
        if item["type"] in ("weapon", "armor"):
            ranking.append((key, item_power(key) / item["price"] * 100))
    ranking.sort(key=lambda pair: pair[1], reverse=True)
    return ranking[:limit]


def count_potions() -> int:
    """จำนวนยาในกระเป๋า"""
    return sum(1 for item in storage.state["bag"] if item["key"] == "potion")


def use_potions(amount: int) -> None:
    """ลบยาออกจากกระเป๋าตามจำนวนที่ใช้ไปในการต่อสู้"""
    for _ in range(amount):
        for item in storage.state["bag"]:
            if item["key"] == "potion":
                storage.state["bag"].remove(item)
                break


def print_shop_list(keys: list) -> None:
    """แสดงรายการสินค้าพร้อมหมายเลข"""
    for number, key in enumerate(keys, start=1):
        item = ITEMS[key]
        print(f"{number:>2}. {tr(item['name']):<16} {item['price']:>4} {get_text('ทอง', 'g')}"
              f"   {tr(ITEM_TYPES[item['type']]):<6} {describe_item(key)}")


def browse_shop() -> None:
    """ดูสินค้าโดยเลือกประเภทและวิธีเรียง"""
    heading("ดูสินค้า", "BROWSE THE SHOP")
    print(get_text("ประเภท: 1. ทั้งหมด  2. อาวุธ  3. เกราะ  4. ยา",
                   "Type: 1. All  2. Weapons  3. Armor  4. Potions"))
    type_filter = {"1": "all", "2": "weapon", "3": "armor", "4": "potion"}.get(
        input(get_text("เลือกประเภท: ", "Choose type: ")).strip())
    if type_filter is None:
        print(get_text("ตัวเลือกไม่ถูกต้อง", "Invalid option."))
        return

    print(get_text("เรียงตาม: 1. ราคา  2. ค่าพลัง  3. เลเวล", "Sort by: 1. Price  2. Power  3. Level"))
    sort_by = {"1": "price", "2": "power", "3": "level"}.get(
        input(get_text("เลือกวิธีเรียง: ", "Choose sort: ")).strip())
    if sort_by is None:
        print(get_text("ตัวเลือกไม่ถูกต้อง", "Invalid option."))
        return

    affordable = ask_yes_no("แสดงเฉพาะของที่ซื้อไหว?", "Only items you can afford?")

    keys = shop_items(type_filter, sort_by, affordable)
    print()
    if not keys:
        print(get_text("ไม่มีสินค้าที่ตรงเงื่อนไข", "No items match."))
        return
    print_shop_list(keys)
    print(f"\n{get_text('ทอง', 'Gold')}: {storage.state['gold']}")


def show_best_value() -> None:
    """แสดงอาวุธ/เกราะที่คุ้มค่าที่สุด 5 อันดับ"""
    heading("ของคุ้มที่สุด", "BEST VALUE")
    print(get_text("(ค่าพลังที่ได้ต่อทอง 100)\n", "(power per 100 gold)\n"))
    for rank, (key, value) in enumerate(best_value_items(), start=1):
        item = ITEMS[key]
        print(f"{rank}. {tr(item['name']):<16} {value:>5.1f}   ({item['price']} {get_text('ทอง', 'g')}, "
              f"{describe_item(key)})")


def do_buy(key: str) -> str:
    """ซื้อสินค้าเข้ากระเป๋า (ใช้ร่วมกันทั้ง Terminal และ GUI) คืนข้อความผิดพลาด หรือ "" หากสำเร็จ"""
    price = ITEMS[key]["price"]
    # กฎ: ทองต้องพอ
    error = storage.check_gold(price)
    if error:
        return error
    # กฎ: กระเป๋ามีจำกัด
    if len(storage.state["bag"]) >= BAG_SIZE:
        return get_text(f"กระเป๋าเต็ม ({BAG_SIZE} ช่อง) ขายของออกก่อน",
                        f"Your bag is full ({BAG_SIZE} slots). Sell something first.")

    storage.state["bag"].append({"uid": storage.state["next_uid"], "key": key})
    storage.state["next_uid"] += 1
    storage.spend_gold(price)
    storage.save_game()
    return ""


def buy_item() -> None:
    """ซื้อสินค้าเข้ากระเป๋า"""
    heading("ซื้อของ", "BUY")
    keys = shop_items()
    print_shop_list(keys)
    print(f"\n{get_text('ทอง', 'Gold')}: {storage.state['gold']}   "
          f"{get_text('กระเป๋า', 'Bag')}: {len(storage.state['bag'])}/{BAG_SIZE}")

    key = choose_from_list(keys, "เลือกสินค้า", "Choose an item")
    if key is None:
        return

    error = do_buy(key)
    if error:
        print(error)
        return
    print(get_text(f"ซื้อ {tr(ITEMS[key]['name'])} แล้ว (เหลือ {storage.state['gold']} ทอง)",
                   f"Bought {tr(ITEMS[key]['name'])}. ({storage.state['gold']} gold left)"))


def print_bag() -> None:
    """แสดงไอเทมในกระเป๋าพร้อมหมายเลข และบอกว่าใครใส่อยู่"""
    for number, bag_item in enumerate(storage.state["bag"], start=1):
        item = ITEMS[bag_item["key"]]
        holder = heroes.holder_of(bag_item["uid"])
        worn = get_text(f"  ← {holder['name']} ใส่อยู่", f"  ← worn by {holder['name']}") if holder else ""
        print(f"{number:>2}. {tr(item['name']):<16} {describe_item(bag_item['key'])}{worn}")


def view_bag() -> None:
    """ดูกระเป๋า"""
    heading("กระเป๋า", "BAG")
    if not storage.state["bag"]:
        print(get_text("กระเป๋าว่าง", "Your bag is empty."))
    else:
        print_bag()
    print(f"\n{get_text('ช่องที่ใช้', 'Slots used')}: {len(storage.state['bag'])}/{BAG_SIZE}"
          f"   {get_text('ทอง', 'Gold')}: {storage.state['gold']}")


def sell_price(key: str) -> int:
    """ราคาขายคืน (ครึ่งราคา)"""
    return int(ITEMS[key]["price"] * SELL_RATE)


def do_sell(bag_item: dict) -> str:
    """ขายไอเทมในกระเป๋า คืนข้อความผิดพลาด หรือ "" หากสำเร็จ"""
    # กฎ: ขายของที่มีคนใส่อยู่ไม่ได้
    holder = heroes.holder_of(bag_item["uid"])
    if holder is not None:
        return get_text(f"{holder['name']} ใส่อยู่ ต้องถอดออกก่อน",
                        f"{holder['name']} is wearing it. Unequip it first.")
    storage.state["bag"].remove(bag_item)
    storage.state["gold"] += sell_price(bag_item["key"])
    storage.save_game()
    return ""


def sell_item() -> None:
    """ขายไอเทมในกระเป๋า ได้ทองคืนครึ่งราคา"""
    heading("ขายของ", "SELL")
    if not storage.state["bag"]:
        print(get_text("กระเป๋าว่าง ไม่มีอะไรให้ขาย", "Your bag is empty."))
        return
    print_bag()

    bag_item = choose_from_list(storage.state["bag"], "เลือกของที่จะขาย", "Choose an item to sell")
    if bag_item is None:
        return

    error = do_sell(bag_item)
    if error:
        print(error)
        return
    item = ITEMS[bag_item["key"]]
    refund = sell_price(bag_item["key"])
    print(get_text(f"ขาย {tr(item['name'])} ได้ {refund} ทอง", f"Sold {tr(item['name'])} for {refund} gold."))


def check_can_equip(hero: dict, key: str) -> str:
    """ตรวจว่าฮีโร่ใส่ไอเทมนี้ได้ไหม คืนข้อความผิดพลาด หรือ "" หากใส่ได้"""
    item = ITEMS[key]
    if item["type"] == "potion":
        return get_text("ยาใส่ไม่ได้ จะถูกใช้อัตโนมัติในการต่อสู้",
                        "Potions are used automatically in battle.")
    # กฎ: อาชีพต้องตรง
    if hero["class"] not in item["classes"]:
        return get_text(f"{heroes.class_name(hero['class'])} ใช้ {tr(item['name'])} ไม่ได้",
                        f"A {heroes.class_name(hero['class'])} cannot use {tr(item['name'])}.")
    # กฎ: เลเวลต้องถึง
    if hero["level"] < item["level"]:
        return get_text(f"ต้องเลเวล {item['level']} ขึ้นไป ({hero['name']} เลเวล {hero['level']})",
                        f"Requires level {item['level']} ({hero['name']} is level {hero['level']}).")
    return ""


def do_equip(hero: dict, bag_item: dict) -> str:
    """ให้ฮีโร่ใส่ไอเทม (แทนชิ้นเดิมในช่องเดียวกัน) คืนข้อความผิดพลาด หรือ "" หากสำเร็จ"""
    error = check_can_equip(hero, bag_item["key"])
    if error:
        return error
    # กฎ: ไอเทม 1 ชิ้นใส่ได้ทีละคน
    holder = heroes.holder_of(bag_item["uid"])
    if holder is not None and holder is not hero:
        return get_text(f"{holder['name']} ใส่อยู่แล้ว", f"{holder['name']} is already wearing it.")

    hero[ITEMS[bag_item["key"]]["type"]] = bag_item["uid"]
    storage.save_game()
    return ""


def equip_item() -> None:
    """ให้ฮีโร่สวมใส่อาวุธหรือเกราะจากกระเป๋า"""
    heading("สวมใส่", "EQUIP")
    gear = [b for b in storage.state["bag"] if ITEMS[b["key"]]["type"] in ("weapon", "armor")]
    if not gear:
        print(get_text("ไม่มีอาวุธหรือเกราะในกระเป๋า ไปซื้อที่ร้านก่อน",
                       "No weapons or armor in your bag. Visit the shop first."))
        return

    for number, hero in enumerate(storage.state["heroes"], start=1):
        print(f"{number}. {hero['name']} ({heroes.class_name(hero['class'])} Lv.{hero['level']})")
    hero = choose_from_list(storage.state["heroes"], "เลือกฮีโร่", "Choose a hero")
    if hero is None:
        return

    print()
    for number, bag_item in enumerate(gear, start=1):
        holder = heroes.holder_of(bag_item["uid"])
        worn = get_text(f"  ← {holder['name']} ใส่อยู่", f"  ← worn by {holder['name']}") if holder else ""
        print(f"{number}. {tr(ITEMS[bag_item['key']]['name']):<16} {describe_item(bag_item['key'])}{worn}")
    bag_item = choose_from_list(gear, "เลือกไอเทม", "Choose an item")
    if bag_item is None:
        return

    error = do_equip(hero, bag_item)
    if error:
        print(error)
        return
    print(get_text(f"{hero['name']} ใส่ {tr(ITEMS[bag_item['key']]['name'])} แล้ว  (ATK {heroes.hero_attack(hero)}"
                   f"  DEF {heroes.hero_defense(hero)})",
                   f"{hero['name']} equipped {tr(ITEMS[bag_item['key']]['name'])}.  (ATK {heroes.hero_attack(hero)}"
                   f"  DEF {heroes.hero_defense(hero)})"))


def do_unequip(hero: dict, slot: str) -> str:
    """ถอดอุปกรณ์ช่อง 'weapon' หรือ 'armor' คืนข้อความผิดพลาด หรือ "" หากสำเร็จ"""
    if hero[slot] is None:
        return get_text("ช่องนี้ว่างอยู่แล้ว", "Nothing equipped there.")
    hero[slot] = None
    storage.save_game()
    return ""


def unequip_item() -> None:
    """ถอดอาวุธหรือเกราะของฮีโร่ (ไอเทมยังอยู่ในกระเป๋า)"""
    heading("ถอดอุปกรณ์", "UNEQUIP")
    for number, hero in enumerate(storage.state["heroes"], start=1):
        print(f"{number}. {hero['name']}")
    hero = choose_from_list(storage.state["heroes"], "เลือกฮีโร่", "Choose a hero")
    if hero is None:
        return

    print(get_text("1. อาวุธ  2. เกราะ", "1. Weapon  2. Armor"))
    slot = {"1": "weapon", "2": "armor"}.get(input(get_text("เลือก: ", "Choose: ")).strip())
    if slot is None:
        print(get_text("ตัวเลือกไม่ถูกต้อง", "Invalid option."))
        return
    error = do_unequip(hero, slot)
    if error:
        print(error)
        return
    print(get_text("ถอดแล้ว ไอเทมกลับเข้ากระเป๋า", "Unequipped. The item is back in your bag."))


def shop_menu() -> None:
    """เมนูร้านค้า"""
    actions = {"1": browse_shop, "2": buy_item, "3": sell_item, "4": show_best_value}
    while True:
        clear_screen()
        heading(f"ร้านค้า   (ทอง {storage.state['gold']})", f"SHOP   (gold {storage.state['gold']})")
        print(get_text("1. ดูสินค้า (กรอง/เรียง)", "1. Browse (filter/sort)"))
        print(get_text("2. ซื้อของ", "2. Buy"))
        print(get_text("3. ขายของ", "3. Sell"))
        print(get_text("4. ของคุ้มที่สุด", "4. Best Value"))
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


def bag_menu() -> None:
    """เมนูกระเป๋าและการสวมใส่"""
    actions = {"1": view_bag, "2": equip_item, "3": unequip_item}
    while True:
        clear_screen()
        heading("กระเป๋า / สวมใส่", "BAG / EQUIPMENT")
        print(get_text("1. ดูกระเป๋า", "1. View Bag"))
        print(get_text("2. สวมใส่อุปกรณ์", "2. Equip"))
        print(get_text("3. ถอดอุปกรณ์", "3. Unequip"))
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
