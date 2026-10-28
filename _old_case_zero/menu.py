#!/usr/bin/env python3
"""
Menu Module - CASE ZERO
แสดงเมนู รับตัวเลือก และจัดการการนำทาง
Display menu, handle user inputs, and navigate application workflows.
"""

from language import get_text, clear_screen, pause, choose_language
import cases
import evidence
import game
import storage


def display_menu() -> None:
    """แสดงรายการเมนูหลักของระบบ CASE ZERO"""
    print("=" * 44)
    print("              CASE ZERO")
    print("    ศูนย์สืบสวนคดีปริศนา / Mystery Desk")
    print("=" * 44)
    print(get_text("1. 🕵  เริ่มสืบสวนคดี", "1. 🕵  Start Investigation"))
    print(get_text("2. แฟ้มคดี (ดู/เพิ่ม/ค้นหา/แก้ไข/ลบ)", "2. Case Files (view/add/search/edit/delete)"))
    print(get_text("3. ห้องเก็บหลักฐาน", "3. Evidence Room"))
    print(get_text("4. รายงานการสืบสวน", "4. Investigation Reports"))
    print(get_text("5. เปลี่ยนภาษา", "5. Change Language"))
    print(get_text("0. ออกจากระบบ", "0. Exit"))


def run_menu() -> None:
    """ลูปการทำงานหลักของโปรแกรม รับคำสั่งและนำทางไปยังส่วนต่างๆ"""
    while True:
        clear_screen()
        display_menu()

        choice = input(get_text(
            "\nกรุณาเลือกเมนู (0-5): ",
            "\nChoose an option (0-5): "
        )).strip()

        if choice == "1":
            clear_screen()
            game.start_investigation()
            pause()

        elif choice == "2":
            cases.manage_cases()

        elif choice == "3":
            evidence.manage_evidence()

        elif choice == "4":
            cases.report_menu()

        elif choice == "5":
            choose_language()

        elif choice == "0":
            clear_screen()
            # บันทึกข้อมูล JSON ก่อนปิดโปรแกรม
            storage.auto_save()
            print(get_text(
                "ปิดระบบ CASE ZERO ขอบคุณที่ปฏิบัติหน้าที่ นักสืบ",
                "CASE ZERO shutting down. Good work, detective."
            ))
            break

        else:
            print(get_text("ไม่มีเมนูนี้", "Invalid option."))
            pause()

