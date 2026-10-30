#!/usr/bin/env python3
"""
UI Module - GHOST REALM (มิติผี)
ตัวช่วยรับ input และแสดงหัวข้อที่ทุกเมนูใช้ร่วมกัน
Shared input helpers and headings.
"""

import os
import sys

from language import get_text

# ---------- สี (ANSI) ----------
# ปิดสีเองเมื่อไม่ได้แสดงบน Terminal หรือตั้ง NO_COLOR ไว้
USE_COLOR = sys.stdout.isatty() and "NO_COLOR" not in os.environ
if USE_COLOR and os.name == "nt":
    os.system("")  # เปิดโหมดสี ANSI ใน Windows console

RESET = "\033[0m"
PURPLE = "\033[38;5;135m"
CYAN = "\033[38;5;159m"
YELLOW = "\033[38;5;229m"
WHITE = "\033[97m"
GREY = "\033[38;5;244m"
RED = "\033[38;5;160m"
GREEN = "\033[38;5;71m"

# ไล่สีแบนเนอร์จากม่วงด้านบนไปแดงเลือดด้านล่าง
BANNER_GRADIENT = [93, 99, 135, 135, 171, 170, 169, 168, 167, 161, 160, 124]


def paint(text: str, color: str) -> str:
    """ระบายสีข้อความ (คืนข้อความเดิมถ้าปิดสีอยู่)"""
    if not USE_COLOR or not text:
        return text
    return color + text + RESET

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


# ภาพประกอบตอนสำคัญ: ตกกลางคืน / ประตูมิติเปิด (ชนะ) / หลุมศพ (แพ้)
NIGHT_ART = [
    r"        _..._                     .-.",
    r"      .'     '.    *     .       ( o o)    .",
    r"     /    .-'''      .        *   | O \        *",
    r"    |    /         *      .        \   \ ",
    r"    |    |    .                     `~~~'   .",
    r"     \    '-...       *       .          *",
    r"      '.     .'   .      ,/\,  ,/\,  ,/\,",
    r"        `'''`        ___/____\/____\/____\___",
]

PORTAL_ART = [
    r"             .  *  .   .-~~~~~~-.   .  *  .",
    r"          *        .-~  .-~~-.   ~-.       *",
    r"            .    /   .'  @@  '.    \   .",
    r"               |   /   @@@@@@  \    |",
    r"          *    |   |  @@ () @@  |   |    *",
    r"               |   \   @@@@@@  /    |",
    r"            .    \   '.  @@  .'    /   .",
    r"          *        '-._ '--' _.-'        *",
    r"             .  *  .   '~~~~~~'   .  *  .",
]

# โซนสีของแต่ละภาพ: (แถวเริ่ม, แถวจบ, คอลัมน์เริ่ม, คอลัมน์จบ, สี) โซนแรกที่ตรงจะถูกใช้
NIGHT_ZONES = [(0, 6, 0, 18, YELLOW), (0, 5, 32, 42, CYAN), (6, 8, 18, 50, RED)]
PORTAL_ZONES = [(2, 7, 19, 32, PURPLE), (1, 8, 15, 36, CYAN)]

GRAVE_ART = [
    r"                    _______",
    r"                  .'       '.",
    r"                 /   R.I.P   \ ",
    r"                 |           |",
    r"                 |   ~ ~ ~   |",
    r"                 |           |",
    r"             ,,,,|,,,,,,,,,,,|,,,,",
    r"            ^^^^^^^^^^^^^^^^^^^^^^^^",
]
GRAVE_ZONES = [(0, 6, 0, 40, WHITE), (6, 7, 0, 40, GREEN), (7, 8, 0, 40, GREY)]


def show_banner() -> None:
    """แสดงแบนเนอร์ตัวใหญ่ "มิติผี" ไล่สีทีละบรรทัด"""
    for line, shade in zip(BANNER, BANNER_GRADIENT):
        print("  " + paint(line, f"\033[38;5;{shade}m"))


def zone_color(zones: list, row: int, col: int, default: str) -> str:
    """หาสีของตัวอักษรที่ตำแหน่ง (แถว, คอลัมน์) จากโซนสีของภาพ"""
    for top, bottom, left, right, color in zones:
        if top <= row < bottom and left <= col < right:
            return color
    return default


def show_art(art: list, zones: list = (), default: str = GREY, pixels: list = None) -> None:
    """แสดงภาพ pixel art ถ้าเปิดสีอยู่ ไม่งั้นแสดง ASCII art ระบายสีตามโซน (ดาว * เป็นสีขาวเสมอ)"""
    print()
    if pixels and USE_COLOR:
        for line in pixels:
            print("  " + line)
        return
    for row, line in enumerate(art):
        out, run, run_color = "", "", None
        for col, char in enumerate(line):
            color = WHITE if char == "*" else zone_color(zones, row, col, default)
            if color != run_color:
                out += paint(run, run_color)
                run, run_color = "", color
            run += char
        print(out + paint(run, run_color))


def heading(th: str, en: str) -> None:
    """แสดงหัวข้อของหน้าจอ"""
    print("\n" + paint("=" * 52, PURPLE))
    print("  " + paint(get_text(th, en), YELLOW))
    print(paint("=" * 52, PURPLE))


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
