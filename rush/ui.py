#!/usr/bin/env python3
"""
UI Module - GHOST REALM (มิติผี)
ตัวช่วยรับ input และแสดงหัวข้อที่ทุกเมนูใช้ร่วมกัน
Shared input helpers and headings.
"""

from language import get_text

# แบนเนอร์ตัวใหญ่ "มิติผี" ของหน้าแรก (วาดด้วยบล็อก █ ทีละช่อง)
BANNER = [
    "                                                        ██",
    "        ██████              ██████                ████████",
    "    ████████████        ████████████          ████████████",
    "",
    "  ██          ██      ████    ████        ██            ██",
    "██  ██        ██    ██    ████    ██    ██  ██          ██",
    "  ████        ██    ██            ██      ████          ██",
    "    ██        ██    ██  ████      ██        ██          ██",
    "    ██        ██    ████    ██    ██        ██          ██",
    "  ████        ██    ██  ████      ██        ██    ██    ██",
    "██  ██        ██    ██            ██        ██  ██  ██  ██",
    "  ██████████████    ████          ██        ████      ████",
]


def show_banner() -> None:
    """แสดงแบนเนอร์ตัวใหญ่ "มิติผี" """
    for line in BANNER:
        print("  " + line)


def heading(th: str, en: str) -> None:
    """แสดงหัวข้อของหน้าจอ"""
    print("\n" + "=" * 52)
    print("  " + get_text(th, en))
    print("=" * 52)


def choose_from_list(items: list, prompt_th: str, prompt_en: str):
    """
    ให้ผู้ใช้เลือกรายการด้วยหมายเลข (1, 2, 3, ...) หรือ 0 เพื่อยกเลิก
    คืนค่ารายการที่เลือก หรือ None หากยกเลิก/กรอกไม่ถูกต้อง
    """
    choice = input(get_text(prompt_th + " (0 = ยกเลิก): ", prompt_en + " (0 = cancel): ")).strip()
    try:
        number = int(choice)
    except ValueError:
        print(get_text("กรุณากรอกเป็นตัวเลข", "Please enter a number."))
        return None

    if number == 0:
        return None
    if number < 0 or number > len(items):
        print(get_text("ไม่มีหมายเลขนี้", "That number is not on the list."))
        return None
    return items[number - 1]


def ask_yes_no(prompt_th: str, prompt_en: str) -> bool:
    """ถามยืนยัน คืนค่า True เมื่อผู้ใช้ตอบ y"""
    answer = input(get_text(prompt_th + " (y/n): ", prompt_en + " (y/n): ")).strip().lower()
    return answer == "y"
