#!/usr/bin/env python3
"""
UI Module - LAST SHELTER
ตัวช่วยรับ input และแสดงหัวข้อที่ทุกเมนูใช้ร่วมกัน
Shared input helpers and headings.
"""

from language import get_text


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


def choose_many(items: list, prompt_th: str, prompt_en: str, most: int):
    """
    ให้ผู้ใช้เลือกหลายรายการพร้อมกัน เช่น "1,3" (ไม่เกิน most รายการ และห้ามซ้ำ)
    คืนค่า list ของรายการที่เลือก หรือ None หากยกเลิก/กรอกไม่ถูกต้อง
    """
    text = input(get_text(f"{prompt_th} เช่น 1,3 (0 = ยกเลิก): ",
                          f"{prompt_en} e.g. 1,3 (0 = cancel): ")).strip()
    if text == "0":
        return None
    try:
        numbers = [int(part) for part in text.replace(" ", "").split(",") if part]
    except ValueError:
        print(get_text("กรุณากรอกเป็นตัวเลขคั่นด้วยจุลภาค", "Please enter numbers separated by commas."))
        return None

    if not numbers:
        print(get_text("ยังไม่ได้เลือกอะไร", "Nothing selected."))
        return None
    if len(numbers) > most:
        print(get_text(f"เลือกได้ไม่เกิน {most} รายการ", f"Choose at most {most}."))
        return None
    if len(set(numbers)) != len(numbers):
        print(get_text("ห้ามเลือกซ้ำ", "No duplicates allowed."))
        return None
    if any(number < 1 or number > len(items) for number in numbers):
        print(get_text("มีหมายเลขที่ไม่อยู่ในรายการ", "A number is not on the list."))
        return None
    return [items[number - 1] for number in numbers]
