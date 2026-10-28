#!/usr/bin/env python3
"""
Storage Module - DUNGEON RUSH
เก็บสถานะของเกม (ทอง ฮีโร่ กระเป๋า ชั้นดันเจี้ยน สถิติ) และบันทึก/โหลดไฟล์ JSON
Game state plus JSON save/load.
"""

import copy
import json
import os

from language import get_text

# เก็บไฟล์เซฟไว้ในโฟลเดอร์เดียวกับโปรแกรม ไม่ว่าจะสั่งรันจากโฟลเดอร์ไหน
SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dungeon_rush_save.json")

# สถานะเริ่มต้นของเกมใหม่: มีทอง 120 และนักรบ 1 คน
NEW_GAME = {
    "gold": 120,
    "floor": 1,             # ชั้นที่จะลงต่อไป (6 = ปราบมังกรสำเร็จแล้ว)
    "next_uid": 1,          # เลขประจำไอเทมชิ้นถัดไปในกระเป๋า
    "heroes": [
        {"name": "Arthur", "class": "warrior", "level": 1, "xp": 0,
         "hp": 45, "max_hp": 45, "atk": 8, "def": 5, "weapon": None, "armor": None},
    ],
    "bag": [],              # ไอเทมในกระเป๋า: {"uid": 1, "key": "iron_sword"}
    "log": {"battles": 0, "wins": 0, "losses": 0, "gold_earned": 0, "gold_spent": 0},
}

# สถานะของเกมที่กำลังเล่นอยู่ (ทุกโมดูลอ่าน/แก้ผ่าน storage.state)
state = copy.deepcopy(NEW_GAME)


def new_game() -> None:
    """เริ่มเกมใหม่ทั้งหมด"""
    state.clear()
    state.update(copy.deepcopy(NEW_GAME))
    save_game()


def load_game() -> bool:
    """
    โหลดเกมจากไฟล์เซฟ คืนค่า True หากโหลดสำเร็จ
    หากไม่มีไฟล์ หรือไฟล์เสีย จะเริ่มเกมใหม่แทน
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


def check_gold(amount: int) -> str:
    """กฎ: ทองต้องพอจ่าย คืนข้อความผิดพลาด หรือ "" หากพอ"""
    if state["gold"] < amount:
        return get_text(f"ทองไม่พอ (ต้องใช้ {amount} มี {state['gold']})",
                        f"Not enough gold (need {amount}, have {state['gold']}).")
    return ""


def spend_gold(amount: int) -> None:
    """หักทองและจดลงสถิติ"""
    state["gold"] -= amount
    state["log"]["gold_spent"] += amount


def save_game() -> bool:
    """บันทึกสถานะเกมลงไฟล์ JSON"""
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as file:
            json.dump(state, file, ensure_ascii=False, indent=2)
        return True
    except OSError:
        return False
