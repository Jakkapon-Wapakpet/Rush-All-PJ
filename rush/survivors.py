#!/usr/bin/env python3
"""
Survivors Module - GHOST REALM (มิติผี)
ผู้รอดชีวิต: ดูสถานะ มอบหมายงาน แนะนำงานอัตโนมัติ ตรวจและรับคนเข้าศาลา เปลี่ยนชื่อ และไล่ออก
Survivors: status, job assignment, auto-assign, recruiting, renaming, and exiling.
"""

from language import get_text
from data import JOBS, SKILLS, LOOKS, LOCATIONS, MAX_PEOPLE, MAX_HP, MIN_SCAVENGE_HP, RAID_START_DAY, TURN_DAYS, tr
from ui import heading, choose_from_list, ask_yes_no
import sala
import realm
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


def job_text(person: dict) -> str:
    """งานของคนนี้ ถ้าออกไปหาของในระดับปกติขึ้นไปจะบอกสถานที่ด้วย"""
    if person["job"] == "scavenge" and person.get("target") and realm.advanced():
        return f"{job_label('scavenge')}: {realm.location_label(person['target'])}"
    return job_label(person["job"])


def possession_text(person: dict) -> str:
    """สถานะถูกผีสิง เช่น '😈 ถูกผีสิง! กลายเป็นผีในอีก 1 วัน' หรือ '' ถ้าปกติ"""
    if not person["possessed"]:
        return ""
    left = TURN_DAYS - person["possessed"] + 1
    return get_text(f"😈 ถูกผีสิง! กลายเป็นผีในอีก {left} วัน", f"😈 POSSESSED! Becomes a ghost in {left} day(s)")


def look_of(person: dict) -> str:
    """รูปร่างของคนนี้สำหรับภาพใน GUI (เซฟเก่าที่ยังไม่มี look จะเลือกจากชื่อ)"""
    return person.get("look") or LOOKS[sum(map(ord, person["name"])) % len(LOOKS)]


def print_survivor(number: int, person: dict) -> None:
    """แสดงข้อมูลผู้รอดชีวิต 1 คน"""
    skills = "  ".join(f"{tr(SKILLS[s])} {stars(level)}" for s, level in person["skills"].items())
    print(f"\n{number}. {person['name']:<10} HP {hp_bar(person['hp'])} {person['hp']:>3}/{MAX_HP}   {job_text(person)}")
    print(f"   {skills}   {possession_text(person)}")


def view_survivors() -> None:
    """แสดงผู้รอดชีวิตทุกคน"""
    heading(f"ผู้รอดชีวิต {len(storage.state['survivors'])}/{MAX_PEOPLE} คน",
            f"SURVIVORS {len(storage.state['survivors'])}/{MAX_PEOPLE}")
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
            return get_text("มีคนชื่อนี้ในศาลาแล้ว", "Someone in the sala already has this name.")
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
    # กฎ: น้ำมนต์ต้องพอสำหรับคนที่ได้งานประพรมน้ำมนต์ทุกคน (คนละ 1)
    if job == "heal" and storage.state["resources"]["holy_water"] < healers_assigned(person) + 1:
        return get_text("น้ำมนต์ไม่พอ (ใช้น้ำมนต์คนละ 1)", "Not enough holy water (each blesser needs 1).")
    return ""


def do_assign(person: dict, job: str, target: str = None) -> str:
    """
    มอบหมายงาน (คนละ 1 งานต่อวัน เปลี่ยนได้จนกว่าจะจบวัน) คืนข้อความผิดพลาด หรือ "" หากสำเร็จ
    target = สถานที่ออกไปหาของ (ระดับปกติขึ้นไป ถ้าไม่ระบุจะเลือกที่แนะนำให้)
    """
    error = check_job(person, job)
    if error:
        return error
    person["job"] = job
    person["target"] = (target or realm.recommend_location()) if job == "scavenge" and realm.advanced() else None
    storage.save_game()
    return ""


def job_score(person: dict, job: str) -> float:
    """
    คะแนนความเหมาะสมของงานกับคนนี้ในสถานการณ์ตอนนี้
    = ระดับทักษะ x ความจำเป็นของงานนั้น (อาหาร/น้ำใกล้หมด, ผีบุก, มีคนเจ็บ/ถูกผีสิง)
    """
    state = storage.state
    if job == "rest":
        return (MAX_HP - person["hp"]) / 25
    skill = person["skills"][JOBS[job]["skill"]]
    if job == "scavenge":
        need = 2.0 if min(sala.days_left("food"), sala.days_left("water")) <= 2 else 1.0
    elif job == "guard":
        need = 1.3 if state["day"] >= RAID_START_DAY else 0.2
    else:
        # มีคนถูกผีสิง = ต้องประพรมน้ำมนต์ด่วนที่สุด
        if any(p["possessed"] for p in state["survivors"]):
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
        person["target"] = realm.recommend_location() if job == "scavenge" and realm.advanced() else None
        plan.append((person, job))
    storage.save_game()
    return plan


