#!/usr/bin/env python3
"""
Storage Module - LAST SHELTER
เก็บสถานะของศูนย์พักพิง (วัน ทรัพยากร ผู้รอดชีวิต สิ่งก่อสร้าง สถิติ) และบันทึก/โหลด JSON
Shelter state plus JSON save/load.
"""

import copy
import json
import os

from language import get_text
from data import RESOURCES, STARTING_SURVIVORS, MAX_HP, tr

# เก็บไฟล์เซฟไว้ในโฟลเดอร์เดียวกับโปรแกรม ไม่ว่าจะสั่งรันจากโฟลเดอร์ไหน
SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "last_shelter_save.json")

# สถานะเริ่มต้นของเกมใหม่
NEW_GAME = {
    "day": 1,
    "status": "playing",                                           # playing / won / lost
    "resources": {"food": 6, "water": 6, "scrap": 5, "medicine": 1},
    "survivors": [],                                               # เติมจาก STARTING_SURVIVORS ตอนเริ่มเกม
    "buildings": [],                                               # สิ่งก่อสร้างที่สร้างแล้ว
    "wanderer": None,                                              # คนที่มาขอเข้าศูนย์วันนี้ (หรือ None)
    "log": {"gathered": {"food": 0, "water": 0, "scrap": 0, "medicine": 0},
            "raids": 0, "repelled": 0, "deaths": 0, "joined": 0,
            "infected": 0, "cured": 0, "turned": 0, "level_ups": 0, "biggest_horde": 0, "days": []},
}

# สถานะของศูนย์พักพิงที่กำลังเล่นอยู่ (ทุกโมดูลอ่าน/แก้ผ่าน storage.state)
state = copy.deepcopy(NEW_GAME)


def new_survivor(name: str, skills: dict, power: str, level: int = 1) -> dict:
    """
    สร้างข้อมูลผู้รอดชีวิต 1 คน (HP เต็ม ยังไม่มีงาน)
    infected = จำนวนวันที่ติดเชื้อมาแล้ว (0 = ปกติ)
    power / level / xp = พลังพิเศษ เลเวล และ XP สะสม
    """
    return {"name": name, "hp": MAX_HP, "skills": dict(skills), "job": None, "infected": 0,
            "power": power, "level": level, "xp": 0}


def new_game() -> None:
    """เริ่มเกมใหม่ทั้งหมด"""
    state.clear()
    state.update(copy.deepcopy(NEW_GAME))
    state["survivors"] = [new_survivor(s["name"], s["skills"], s["power"], s["level"]) for s in STARTING_SURVIVORS]
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


def save_game() -> bool:
    """บันทึกสถานะศูนย์พักพิงลงไฟล์ JSON"""
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as file:
            json.dump(state, file, ensure_ascii=False, indent=2)
        return True
    except OSError:
        return False


def check_resources(cost: dict) -> str:
    """กฎ: ทรัพยากรต้องพอ คืนข้อความผิดพลาด หรือ "" หากพอ"""
    for key, amount in cost.items():
        have = state["resources"][key]
        if have < amount:
            return get_text(f"{tr(RESOURCES[key]['name'])}ไม่พอ (ต้องใช้ {amount} มี {have})",
                            f"Not enough {tr(RESOURCES[key]['name'])} (need {amount}, have {have}).")
    return ""


def spend(cost: dict) -> None:
    """หักทรัพยากรตาม cost"""
    for key, amount in cost.items():
        state["resources"][key] -= amount


def gain(key: str, amount: int) -> None:
    """เพิ่มทรัพยากรและจดลงสถิติ"""
    state["resources"][key] += amount
    state["log"]["gathered"][key] += amount


# ---------- ประวัติผลเกม (แยกไฟล์ เพื่อไม่ให้หายตอนเริ่มเกมใหม่) ----------

HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "last_shelter_history.json")


def load_history() -> list:
    """โหลดประวัติผลเกม คืนค่า list ว่างถ้าไม่มีไฟล์หรือไฟล์เสีย"""
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as file:
            history = json.load(file)
    except (OSError, json.JSONDecodeError):
        return []
    return history if isinstance(history, list) else []


def record_result(stars: int, rescued: int) -> None:
    """บันทึกผลเกมที่เพิ่งจบลงไฟล์ประวัติ"""
    history = load_history()
    history.append({"game": len(history) + 1, "status": state["status"], "day": state["day"],
                    "stars": stars, "rescued": rescued, "deaths": state["log"]["deaths"],
                    "joined": state["log"]["joined"]})
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as file:
            json.dump(history, file, ensure_ascii=False, indent=2)
    except OSError:
        pass
