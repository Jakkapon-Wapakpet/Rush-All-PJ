#!/usr/bin/env python3
"""
Camp Module - LAST SHELTER
ทรัพยากรและสิ่งก่อสร้าง: ดูของในศูนย์พักพิง คาดการณ์ว่าอาหาร/น้ำจะหมดในกี่วัน และสร้างสิ่งก่อสร้าง
Resources and buildings: stock, run-out forecast, and construction.
"""

from language import get_text
from data import RESOURCES, BUILDINGS, tr
from ui import heading, choose_from_list
import powers
import storage

# ผลผลิตต่อวันของสิ่งก่อสร้าง (ห้องปฐมพยาบาลให้ยา 1 ทุก 2 วัน คิดเฉลี่ยเป็น 0.5)
DAILY_OUTPUT = {"garden": ("food", 1), "collector": ("water", 1), "clinic": ("medicine", 0.5)}


def resource_label(key: str) -> str:
    """ชื่อทรัพยากรพร้อมไอคอน"""
    return f"{RESOURCES[key]['icon']} {tr(RESOURCES[key]['name'])}"


def daily_use(key: str) -> int:
    """ใช้ต่อวัน: ทุกคนกินอาหาร 1 และดื่มน้ำ 1"""
    return len(storage.state["survivors"]) if key in ("food", "water") else 0


def daily_output(key: str) -> float:
    """ผลิตได้ต่อวันจากสิ่งก่อสร้าง"""
    total = 0
    for building in storage.state["buildings"]:
        resource, amount = DAILY_OUTPUT.get(building, (None, 0))
        if resource == key:
            total += amount
    return total


def days_left(key: str) -> int:
    """
    คาดการณ์ว่าทรัพยากรนี้จะพอใช้อีกกี่วัน (ไม่นับของที่จะหามาได้)
    คืนค่า 99 ถ้าผลิตได้มากกว่าที่ใช้ (ไม่มีวันหมด)
    """
    net = daily_use(key) - daily_output(key)
    if net <= 0:
        return 99
    return int(storage.state["resources"][key] // net)


def days_text(key: str) -> str:
    """ข้อความคาดการณ์ เช่น 'พอ 3 วัน' หรือ 'ไม่มีวันหมด'"""
    days = days_left(key)
    if days >= 99:
        return get_text("ไม่มีวันหมด", "never runs out")
    warn = "⚠ " if days <= 1 else ""
    return get_text(f"{warn}พอ {days} วัน", f"{warn}{days} day(s) left")


def build_cost(key: str) -> dict:
    """ค่าก่อสร้างจริง: เศษวัสดุลดลงตามเลเวลของช่างซ่อมที่เก่งที่สุด (อย่างน้อย 1)"""
    cost = dict(BUILDINGS[key]["cost"])
    cost["scrap"] = max(1, cost["scrap"] - powers.build_discount())
    return cost


def do_build(key: str) -> str:
    """สร้างสิ่งก่อสร้าง (ใช้ร่วมกันทั้ง Terminal และ GUI) คืนข้อความผิดพลาด หรือ "" หากสำเร็จ"""
    # กฎ: สิ่งก่อสร้างแต่ละอย่างสร้างได้ครั้งเดียว
    if key in storage.state["buildings"]:
        return get_text(f"สร้าง{tr(BUILDINGS[key]['name'])}ไปแล้ว", f"{tr(BUILDINGS[key]['name'])} is already built.")
    # กฎ: ทรัพยากรต้องพอ
    cost = build_cost(key)
    error = storage.check_resources(cost)
    if error:
        return error
    storage.spend(cost)
    storage.state["buildings"].append(key)
    storage.save_game()
    return ""


def cost_text(cost: dict) -> str:
    """ค่าก่อสร้าง เช่น '🔩 เศษวัสดุ 9 + 💧 น้ำ 3'"""
    return " + ".join(f"{resource_label(k)} {v}" for k, v in cost.items())


def view_status() -> None:
    """สถานะศูนย์พักพิง: ทรัพยากร การใช้/ผลิตต่อวัน และคาดการณ์"""
    heading(f"สถานะศูนย์พักพิง  วันที่ {storage.state['day']}", f"SHELTER STATUS  DAY {storage.state['day']}")
    print(get_text(f"{'ทรัพยากร':<14}{'มี':>6}{'ใช้/วัน':>9}{'ผลิต/วัน':>10}   คาดการณ์",
                   f"{'Resource':<14}{'Have':>6}{'Use/day':>9}{'Make/day':>10}   Forecast"))
    for key in RESOURCES:
        print(f"{resource_label(key):<13}{storage.state['resources'][key]:>6}{daily_use(key):>9}"
              f"{daily_output(key):>10g}   {days_text(key) if key in ('food', 'water') else ''}")

    built = storage.state["buildings"]
    print(get_text("\nสิ่งก่อสร้าง: ", "\nBuildings: ")
          + (", ".join(f"{BUILDINGS[b]['icon']} {tr(BUILDINGS[b]['name'])}" for b in built) if built
             else get_text("ยังไม่มี", "none yet")))


def build() -> None:
    """เลือกสิ่งก่อสร้างที่จะสร้าง"""
    heading("สร้างสิ่งก่อสร้าง", "BUILD")
    keys = list(BUILDINGS)
    for number, key in enumerate(keys, start=1):
        info = BUILDINGS[key]
        done = get_text("  ✔ สร้างแล้ว", "  ✔ built") if key in storage.state["buildings"] else ""
        print(f"{number}. {info['icon']} {tr(info['name']):<16} {cost_text(build_cost(key)):<26} {tr(info['about'])}{done}")
    if powers.build_discount():
        print(get_text(f"\n🔧 ช่างซ่อม Lv.{powers.build_discount()} ช่วยลดค่าเศษวัสดุ -{powers.build_discount()}",
                       f"\n🔧 Mechanic Lv.{powers.build_discount()} saves -{powers.build_discount()} scrap"))
    print(get_text(f"\nมีเศษวัสดุ {storage.state['resources']['scrap']}  น้ำ {storage.state['resources']['water']}",
                   f"\nScrap {storage.state['resources']['scrap']}  Water {storage.state['resources']['water']}"))

    key = choose_from_list(keys, "เลือกสิ่งก่อสร้าง", "Choose a building")
    if key is None:
        return
    error = do_build(key)
    print(error or get_text(f"🔨 สร้าง{tr(BUILDINGS[key]['name'])}เสร็จแล้ว! ({tr(BUILDINGS[key]['about'])})",
                            f"🔨 {tr(BUILDINGS[key]['name'])} built! ({tr(BUILDINGS[key]['about'])})"))
