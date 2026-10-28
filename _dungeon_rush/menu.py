#!/usr/bin/env python3
"""
Menu Module - DUNGEON RUSH
เมนูหลักของเมือง และการนำทางไปยังส่วนต่างๆ
Town main menu and navigation.
"""

from language import get_text, clear_screen, pause, choose_language
from data import MONSTERS, MAX_PARTY, BAG_SIZE
from ui import ask_yes_no
import dungeon
import heroes
import items
import storage


def display_menu() -> None:
    """แสดงเมนูหลักพร้อมแถบสถานะ"""
    state = storage.state
    floor = min(state["floor"], len(MONSTERS))
    print("=" * 52)
    print("            ⚔  D U N G E O N   R U S H  ⚔")
    print("=" * 52)
    print(get_text(
        f" ทอง {state['gold']}  |  ชั้น {floor}/{len(MONSTERS)}  |  ทีม {len(state['heroes'])}/{MAX_PARTY}"
        f"  |  กระเป๋า {len(state['bag'])}/{BAG_SIZE}",
        f" Gold {state['gold']}  |  Floor {floor}/{len(MONSTERS)}  |  Party {len(state['heroes'])}/{MAX_PARTY}"
        f"  |  Bag {len(state['bag'])}/{BAG_SIZE}"
    ))
    print("-" * 52)
    print(get_text("1. ทีมฮีโร่", "1. Party"))
    print(get_text("2. ร้านค้า", "2. Shop"))
    print(get_text("3. กระเป๋า / สวมใส่", "3. Bag / Equipment"))
    print(get_text("4. ลงดันเจี้ยน", "4. Enter the Dungeon"))
    print(get_text("5. โรงเตี๊ยม (พักฟื้น HP)", "5. Inn (restore HP)"))
    print(get_text("6. บันทึกการผจญภัย", "6. Adventure Log"))
    print(get_text("7. เปลี่ยนภาษา", "7. Change Language"))
    print(get_text("8. เริ่มเกมใหม่", "8. New Game"))
    print(get_text("0. ออกจากเกม", "0. Quit"))


def start_new_game() -> None:
    """เริ่มเกมใหม่ (ถามยืนยันก่อน เพราะเซฟเดิมจะหายไป)"""
    if ask_yes_no("เริ่มเกมใหม่? ความคืบหน้าเดิมจะหายทั้งหมด", "Start over? All progress will be lost."):
        storage.new_game()
        print(get_text("เริ่มเกมใหม่แล้ว", "New game started."))
    else:
        print(get_text("ยกเลิก", "Cancelled."))


def run_menu() -> None:
    """ลูปเมนูหลัก วนรับคำสั่งจนกว่าผู้เล่นจะเลือกออก"""
    # เมนูที่แสดงผลแล้วรอกด Enter
    actions = {
        "4": dungeon.enter_dungeon,
        "5": heroes.rest_at_inn,
        "6": dungeon.adventure_log,
        "8": start_new_game,
    }

    while True:
        clear_screen()
        display_menu()
        choice = input(get_text("\nเลือกเมนู (0-8): ", "\nChoose (0-8): ")).strip()

        if choice == "1":
            heroes.party_menu()
        elif choice == "2":
            items.shop_menu()
        elif choice == "3":
            items.bag_menu()
        elif choice in actions:
            clear_screen()
            actions[choice]()
            pause()
        elif choice == "7":
            choose_language()
        elif choice == "0":
            storage.save_game()
            print(get_text("บันทึกเกมแล้ว แล้วพบกันใหม่ นักผจญภัย!", "Game saved. Farewell, adventurer!"))
            break
        else:
            print(get_text("ไม่มีเมนูนี้", "Invalid option."))
            pause()
