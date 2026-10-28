#!/usr/bin/env python3
"""
Survivors Module - LAST SHELTER
ผู้รอดชีวิต: ดูสถานะ มอบหมายงาน แนะนำงานอัตโนมัติ ตรวจและรับคนเข้าศูนย์ เปลี่ยนชื่อ และไล่ออก
Survivors: status, job assignment, auto-assign, recruiting, renaming, and exiling.
"""

from language import get_text
from data import JOBS, SKILLS, POWERS, MAX_CAMP, MAX_HP, MAX_LEVEL, MIN_SCAVENGE_HP, RAID_START_DAY, TURN_DAYS, tr
from ui import heading, choose_from_list, ask_yes_no
import camp
import powers
import storage

MAX_NAME_LENGTH = 12


def stars(level: int) -> str:
    """ระดับทักษะแบบดาว เช่น ★★★☆☆"""
    return "★" * level + "☆" * (5 - level)


def hp_bar(hp: int, width: int = 10) -> str:
    """แถบ HP เช่น ███████░░░"""
    filled = round(width * hp / MAX_HP)
    return "█" * filled + "░" * (width - filled)


def job_label(job) -> str:
    """ชื่องานพร้อมไอคอน หรือ 'ยังไม่มีงาน'"""
    if job is None:
        return get_text("— ยังไม่มีงาน", "— no job")
    return f"{JOBS[job]['icon']} {tr(JOBS[job]['name'])}"


def infection_text(person: dict) -> str:
    """สถานะติดเชื้อ เช่น '🦠 ติดเชื้อ! กลายร่างในอีก 1 วัน' หรือ '' ถ้าปกติ"""
    if not person["infected"]:
        return ""
    left = TURN_DAYS - person["infected"] + 1
    return get_text(f"🦠 ติดเชื้อ! กลายร่างในอีก {left} วัน", f"🦠 INFECTED! Turns in {left} day(s)")


def print_survivor(number: int, person: dict) -> None:
    """แสดงข้อมูลผู้รอดชีวิต 1 คน"""
    skills = "  ".join(f"{tr(SKILLS[s])} {stars(level)}" for s, level in person["skills"].items())
    xp = "MAX" if person["level"] >= MAX_LEVEL else f"XP {person['xp']}/{powers.xp_needed(person['level'])}"
    print(f"\n{number}. {person['name']:<10} HP {hp_bar(person['hp'])} {person['hp']:>3}/{MAX_HP}   {job_label(person['job'])}")
    print(f"   ⚡ {powers.power_label(person)} ({xp}) — {tr(POWERS[person['power']]['about'])}")
    print(f"   {skills}   {infection_text(person)}")


def view_survivors() -> None:
    """แสดงผู้รอดชีวิตทุกคน"""
    heading(f"ผู้รอดชีวิต {len(storage.state['survivors'])}/{MAX_CAMP} คน",
            f"SURVIVORS {len(storage.state['survivors'])}/{MAX_CAMP}")
    for number, person in enumerate(storage.state["survivors"], start=1):
        print_survivor(number, person)


# ---------- กฎและการเปลี่ยนข้อมูล (ใช้ร่วมกันทั้ง Terminal และ GUI) ----------

def validate_name(name: str, person: dict = None) -> str:
    """ตรวจชื่อ คืนข้อความผิดพลาด หรือ "" หากใช้ได้ (person = คนที่กำลังเปลี่ยนชื่อ ไม่นับว่าซ้ำกับตัวเอง)"""
    if not name:
        return get_text("ชื่อห้ามว่าง", "Name cannot be empty.")
    if len(name) > MAX_NAME_LENGTH:
        return get_text(f"ชื่อยาวได้ไม่เกิน {MAX_NAME_LENGTH} ตัวอักษร", f"Name must be at most {MAX_NAME_LENGTH} characters.")
    for other in storage.state["survivors"]:
        if other is not person and other["name"].lower() == name.lower():
            return get_text("มีคนชื่อนี้ในศูนย์แล้ว", "Someone in the shelter already has this name.")
    return ""


def healers_assigned(exclude: dict = None) -> int:
    """จำนวนคนที่ได้รับงานรักษาแล้ว (ไม่นับ exclude)"""
    return sum(1 for p in storage.state["survivors"] if p["job"] == "heal" and p is not exclude)


def assignable_jobs() -> list:
    """งานที่มอบหมายเองได้ (ไม่รวมงานซ่อน เช่น ตรวจคนแปลกหน้า)"""
    return [job for job, info in JOBS.items() if not info["hidden"]]


