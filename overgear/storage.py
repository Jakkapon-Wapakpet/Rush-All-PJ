#!/usr/bin/env python3
"""
Storage Module - OVERGEAR (ร้านตีอาวุธ)
เก็บสถานะของร้าน (วัน เงิน ชื่อเสียง คลัง อาวุธ ออเดอร์ ผู้กล้า) และบันทึก/โหลด JSON
Shop state plus JSON save/load and the game history file.
"""

import copy
import json
import os

from language import get_text
from data import (MATERIALS, DIFFICULTIES, BASE_STORAGE, BASE_FORGES, MAX_FAME, tr)

# เก็บไฟล์เซฟไว้ในโฟลเดอร์เดียวกับโปรแกรม ไม่ว่าจะสั่งรันจากโฟลเดอร์ไหน
FOLDER = os.path.dirname(os.path.abspath(__file__))
SAVE_FILE = os.path.join(FOLDER, "overgear_save.json")
HISTORY_FILE = os.path.join(FOLDER, "overgear_history.json")

# ปิดได้ตอนจำลองเล่น (simulate.py) จะได้ไม่ทับเซฟจริง
SAVE_ENABLED = True

# ส่วนที่ไฟล์เซฟต้องมี (ส่วนอื่นจะเติมค่าเริ่มต้นให้)
REQUIRED = ("day", "status", "difficulty", "gold", "fame", "materials", "weapons", "orders", "heroes")

# สถานะเริ่มต้นของเกมใหม่
NEW_GAME = {
    "day": 1,
    "status": "playing",                                   # playing / won / lost
    "started": False,                                      # ผู้เล่นเลือกระดับแล้ว (เซฟที่สร้างอัตโนมัติยังไม่นับ)
    "difficulty": "normal",                                # easy / normal / nightmare
    "gold": 0,
    "fame": 0,
    "materials": {key: 0 for key in MATERIALS},            # วัตถุดิบในคลัง
    "weapons": [],                                         # อาวุธบนชั้นวาง (ยังไม่ได้ส่ง)
    "orders": [],                                          # ออเดอร์ที่รับแล้ว
    "board": [],                                           # ลูกค้าที่มารอบนกระดานวันนี้
    "heroes": [],                                          # ผู้กล้าในเมือง
    "fallen": [],                                          # ชื่อผู้กล้าที่ตาย (ขณะใช้อาวุธของเรา)
    "garrison": [],                                        # อาวุธที่ส่งให้ทหารรักษาเมือง
    "champion": None,                                      # id ของผู้กล้าแชมป์ที่จะสู้มังกร
    "forge_level": 1,
    "apprentice": False,
    "molds": ["dagger", "sword", "axe"],
    "storage": BASE_STORAGE,
    "forges_left": BASE_FORGES,
    "forging": None,                                       # มินิเกมที่กำลังตีค้างอยู่ (หรือ None)
    "prices": {},                                          # ราคาวัตถุดิบวันนี้
    "last_prices": {},                                     # ราคาเมื่อวาน (ไว้แสดงขึ้น/ลง)
    "news": "calm",                                        # ข่าววันนี้
    "rumor": "calm",                                       # ข่าวลือของพรุ่งนี้
    "offers": [],                                          # ของที่ผู้กล้านำกลับมาขายวันนี้
    "next_id": 1,
    "ending": None,                                        # ผลการสู้มังกร (เมื่อจบเกม)
    "log": {"forged": 0, "grades": [0, 0, 0, 0, 0], "crits": 0, "delivered": 0, "late": 0, "cancelled": 0,
            "earned": 0, "spent": 0, "hunts": 0, "wins": 0, "deaths": 0, "legends": 0, "repairs": 0,
            "best": None, "days": []},
}

# สถานะของร้านที่กำลังเล่นอยู่ (ทุกโมดูลอ่าน/แก้ผ่าน storage.state)
state = copy.deepcopy(NEW_GAME)


def next_id() -> int:
    """แจก id ใหม่ให้อาวุธ/ออเดอร์/ผู้กล้า (ไม่ซ้ำกันตลอดเกม)"""
    number = state["next_id"]
    state["next_id"] += 1
    return number


def setting(key: str):
    """ค่าของระดับความยากที่กำลังเล่น"""
    return DIFFICULTIES[state["difficulty"]][key]


def new_game(difficulty: str = "normal", rng=None) -> None:
    """เริ่มเกมใหม่ทั้งหมดตามระดับความยาก (ตลาด ผู้กล้า และกระดานวันแรกสร้างใน day.start_morning)"""
    import day      # import ตรงนี้เพื่อไม่ให้ import วนกัน
    state.clear()
    state.update(copy.deepcopy(NEW_GAME))
    state["difficulty"] = difficulty
    state["gold"] = setting("gold")
    state["fame"] = setting("fame")
    state["materials"]["iron"] = 4
    state["materials"]["oak"] = 2
    day.start_game(rng)
    save_game()


