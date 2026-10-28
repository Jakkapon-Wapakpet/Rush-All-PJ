#!/usr/bin/env python3
"""
Storage Module - WITCH'S BREW
เก็บสถานะของร้าน (ทอง ชื่อเสียง คลังสมุนไพร ชั้นวางยา ตำรา ลูกค้า สถิติ) และบันทึก/โหลด JSON
Shop state plus JSON save/load.
"""

import copy
import json
import os

from language import get_text

# เก็บไฟล์เซฟไว้ในโฟลเดอร์เดียวกับโปรแกรม ไม่ว่าจะสั่งรันจากโฟลเดอร์ไหน
SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "witch_brew_save.json")

# สถานะเริ่มต้นของร้านใหม่
NEW_GAME = {
    "day": 1,
    "gold": 100,
    "reputation": 50,                                     # ชื่อเสียง 0-100
    "herbs": {"mint": 2, "honey": 2, "ginger": 1},        # คลังสมุนไพร: ชื่อ -> จำนวน
    "shelf": {"cough_syrup": 1},                          # ยาบนชั้น: สูตร -> จำนวนขวด
    "prices": {},                                         # ราคาขายที่ตั้งเอง: สูตร -> ราคา
    "known": ["cough_syrup", "fever_tea", "dream_drop"],  # สูตรที่รู้แล้ว
    "market": {},                                         # ราคาสมุนไพรวันนี้
    "customers": [],                                      # ลูกค้าที่รออยู่หน้าร้านวันนี้
    "log": {"income": 0, "spent": 0, "served": 0, "turned_away": 0, "explosions": 0,
            "brewed": 0, "sold": {}, "daily": []},
    "today": {"income": 0, "spent": 0},
}

# สถานะของร้านที่กำลังเล่นอยู่ (ทุกโมดูลอ่าน/แก้ผ่าน storage.state)
state = copy.deepcopy(NEW_GAME)


def new_game() -> None:
    """เริ่มร้านใหม่ทั้งหมด"""
    # import ตรงนี้เพื่อเลี่ยงการ import วนกัน (shop ใช้ storage)
    import shop

    state.clear()
    state.update(copy.deepcopy(NEW_GAME))
    shop.start_day()
    save_game()


def load_game() -> bool:
    """
    โหลดร้านจากไฟล์เซฟ คืนค่า True หากโหลดสำเร็จ
    หากไม่มีไฟล์ หรือไฟล์เสีย จะเริ่มร้านใหม่แทน
    """
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        new_game()
        return False

    # ไฟล์ต้องมีข้อมูลครบทุกส่วน มิฉะนั้นถือว่าเสีย
    if not isinstance(data, dict) or any(key not in data for key in NEW_GAME):
        new_game()
        return False

    state.clear()
    state.update(data)
    return True


def save_game() -> bool:
    """บันทึกสถานะร้านลงไฟล์ JSON"""
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as file:
            json.dump(state, file, ensure_ascii=False, indent=2)
        return True
    except OSError:
        return False


def check_gold(amount: int) -> str:
    """กฎ: ทองต้องพอจ่าย คืนข้อความผิดพลาด หรือ "" หากพอ"""
    if state["gold"] < amount:
        return get_text(f"ทองไม่พอ (ต้องใช้ {amount} มี {state['gold']})",
                        f"Not enough gold (need {amount}, have {state['gold']}).")
    return ""


def spend_gold(amount: int) -> None:
    """หักทองและจดลงสถิติ"""
    state["gold"] -= amount
    state["log"]["spent"] += amount
    state["today"]["spent"] += amount


def earn_gold(amount: int) -> None:
    """รับทองและจดลงสถิติ"""
    state["gold"] += amount
    state["log"]["income"] += amount
    state["today"]["income"] += amount
