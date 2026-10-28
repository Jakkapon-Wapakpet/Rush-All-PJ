#!/usr/bin/env python3
"""
Powers Module - LAST SHELTER
พลังพิเศษของผู้รอดชีวิต (เลเวล 1-5): XP และเลเวลอัป และผลของพลังแต่ละแบบ
Survivor powers (level 1-5): XP, level-ups, and each power's effect.
"""

from language import get_text
from data import POWERS, MAX_LEVEL, XP_PER_LEVEL, tr
import storage


def power_label(person: dict) -> str:
    """ชื่อพลังพร้อมเลเวล เช่น '🎯 แม่นปืน Lv.2'"""
    info = POWERS[person["power"]]
    return f"{info['icon']} {tr(info['name'])} Lv.{person['level']}"


def xp_needed(level: int) -> int:
    """XP ที่ต้องใช้เพื่อขึ้นจากเลเวลนี้ไปเลเวลถัดไป"""
    return level * XP_PER_LEVEL


def gain_xp(person: dict, amount: int) -> bool:
    """เพิ่ม XP และเลเวลอัปถ้าครบ (สูงสุด MAX_LEVEL) คืนค่า True ถ้าเลเวลอัป"""
    if person["level"] >= MAX_LEVEL:
        return False
    person["xp"] += amount
    if person["xp"] < xp_needed(person["level"]):
        return False
    person["xp"] -= xp_needed(person["level"])
    person["level"] += 1
    storage.state["log"]["level_ups"] += 1
    return True


def best_level(power: str) -> int:
    """เลเวลสูงสุดของพลังนี้ในศูนย์ (0 = ไม่มีใครมีพลังนี้)"""
    return max((p["level"] for p in storage.state["survivors"] if p["power"] == power), default=0)


def level_of(person: dict, power: str) -> int:
    """เลเวลของพลังนี้ของคนนี้ (0 ถ้าคนนี้ไม่ได้มีพลังนี้)"""
    return person["level"] if person["power"] == power else 0


def guard_bonus(person: dict) -> int:
    """🎯 แม่นปืน: เฝ้ายามได้พลังป้องกันเพิ่ม +2 ต่อเลเวล"""
    return level_of(person, "marksman") * 2


def infection_factor(person: dict) -> float:
    """🧬 ภูมิคุ้มกัน: ตัวคูณโอกาสติดเชื้อ (ลดลง 15% ต่อเลเวล)"""
    return 1 - level_of(person, "immune") * 0.15


def scout_bonus(person: dict) -> int:
    """👃 นักสำรวจ: หาเสบียงได้ของเพิ่มกี่ชิ้น"""
    return level_of(person, "scout")


def build_discount() -> int:
    """🔧 ช่างซ่อม: ส่วนลดค่าก่อสร้าง (เศษวัสดุ) จากช่างที่เลเวลสูงสุดในศูนย์"""
    return best_level("mechanic")


def medicine_interval():
    """💉 นักวิทยาศาสตร์: ผลิตยาเองทุกกี่วัน (None = ไม่มีนักวิทยาศาสตร์)"""
    level = best_level("scientist")
    return 6 - level if level else None


def level_up_text(person: dict) -> str:
    """ข้อความเลเวลอัป"""
    return get_text(f"⬆ {person['name']} เลเวลอัป! {power_label(person)}",
                    f"⬆ {person['name']} leveled up! {power_label(person)}")
