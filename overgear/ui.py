#!/usr/bin/env python3
"""
UI Module - OVERGEAR (ร้านตีอาวุธ)
ตัวช่วยรับ input และแสดงหัวข้อที่ทุกเมนูใช้ร่วมกัน
Shared input helpers and headings.
"""

from language import get_text


def heading(th: str, en: str) -> None:
    """แสดงหัวข้อของหน้าจอ"""
    print("\n" + "=" * 60)
    print("  " + get_text(th, en))
    print("=" * 60)


def bar(value: float, high: float, width: int = 10) -> str:
    """แถบความยาว width ช่อง เติมตามสัดส่วน value/high"""
    if high <= 0:
        return "░" * width
    filled = max(0, min(width, round(width * value / high)))
    return "█" * filled + "░" * (width - filled)


def choose_from_list(items: list, prompt_th: str, prompt_en: str):
    """
    ให้ผู้ใช้เลือกรายการด้วยหมายเลข (1, 2, 3, ...) หรือ 0 เพื่อยกเลิก
    คืนค่ารายการที่เลือก หรือ None หากยกเลิก/กรอกไม่ถูกต้อง
    """
    if not items:
        print(get_text("ไม่มีรายการให้เลือก", "Nothing to choose from."))
        return None
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


def ask_int(prompt_th: str, prompt_en: str, low: int, high: int):
    """
    ให้ผู้ใช้พิมพ์จำนวนเต็มในช่วง low..high
    คืนค่าตัวเลข หรือ None หากพิมพ์ไม่ใช่ตัวเลขหรืออยู่นอกช่วง
    """
    text = input(get_text(f"{prompt_th} ({low}-{high}): ", f"{prompt_en} ({low}-{high}): ")).strip()
    try:
        number = int(text)
    except ValueError:
        print(get_text("กรุณากรอกเป็นตัวเลข", "Please enter a number."))
        return None
    if number < low or number > high:
        print(get_text(f"ต้องอยู่ระหว่าง {low} ถึง {high}", f"Must be between {low} and {high}."))
        return None
    return number


def show_error(message: str) -> bool:
    """แสดงข้อความผิดพลาดจากฟังก์ชัน do_* คืนค่า True ถ้ามีข้อผิดพลาด"""
    if message:
        print("✖ " + message)
        return True
    return False