def check_job(person: dict, job: str) -> str:
    """ตรวจว่าคนนี้รับงานนี้ได้ไหม คืนข้อความผิดพลาด หรือ "" หากได้"""
    # กฎ: HP ต่ำห้ามออกไปหาของหรือเฝ้ายาม
    if job in ("scavenge", "guard") and person["hp"] < MIN_SCAVENGE_HP:
        return get_text(f"{person['name']} บาดเจ็บหนัก (HP {person['hp']}) ต้องมี HP อย่างน้อย {MIN_SCAVENGE_HP}",
                        f"{person['name']} is badly hurt (HP {person['hp']}). Needs at least {MIN_SCAVENGE_HP} HP.")
    # กฎ: ยาต้องพอสำหรับคนที่ได้งานรักษาทุกคน (คนละ 1 ชิ้น)
    if job == "heal" and storage.state["resources"]["medicine"] < healers_assigned(person) + 1:
        return get_text("ยาไม่พอสำหรับงานรักษา (ใช้ยาคนละ 1 ชิ้น)", "Not enough medicine (each healer needs 1).")
    return ""


def do_assign(person: dict, job: str) -> str:
    """มอบหมายงาน (คนละ 1 งานต่อวัน เปลี่ยนได้จนกว่าจะจบวัน) คืนข้อความผิดพลาด หรือ "" หากสำเร็จ"""
    error = check_job(person, job)
    if error:
        return error
    person["job"] = job
    storage.save_game()
    return ""


def job_score(person: dict, job: str) -> float:
    """
    คะแนนความเหมาะสมของงานกับคนนี้ในสถานการณ์ตอนนี้
    = (ระดับทักษะ + โบนัสพลังพิเศษที่ตรงกับงาน) x ความจำเป็นของงานนั้น (อาหาร/น้ำใกล้หมด, ซอมบี้บุก, มีคนเจ็บ/ติดเชื้อ)
    """
    state = storage.state
    if job == "rest":
        return (MAX_HP - person["hp"]) / 25
    skill = person["skills"][JOBS[job]["skill"]]
    if POWERS[person["power"]]["job"] == job:
        skill += person["level"] * 0.5
    if job == "scavenge":
        need = 2.0 if min(camp.days_left("food"), camp.days_left("water")) <= 2 else 1.0
    elif job == "guard":
        need = 1.3 if state["day"] >= RAID_START_DAY else 0.2
    else:
        # มีคนติดเชื้อ = ต้องรักษาด่วนที่สุด
        if any(p["infected"] for p in state["survivors"]):
            need = 3.0
        else:
            need = 1.5 if any(p["hp"] < 60 for p in state["survivors"]) else 0.0
    return skill * need


def recommend_job(person: dict) -> str:
    """งานที่เหมาะที่สุดสำหรับคนนี้ (เฉพาะงานที่ทำได้ตามกฎ)"""
    allowed = [job for job in assignable_jobs() if not check_job(person, job)]
    return max(allowed, key=lambda job: job_score(person, job))


def do_auto_assign() -> list:
    """จัดงานให้ทุกคนอัตโนมัติตามคำแนะนำ (ไม่แตะคนที่กำลังตรวจคนแปลกหน้า) คืนค่า [(คน, งาน), ...]"""
    people = [p for p in storage.state["survivors"] if p["job"] != "inspect"]
    for person in people:
        person["job"] = None
    plan = []
    # คนที่ทักษะสูงสุดได้เลือกก่อน (เรียงจากผลรวมทักษะมากไปน้อย)
    for person in sorted(people, key=lambda p: -sum(p["skills"].values())):
        job = recommend_job(person)
        person["job"] = job
        plan.append((person, job))
    storage.save_game()
    return plan


def do_accept_wanderer() -> str:
    """รับคนที่มาขอเข้าศูนย์ (ถ้าติดเชื้อมา จะติดเชื้อตั้งแต่วันแรก) คืนข้อความผิดพลาด หรือ "" หากสำเร็จ"""
    state = storage.state
    if state["wanderer"] is None:
        return get_text("ไม่มีใครรออยู่ที่ประตู", "No one is at the gate.")
    # กฎ: ศูนย์รับคนได้ไม่เกิน MAX_CAMP
    if len(state["survivors"]) >= MAX_CAMP:
        return get_text(f"ศูนย์พักพิงเต็มแล้ว (สูงสุด {MAX_CAMP} คน)", f"The shelter is full (max {MAX_CAMP}).")
    wanderer = state["wanderer"]
    person = storage.new_survivor(wanderer["name"], wanderer["skills"], wanderer["power"], wanderer["level"])
    person["hp"] = wanderer["hp"]
    if wanderer["infected"]:
        # ติดเชื้อมาหลายวันแล้ว: จะกลายร่างคืนนี้ ถ้าไม่ได้ยาวันนี้
        person["infected"] = TURN_DAYS
        state["log"]["infected"] += 1
    state["survivors"].append(person)
    state["wanderer"] = None
    state["log"]["joined"] += 1
    storage.save_game()
    return ""


