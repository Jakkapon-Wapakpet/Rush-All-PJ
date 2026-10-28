#!/usr/bin/env python3
"""
Storage Module - GHOST REALM (หลุดมิติผี)
เก็บสถานะของศาลา (วัน ทรัพยากร ผู้รอดชีวิต สิ่งก่อสร้าง สถิติ) และบันทึก/โหลด JSON
Shelter state plus JSON save/load.
"""

import copy
import json
import os

from language import get_text
from data import RESOURCES, STARTING_SURVIVORS, DIFFICULTIES, MAX_HP, CHARACTER_NAME_UPDATES, tr

# เก็บไฟล์เซฟไว้ในโฟลเดอร์เดียวกับโปรแกรม ไม่ว่าจะสั่งรันจากโฟลเดอร์ไหน
SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "last_shelter_save.json")

# ส่วนที่ไฟล์เซฟต้องมี (ส่วนอื่นที่เพิ่มทีหลังจะเติมค่าเริ่มต้นให้ เซฟเก่าจึงยังโหลดได้)
REQUIRED = ("day", "status", "resources", "survivors", "buildings", "wanderer", "log")

# สถานะเริ่มต้นของเกมใหม่
NEW_GAME = {
    "day": 1,
    "status": "playing",                                           # playing / won / lost
    "difficulty": "normal",                                        # easy / normal / nightmare
    "resources": {"food": 7, "water": 7, "scrap": 6, "medicine": 2},
    "survivors": [],                                               # เติมจาก STARTING_SURVIVORS ตอนเริ่มเกม
    "buildings": [],                                               # สิ่งก่อสร้างที่สร้างแล้ว
    "wanderer": None,                                              # คนที่มาขอเข้าศาลาวันนี้ (หรือ None)
    # ระบบเสริม (ระดับปกติขึ้นไป)
    "omen": None,                                                  # ลางของวันนี้ {"shown", "actual", "whisper"}
    "prepared": [],                                                # ของแก้ผีที่เตรียมไว้คืนนี้
    "light": "normal",                                             # ไฟคืนนี้: dark / normal / fire
    "vow": None,                                                   # บนบานที่ยังไม่แก้ {"wish", "due"}
    "calm": False,                                                 # บนขอให้คืนนี้ผีไม่บุกไว้
    "grudge": 0,                                                   # ความแค้นของมิติผี 0-10
    "tickets": 0,                                                  # ชิ้นส่วนตั๋วที่เก็บได้
    "fallen": [],                                                  # ชื่อเพื่อนที่ตาย/กลายเป็นผี/ถูกไล่ออก (อาจกลับมาเป็นผี)
    "visits": {},                                                  # สถานที่ -> จำนวนครั้งที่ไปแล้ว (ของลดลง)
    "merit_day": 0,                                                # วันที่ทำบุญล่าสุด (ทำได้วันละครั้ง)
    "escaped": False,                                              # กลับบ้านก่อนด้วยตั๋วครบ
    "log": {"gathered": {"food": 0, "water": 0, "scrap": 0, "medicine": 0},
            "raids": 0, "repelled": 0, "deaths": 0, "joined": 0,
            "infected": 0, "cured": 0, "turned": 0, "biggest_horde": 0, "days": []},
}

# สถานะของศาลาที่กำลังเล่นอยู่ (ทุกโมดูลอ่าน/แก้ผ่าน storage.state)
state = copy.deepcopy(NEW_GAME)


def new_survivor(name: str, skills: dict, look: str) -> dict:
    """
    สร้างข้อมูลผู้รอดชีวิต 1 คน (HP เต็ม ยังไม่มีงาน)
    infected = จำนวนวันที่ถูกผีสิงมาแล้ว (0 = ปกติ), look = รูปร่างสำหรับภาพใน GUI
    """
    return {"name": name, "hp": MAX_HP, "skills": dict(skills), "job": None, "infected": 0, "look": look}


def new_game(difficulty: str = "normal") -> None:
    """เริ่มเกมใหม่ทั้งหมดตามระดับความยาก (ของตั้งต้นต่างกันตามระดับ)"""
    state.clear()
    state.update(copy.deepcopy(NEW_GAME))
    state["difficulty"] = difficulty
    state["resources"] = dict(DIFFICULTIES[difficulty]["resources"])
    state["survivors"] = [new_survivor(s["name"], s["skills"], s["look"]) for s in STARTING_SURVIVORS]
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

    # ไฟล์ต้องมีส่วนหลักครบ มิฉะนั้นถือว่าเสีย
    if not isinstance(data, dict) or any(key not in data for key in REQUIRED):
        new_game()
        return False

    # เซฟเก่าก่อนมีระดับความยากเล่นด้วยกฎพื้นฐาน (ง่าย) และเติมส่วนที่ยังไม่มีด้วยค่าเริ่มต้น
    data.setdefault("difficulty", "easy")
    for key, value in NEW_GAME.items():
        data.setdefault(key, copy.deepcopy(value))
    for person in data["survivors"] + ([data["wanderer"]] if data["wanderer"] else []):
        person["name"] = CHARACTER_NAME_UPDATES.get(person["name"], person["name"])
    data["fallen"] = [CHARACTER_NAME_UPDATES.get(name, name) for name in data["fallen"]]
    if data.get("omen") and data["omen"].get("whisper"):
        name = data["omen"]["whisper"]
        data["omen"]["whisper"] = CHARACTER_NAME_UPDATES.get(name, name)
    state.clear()
    state.update(data)
    return True


def save_game() -> bool:
    """บันทึกสถานะศาลาลงไฟล์ JSON"""
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


def record_result(stars: int, rescued: int, early: bool = False) -> None:
    """บันทึกผลเกมที่เพิ่งจบลงไฟล์ประวัติ (early = กลับบ้านก่อนด้วยตั๋วครบ)"""
    history = load_history()
    history.append({"game": len(history) + 1, "status": state["status"], "day": state["day"],
                    "stars": stars, "rescued": rescued, "deaths": state["log"]["deaths"],
                    "joined": state["log"]["joined"], "difficulty": state["difficulty"], "early": early})
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as file:
            json.dump(history, file, ensure_ascii=False, indent=2)
    except OSError:
        pass
