#!/usr/bin/env python3
"""
Menu Module - WITCH'S BREW
เมนูหลักของร้าน และการนำทางไปยังส่วนต่างๆ
Main menu and navigation.
"""

from language import get_text, clear_screen, pause, choose_language
from data import SHELF_SIZE
from ui import ask_yes_no
import brewing
import market
import shop
import storage


def display_menu() -> None:
    """แสดงเมนูหลักพร้อมแถบสถานะของร้าน"""
    state = storage.state
    known, total = brewing.book_progress()
    print("=" * 56)
    print("              🧪  W I T C H ' S   B R E W  🧪")
    print("=" * 56)
    print(get_text(
        f" วันที่ {state['day']}  |  ทอง {state['gold']}  |  ชื่อเสียง {shop.reputation_stars()}  |  ตำรา {known}/{total}",
        f" Day {state['day']}  |  Gold {state['gold']}  |  Reputation {shop.reputation_stars()}  |  Book {known}/{total}"
    ))
    print("-" * 56)
    print(get_text("1. ตลาดสมุนไพร", "1. Herb Market"))
    print(get_text("2. หม้อปรุงยา", "2. Cauldron"))
    print(get_text(f"3. ชั้นวางยา ({brewing.shelf_count()}/{SHELF_SIZE})", f"3. Potion Shelf ({brewing.shelf_count()}/{SHELF_SIZE})"))
    print(get_text(f"4. หน้าร้าน (ลูกค้ารอ {len(state['customers'])} คน)", f"4. Shop Front ({len(state['customers'])} waiting)"))
    print(get_text("5. ตำรายา", "5. Recipe Book"))
    print(get_text("6. บัญชีร้าน", "6. Accounts"))
    print(get_text("7. ปิดร้าน → วันถัดไป", "7. Close Shop → Next Day"))
    print(get_text("8. เปลี่ยนภาษา", "8. Change Language"))
    print(get_text("9. เริ่มร้านใหม่", "9. New Game"))
    print(get_text("0. ออก", "0. Quit"))


def start_new_game() -> None:
    """เริ่มร้านใหม่ (ถามยืนยันก่อน เพราะเซฟเดิมจะหายไป)"""
    if ask_yes_no("เริ่มร้านใหม่? ความคืบหน้าเดิมจะหายทั้งหมด", "Start over? All progress will be lost."):
        storage.new_game()
        print(get_text("เปิดร้านใหม่แล้ว!", "A brand new shop!"))
    else:
        print(get_text("ยกเลิก", "Cancelled."))


def run_menu() -> None:
    """ลูปเมนูหลัก วนรับคำสั่งจนกว่าผู้ใช้จะเลือกออก"""
    # เมนูที่มีเมนูย่อยของตัวเอง
    submenus = {"1": market.market_menu, "2": brewing.cauldron_menu, "3": shop.shelf_menu, "4": shop.front_counter}
    # เมนูที่แสดงผลแล้วรอกด Enter
    actions = {"5": brewing.view_book, "6": shop.accounts, "7": shop.end_day, "9": start_new_game}

    while True:
        clear_screen()
        display_menu()
        choice = input(get_text("\nเลือกเมนู (0-9): ", "\nChoose (0-9): ")).strip()

        if choice in submenus:
            submenus[choice]()
        elif choice in actions:
            clear_screen()
            actions[choice]()
            pause()
        elif choice == "8":
            choose_language()
        elif choice == "0":
            storage.save_game()
            print(get_text("บันทึกแล้ว แล้วพบกันใหม่ แม่มดน้อย 🧹", "Saved. See you soon, little witch 🧹"))
            break
        else:
            print(get_text("ไม่มีเมนูนี้", "Invalid option."))
            pause()