def load_game() -> bool:
    """
    โหลดเกมจากไฟล์เซฟ คืนค่า True หากโหลดสำเร็จ
    หากไม่มีไฟล์ หรือไฟล์เสีย จะเริ่มเกมใหม่แทน
    """
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        new_game()
        return False

    # ไฟล์ต้องมีส่วนหลักครบและชนิดถูกต้อง มิฉะนั้นถือว่าเสีย
    if not valid_save(data):
        new_game()
        return False

    for key, value in NEW_GAME.items():
        data.setdefault(key, copy.deepcopy(value))
    for key in MATERIALS:
        data["materials"].setdefault(key, 0)
    state.clear()
    state.update(data)
    return True


def valid_save(data) -> bool:
    """ตรวจว่าข้อมูลที่อ่านมาเป็นเซฟที่ใช้ได้ (มีส่วนหลักครบ ชนิดถูก ระดับความยากรู้จัก)"""
    if not isinstance(data, dict) or any(key not in data for key in REQUIRED):
        return False
    if data["difficulty"] not in DIFFICULTIES or data["status"] not in ("playing", "won", "lost"):
        return False
    if not isinstance(data["day"], int) or not isinstance(data["gold"], int) or not isinstance(data["fame"], int):
        return False
    return all(isinstance(data[key], list) for key in ("weapons", "orders", "heroes")) and \
        isinstance(data["materials"], dict)


def save_game() -> bool:
    """บันทึกสถานะร้านลงไฟล์ JSON"""
    if not SAVE_ENABLED:
        return True
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as file:
            json.dump(state, file, ensure_ascii=False, indent=2)
        return True
    except OSError:
        return False


# ---------- เงิน ชื่อเสียง วัตถุดิบ ----------

def check_gold(amount: int) -> str:
    """กฎ: เงินต้องพอ คืนข้อความผิดพลาด หรือ "" หากพอ"""
    if state["gold"] < amount:
        return get_text(f"เงินไม่พอ (ต้องใช้ {amount} มี {state['gold']} ทอง)",
                        f"Not enough gold (need {amount}, have {state['gold']}).")
    return ""


def pay(amount: int) -> None:
    """จ่ายเงินและจดลงสถิติ"""
    state["gold"] -= amount
    state["log"]["spent"] += amount


def earn(amount: int) -> None:
    """รับเงินและจดลงสถิติ"""
    state["gold"] += amount
    state["log"]["earned"] += amount


def add_fame(amount: int) -> None:
    """เพิ่ม/ลดชื่อเสียง (อยู่ในช่วง 0-100 เสมอ)"""
    state["fame"] = max(0, min(MAX_FAME, state["fame"] + amount))


def stored() -> int:
    """จำนวนวัตถุดิบทั้งหมดในคลัง"""
    return sum(state["materials"].values())


def check_space(amount: int) -> str:
    """กฎ: คลังต้องมีที่ว่างพอ"""
    free = state["storage"] - stored()
    if amount > free:
        return get_text(f"คลังเต็ม (ว่าง {free} ช่อง จาก {state['storage']})",
                        f"Storage full ({free} of {state['storage']} slots free).")
    return ""


def check_materials(need: dict) -> str:
    """กฎ: วัตถุดิบต้องครบ คืนข้อความผิดพลาด หรือ "" หากครบ"""
    for key, amount in need.items():
        have = state["materials"].get(key, 0)
        if have < amount:
            return get_text(f"{tr(MATERIALS[key]['name'])}ไม่พอ (ต้องใช้ {amount} มี {have})",
                            f"Not enough {tr(MATERIALS[key]['name'])} (need {amount}, have {have}).")
    return ""


# ---------- ประวัติผลเกม (แยกไฟล์ เพื่อไม่ให้หายตอนเริ่มเกมใหม่) ----------

def load_history() -> list:
    """โหลดประวัติผลเกม คืนค่า list ว่างถ้าไม่มีไฟล์หรือไฟล์เสีย"""
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as file:
            history = json.load(file)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return []
    if not isinstance(history, list):
        return []
    return [game for game in history if isinstance(game, dict) and isinstance(game.get("stars"), int)]


def record_result(ending: dict) -> None:
    """บันทึกผลเกมที่เพิ่งจบลงไฟล์ประวัติ"""
    if not SAVE_ENABLED:
        return
    history = load_history()
    history.append({"game": len(history) + 1, "difficulty": state["difficulty"], "status": state["status"],
                    "stars": ending["stars"], "slayer": ending["slayer"], "defense": ending["defense"],
                    "dragon": ending["dragon"], "gold": state["gold"], "fame": state["fame"],
                    "best": state["log"]["best"], "deaths": state["log"]["deaths"]})
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as file:
            json.dump(history, file, ensure_ascii=False, indent=2)
    except OSError:
        pass