def do_inspect(person: dict) -> str:
    """
    ให้คนในศูนย์ไปตรวจร่างกายคนแปลกหน้า (ใช้งานของคนนั้นทั้งวัน)
    คืนข้อความผิดพลาด หรือ "" หากตรวจสำเร็จ (ผลตรวจอยู่ใน state["wanderer"]["checked"])
    """
    wanderer = storage.state["wanderer"]
    if wanderer is None:
        return get_text("ไม่มีใครรออยู่ที่ประตู", "No one is at the gate.")
    if wanderer["checked"]:
        return get_text("ตรวจไปแล้ว", "Already inspected.")
    # กฎ: คนที่ไปตรวจต้องยังไม่มีงานวันนี้ (1 คน 1 งาน)
    if person["job"] is not None:
        return get_text(f"{person['name']} มีงานแล้ววันนี้", f"{person['name']} already has a job today.")
    person["job"] = "inspect"
    wanderer["checked"] = True
    storage.save_game()
    return ""


def do_reject_wanderer() -> None:
    """ปฏิเสธคนที่มาขอเข้าศูนย์"""
    storage.state["wanderer"] = None
    storage.save_game()


def do_rename(person: dict, name: str) -> str:
    """เปลี่ยนชื่อ คืนข้อความผิดพลาด หรือ "" หากสำเร็จ"""
    error = validate_name(name, person)
    if error:
        return error
    person["name"] = name
    storage.save_game()
    return ""


def do_exile(person: dict) -> str:
    """ไล่ออกจากศูนย์ คืนข้อความผิดพลาด หรือ "" หากสำเร็จ"""
    # กฎ: ศูนย์ต้องเหลืออย่างน้อย 1 คน
    if len(storage.state["survivors"]) <= 1:
        return get_text("ไล่ออกไม่ได้ ศูนย์ต้องเหลืออย่างน้อย 1 คน", "You can't exile the last survivor.")
    storage.state["survivors"].remove(person)
    storage.save_game()
    return ""


# ---------- เมนู Terminal ----------

def choose_survivor(people: list = None):
    """แสดงรายชื่อแล้วให้เลือก 1 คน (people = ให้เลือกเฉพาะกลุ่มนี้)"""
    people = storage.state["survivors"] if people is None else people
    for number, person in enumerate(people, start=1):
        print(f"{number}. {person['name']:<10} HP {person['hp']:>3}   {job_label(person['job'])}   {infection_text(person)}")
    return choose_from_list(people, "เลือกคน", "Choose a survivor")


def assign_job() -> None:
    """มอบหมายงานให้ 1 คน"""
    heading("มอบหมายงาน", "ASSIGN A JOB")
    person = choose_survivor()
    if person is None:
        return

    if person["job"] == "inspect":
        print(get_text(f"{person['name']} กำลังตรวจคนแปลกหน้า เปลี่ยนงานไม่ได้วันนี้",
                       f"{person['name']} is inspecting the newcomer today."))
        return
    jobs = assignable_jobs()
    best = recommend_job(person)
    print()
    for number, job in enumerate(jobs, start=1):
        skill = JOBS[job]["skill"]
        level = f"{tr(SKILLS[skill])} {stars(person['skills'][skill])}" if skill else ""
        tip = get_text("  ← แนะนำ", "  ← suggested") if job == best else ""
        print(f"{number}. {job_label(job):<18} {level:<18} {tr(JOBS[job]['about'])}{tip}")

    job = choose_from_list(jobs, "เลือกงาน", "Choose a job")
    if job is None:
        return
    error = do_assign(person, job)
    print(error or get_text(f"{person['name']}: {job_label(job)}", f"{person['name']}: {job_label(job)}"))


def auto_assign() -> None:
    """จัดงานให้ทุกคนอัตโนมัติ"""
    heading("จัดงานอัตโนมัติ", "AUTO-ASSIGN")
    for person, job in do_auto_assign():
        print(f"• {person['name']:<10} → {job_label(job)}")
    print(get_text("\n(ดูจากทักษะ + สถานการณ์: อาหาร/น้ำใกล้หมด, ซอมบี้บุก, มีคนเจ็บ/ติดเชื้อ)",
                   "\n(based on skills + situation: low food/water, raids, injuries/infection)"))


def rename_survivor() -> None:
    """เปลี่ยนชื่อ"""
    heading("เปลี่ยนชื่อ", "RENAME")
    person = choose_survivor()
    if person is None:
        return
    old_name = person["name"]
    name = input(get_text("ชื่อใหม่: ", "New name: ")).strip()
    error = do_rename(person, name)
    print(error or get_text(f"{old_name} เปลี่ยนชื่อเป็น {name}", f"{old_name} is now {name}."))


