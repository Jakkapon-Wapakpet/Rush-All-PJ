#!/usr/bin/env python3
"""
Language Module - GHOST REALM (มิติผี)
จัดการระบบภาษา (ไทย/อังกฤษ) และฟังก์ชันช่วยเหลือด้านหน้าจอ
Bilingual localization (Thai/English) and screen helper utilities.
"""

import os

# ภาษาปัจจุบันของระบบ ('th' หรือ 'en')
current_lang = "th"


def get_language() -> str:
    """คืนค่ารหัสภาษาปัจจุบัน ('th' หรือ 'en')"""
    return current_lang


def set_language(lang: str) -> None:
    """กำหนดภาษาของระบบ ('th' หรือ 'en')"""
    global current_lang
    if lang in ("th", "en"):
        current_lang = lang


def get_text(th: str, en: str) -> str:
    """คืนค่าข้อความตามภาษาที่เลือกไว้ในระบบ"""
    if current_lang == "th":
        return th
    return en


def clear_screen() -> None:
    """ล้างหน้าจอ Terminal รองรับทั้ง Windows และ Unix/Linux/macOS"""
    os.system("cls" if os.name == "nt" else "clear")


def pause(prompt_th: str = "\nกด Enter เพื่อกลับเมนูหลัก...",
          prompt_en: str = "\nPress Enter to return to the main menu...") -> None:
    """หยุดรอให้ผู้ใช้กด Enter ก่อนดำเนินการต่อ"""
    input(get_text(prompt_th, prompt_en))


def choose_language() -> None:
    """หน้าจอเลือกภาษาเริ่มต้นของโปรแกรม"""
    while True:
        clear_screen()
        print("=" * 40)
        print("   👻  มิติผี / GHOST REALM  👻")
        print("  Ghost Survival / เอาชีวิตรอดในมิติผี")
        print("=" * 40)
        print("1. ภาษาไทย (Thai)")
        print("2. English")

        choice = input("\nSelect Language / เลือกภาษา: ").strip()

        if choice == "1":
            set_language("th")
            return
        elif choice == "2":
            set_language("en")
            return
        else:
            print("Invalid option / กรุณาเลือก 1 หรือ 2")
            input("Press Enter / กด Enter...")