def do_accept_stranger() -> str:
    """รับคนที่มาขอเข้าศาลา (ถ้าถูกผีสิงมา จะถูกผีสิงตั้งแต่วันแรก) คืนข้อความผิดพลาด หรือ "" หากสำเร็จ"""
    state = storage.state
    if state["stranger"] is None:
        return get_text("ไม่มีใครรออยู่ที่ประตู", "No one is at the gate.")
    # กฎ: ศาลารับคนได้ไม่เกิน MAX_PEOPLE
    if len(state["survivors"]) >= MAX_PEOPLE:
        return get_text(f"ศาลาเต็มแล้ว (สูงสุด {MAX_PEOPLE} คน)", f"The sala is full (max {MAX_PEOPLE}).")
    stranger = state["stranger"]
    person = storage.new_survivor(stranger["name"], stranger["skills"], stranger["look"])
    person["hp"] = stranger["hp"]
    if stranger.get("disguised"):
        person["disguised"] = 2            # ผีปลอมตัว: จะเผยร่างหลังผ่านไป 2 คืน
    if stranger.get("ticket"):
        realm.add_ticket([])
    if stranger["possessed"]:
        # ถูกผีสิงมาหลายวันแล้ว: จะกลายเป็นผีคืนนี้ ถ้าไม่ได้น้ำมนต์วันนี้
        person["possessed"] = TURN_DAYS
        state["log"]["possessed"] += 1
    state["survivors"].append(person)
    state["stranger"] = None
    state["log"]["joined"] += 1
    storage.save_game()
    return ""


def do_inspect(person: dict) -> str:
    """
    ให้คนในศาลาไปส่องดูเงาคนแปลกหน้า (ใช้งานของคนนั้นทั้งวัน)
    คืนข้อความผิดพลาด หรือ "" หากตรวจสำเร็จ (ผลตรวจอยู่ใน state["stranger"]["checked"])
    """
    stranger = storage.state["stranger"]
    if stranger is None:
        return get_text("ไม่มีใครรออยู่ที่ประตู", "No one is at the gate.")
    if stranger["checked"]:
        return get_text("ตรวจไปแล้ว", "Already inspected.")
    # กฎ: คนที่ไปตรวจต้องยังไม่มีงานวันนี้ (1 คน 1 งาน)
    if person["job"] is not None:
        return get_text(f"{person['name']} มีงานแล้ววันนี้", f"{person['name']} already has a job today.")
    person["job"] = "inspect"
    stranger["checked"] = True
    storage.save_game()
    return ""


def do_reject_stranger() -> None:
    """ปฏิเสธคนที่มาขอเข้าศาลา"""
    storage.state["stranger"] = None
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
    """ไล่ออกจากศาลา คืนข้อความผิดพลาด หรือ "" หากสำเร็จ"""
    # กฎ: ศาลาต้องเหลืออย่างน้อย 1 คน
    if len(storage.state["survivors"]) <= 1:
        return get_text("ไล่ออกไม่ได้ ศาลาต้องเหลืออย่างน้อย 1 คน", "You can't exile the last survivor.")
    storage.state["survivors"].remove(person)
    # ระดับปกติขึ้นไป: คนที่ถูกไล่ออกไปตายในความมืด ผีแค้นเพิ่ม และเขาอาจกลับมาเป็นผี
    if realm.advanced():
        realm.add_grudge(2)
        realm.add_fallen(person["name"])
    storage.save_game()
    return ""


# ---------- เมนู Terminal ----------

def choose_survivor(people: list = None):
    """แสดงรายชื่อแล้วให้เลือก 1 คน (people = ให้เลือกเฉพาะกลุ่มนี้)"""
    people = storage.state["survivors"] if people is None else people
    for number, person in enumerate(people, start=1):
        print(f"{number}. {person['name']:<10} HP {person['hp']:>3}   {job_text(person)}   {possession_text(person)}")
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
    target = None
    if job == "scavenge" and realm.advanced():
        target = choose_location()
        if target is None:
            return
    error = do_assign(person, job, target)
    print(error or f"{person['name']}: {job_text(person)}")


def choose_location():
    """เลือกสถานที่ออกไปหาของ (ระดับปกติขึ้นไป)"""
    keys = list(LOCATIONS)
    best = realm.recommend_location()
    print()
    for number, key in enumerate(keys, start=1):
        left = f"{realm.location_factor(key):.0%}"
        tip = get_text("  ← แนะนำ", "  ← suggested") if key == best else ""
        print(get_text(f"{number}. {realm.location_label(key):<16} {tr(LOCATIONS[key]['about'])} (ของเหลือ {left}){tip}",
                       f"{number}. {realm.location_label(key):<16} {tr(LOCATIONS[key]['about'])} ({left} left){tip}"))
    return choose_from_list(keys, "เลือกสถานที่", "Choose a place")