def exile_survivor() -> None:
    """ไล่ออกจากศูนย์ (เช่น คนที่ติดเชื้อและไม่มียารักษา)"""
    heading("ไล่ออกจากศูนย์", "EXILE")
    person = choose_survivor()
    if person is None:
        return
    if not ask_yes_no(f"ไล่ {person['name']} ออกจากศูนย์?", f"Exile {person['name']}?"):
        print(get_text("ยกเลิก", "Cancelled."))
        return
    error = do_exile(person)
    print(error or get_text(f"{person['name']} เดินจากไปในเมืองร้าง...", f"{person['name']} walks off into the dead city..."))


def gate() -> None:
    """ประตูศูนย์: ตรวจร่างกาย แล้วตัดสินใจรับหรือไม่รับคนที่มาขอเข้า"""
    heading("ประตูศูนย์พักพิง", "SHELTER GATE")
    wanderer = storage.state["wanderer"]
    if wanderer is None:
        print(get_text("ไม่มีใครอยู่ที่ประตูวันนี้", "No one is at the gate today."))
        return

    skills = "  ".join(f"{tr(SKILLS[s])} {stars(level)}" for s, level in wanderer["skills"].items())
    print(get_text(f"🚶 {wanderer['name']} ขอเข้าศูนย์ (HP {wanderer['hp']})", f"🚶 {wanderer['name']} asks to come in (HP {wanderer['hp']})"))
    print(f"   ⚡ {POWERS[wanderer['power']]['icon']} {tr(POWERS[wanderer['power']]['name'])} Lv.{wanderer['level']}"
          f" — {tr(POWERS[wanderer['power']]['about'])}")
    print(f"   {skills}")
    if wanderer["checked"]:
        print(get_text("   🔍 ผลตรวจ: " + ("🦠 พบรอยกัด! ติดเชื้อ" if wanderer["infected"] else "✔ ไม่พบรอยกัด"),
                       "   🔍 Result: " + ("🦠 Bite found! Infected" if wanderer["infected"] else "✔ No bites")))
    else:
        print(get_text("   🔍 ยังไม่ได้ตรวจร่างกาย (อาจติดเชื้อมาแล้ว!)", "   🔍 Not inspected yet (could be infected!)"))
    print(get_text(f"\nรับเข้ามาแล้วต้องเลี้ยงเพิ่ม: อาหาร +1, น้ำ +1 ต่อวัน   (ศูนย์ {len(storage.state['survivors'])}/{MAX_CAMP})",
                   f"\nOne more mouth: +1 food, +1 water per day   (shelter {len(storage.state['survivors'])}/{MAX_CAMP})"))

    print(get_text("\n1. รับเข้าศูนย์   2. ไม่รับ   3. ตรวจร่างกายก่อน (ใช้คนว่าง 1 คนทั้งวัน)   0. ยังไม่ตัดสินใจ",
                   "\n1. Let them in   2. Turn away   3. Inspect first (uses one free survivor for the day)   0. Decide later"))
    choice = input(get_text("เลือก: ", "Choose: ")).strip()
    if choice == "1":
        name, infected = wanderer["name"], wanderer["infected"]
        error = do_accept_wanderer()
        if error:
            print(error)
        elif infected:
            print(get_text(f"😱 {name} เข้ามาแล้ว... แต่มีรอยกัดเก่าที่แขน! จะกลายร่างคืนนี้ถ้าไม่ได้ยาวันนี้!",
                           f"😱 {name} is in... but there's an old bite on their arm! They'll turn tonight without medicine today!"))
        else:
            print(get_text(f"{name} เข้าร่วมศูนย์พักพิงแล้ว!", f"{name} joined the shelter!"))
    elif choice == "2":
        do_reject_wanderer()
        print(get_text("คุณปิดประตู... เขาเดินจากไป", "You close the gate... they walk away."))
    elif choice == "3":
        free = [p for p in storage.state["survivors"] if p["job"] is None]
        if not free:
            print(get_text("ไม่มีใครว่างวันนี้ ทุกคนมีงานแล้ว", "No one is free today."))
            return
        print()
        person = choose_survivor(free)
        if person is None:
            return
        error = do_inspect(person)
        if error:
            print(error)
            return
        result = get_text("🦠 พบรอยกัด! ติดเชื้อ", "🦠 Bite found! Infected") if wanderer["infected"] \
            else get_text("✔ ไม่พบรอยกัด ปลอดภัย", "✔ No bites. Safe")
        print(get_text(f"🔍 {person['name']} ตรวจร่างกาย {wanderer['name']}: {result}",
                       f"🔍 {person['name']} inspects {wanderer['name']}: {result}"))
        print(get_text("(กลับมาที่ประตูเพื่อตัดสินใจรับหรือไม่รับ)", "(Come back to the gate to decide)"))
    elif choice != "0":
        print(get_text("ไม่มีตัวเลือกนี้", "Invalid option."))