def auto_assign() -> None:
    """จัดงานให้ทุกคนอัตโนมัติ"""
    heading("จัดงานอัตโนมัติ", "AUTO-ASSIGN")
    for person, job in do_auto_assign():
        print(f"• {person['name']:<10} → {job_text(person)}")
    print(get_text("\n(ดูจากทักษะ + สถานการณ์: อาหาร/น้ำใกล้หมด, ผีบุก, มีคนเจ็บ/ถูกผีสิง)",
                   "\n(based on skills + situation: low food/water, raids, injuries/possession)"))


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
    """ไล่ออกจากศาลา (เช่น คนที่ถูกผีสิงและไม่มีน้ำมนต์)"""
    heading("ไล่ออกจากศาลา", "EXILE")
    person = choose_survivor()
    if person is None:
        return
    if not ask_yes_no(f"ไล่ {person['name']} ออกจากศาลา?", f"Exile {person['name']}?"):
        print(get_text("ยกเลิก", "Cancelled."))
        return
    error = do_exile(person)
    print(error or get_text(f"{person['name']} เดินหายไปในความมืดของมิติผี...", f"{person['name']} vanishes into the dark of the ghost realm..."))


def gate() -> None:
    """ประตูศาลา: ส่องดูเงา แล้วตัดสินใจรับหรือไม่รับคนที่มาขอเข้า"""
    heading("ประตูศาลา", "SALA GATE")
    stranger = storage.state["stranger"]
    if stranger is None:
        print(get_text("ไม่มีใครอยู่ที่ประตูวันนี้", "No one is at the gate today."))
        return

    skills = "  ".join(f"{tr(SKILLS[s])} {stars(level)}" for s, level in stranger["skills"].items())
    print(get_text(f"🚶 {stranger['name']} ขอเข้าศาลา (HP {stranger['hp']})", f"🚶 {stranger['name']} asks to come in (HP {stranger['hp']})"))
    print(f"   {skills}")
    for line in realm.story_lines(stranger):
        print(f"   {line}")
    if stranger["checked"]:
        print(get_text("   🔍 ผลตรวจ: " + ("😈 เงาไม่ขยับตามตัว! ถูกผีสิง" if stranger["possessed"] else "✔ เงาปกติ"),
                       "   🔍 Result: " + ("😈 Their shadow doesn't move! Possessed" if stranger["possessed"] else "✔ Normal shadow")))
    else:
        print(get_text("   🔍 ยังไม่ได้ส่องดูเงา (อาจถูกผีสิงมาแล้ว!)", "   🔍 Not inspected yet (could be possessed!)"))
    print(get_text(f"\nรับเข้ามาแล้วต้องเลี้ยงเพิ่ม: อาหาร +1, น้ำ +1 ต่อวัน   (ศาลา {len(storage.state['survivors'])}/{MAX_PEOPLE})",
                   f"\nOne more mouth: +1 food, +1 water per day   (sala {len(storage.state['survivors'])}/{MAX_PEOPLE})"))

    print(get_text("\n1. รับเข้าศาลา   2. ไม่รับ   3. ส่องดูเงาก่อน (ใช้คนว่าง 1 คนทั้งวัน)   0. ยังไม่ตัดสินใจ",
                   "\n1. Let them in   2. Turn away   3. Check their shadow first (uses one free survivor for the day)   0. Decide later"))
    choice = input(get_text("เลือก: ", "Choose: ")).strip()
    if choice == "1":
        name, possessed = stranger["name"], stranger["possessed"]
        error = do_accept_stranger()
        if error:
            print(error)
        elif possessed:
            print(get_text(f"😱 {name} เข้ามาแล้ว... แต่เงาไม่ขยับตามตัว! ถูกผีสิงมา จะกลายเป็นผีคืนนี้ถ้าไม่ได้น้ำมนต์วันนี้!",
                           f"😱 {name} is in... but their shadow doesn't move! Possessed: holy water today or they become a ghost tonight!"))
        else:
            print(get_text(f"{name} เข้ามาอยู่ในศาลาแล้ว!", f"{name} joined the sala!"))
        if not error and stranger.get("ticket"):
            print(get_text(f"🎫 {name} ยื่นชิ้นส่วนตั๋วบ้านผีสิงให้! ({storage.state['tickets']}/3)",
                           f"🎫 {name} hands you a piece of the ticket! ({storage.state['tickets']}/3)"))
    elif choice == "2":
        do_reject_stranger()
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
        result = get_text("😈 เงาไม่ขยับตามตัว! ถูกผีสิง", "😈 Their shadow doesn't move! Possessed") if stranger["possessed"] \
            else get_text("✔ เงาปกติ ปลอดภัย", "✔ Normal shadow. Safe")
        print(get_text(f"🔍 {person['name']} ส่องดูเงาของ {stranger['name']}: {result}",
                       f"🔍 {person['name']} inspects {stranger['name']}: {result}"))
        print(get_text("(กลับมาที่ประตูเพื่อตัดสินใจรับหรือไม่รับ)", "(Come back to the gate to decide)"))
    elif choice != "0":
        print(get_text("ไม่มีตัวเลือกนี้", "Invalid option."))
