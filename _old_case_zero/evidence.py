#!/usr/bin/env python3
"""
Evidence Module - CASE ZERO
จัดการข้อมูลหลักฐาน: เพิ่มและแสดงหลักฐาน
Evidence management: view, add, and manage forensic evidence.
"""

from language import get_text, get_language, clear_screen, pause
import storage

# รายการหลักฐานทั้งหมดในระบบ
all_evidence = []


def get_all_evidence() -> list:
    """คืนค่ารายการหลักฐานทั้งหมด"""
    return all_evidence


def set_all_evidence(evidence_list: list) -> None:
    """ตั้งค่ารายการหลักฐานทั้งหมด"""
    global all_evidence
    all_evidence = evidence_list


def find_evidence_by_case(case_id: str) -> list:
    """ค้นหาหลักฐานที่เกี่ยวข้องกับรหัสคดีที่ระบุ"""
    result = []
    for evd in all_evidence:
        if evd.get("รหัสคดี", "").strip().lower() == case_id.strip().lower():
            result.append(evd)
    return result


def remove_evidence_by_case(case_id: str) -> int:
    """ลบหลักฐานทั้งหมดของคดีที่ระบุ และคืนค่าจำนวนที่ลบไป"""
    before = len(all_evidence)
    # แก้ไขรายการเดิมแบบ in-place เพื่อให้ตัวแปรที่อ้างถึงรายการนี้เห็นผลด้วย
    all_evidence[:] = [
        evd for evd in all_evidence
        if evd.get("รหัสคดี", "").strip().lower() != case_id.strip().lower()
    ]
    return before - len(all_evidence)


def next_evidence_id() -> str:
    """สร้างรหัสหลักฐานถัดไปอัตโนมัติ เช่น EVD-009 (มากกว่าเลขที่มีอยู่เสมอ)"""
    max_id_num = len(all_evidence) + 1
    for evd in all_evidence:
        code = evd.get("รหัส", "")
        if code.startswith("EVD-") and code[4:].isdigit():
            val = int(code[4:])
            if val >= max_id_num:
                max_id_num = val + 1
    return f"EVD-{max_id_num:03d}"


def create_evidence(case: dict, name: str, desc: str) -> dict:
    """เพิ่มหลักฐานให้คดีที่มีอยู่จริง บันทึก และคืนค่าหลักฐานที่สร้าง (ใช้ร่วมกันทั้ง Terminal และ GUI)"""
    new_evidence = {
        "รหัส": next_evidence_id(),
        "รหัสคดี": case["รหัส"],
        "ชื่อ_th": name,
        "ชื่อ_en": name,
        "รายละเอียด_th": desc,
        "รายละเอียด_en": desc
    }
    all_evidence.append(new_evidence)
    storage.auto_save()
    return new_evidence


def view_all_evidence() -> None:
    """แสดงหลักฐานทั้งหมดในคลังหลักฐาน"""
    lang = get_language()
    clear_screen()
    print(get_text(
        "\n========== แฟ้มหลักฐานทั้งหมด ==========",
        "\n========== ALL FORENSIC EVIDENCE =========="
    ))

    if not all_evidence:
        print(get_text("ยังไม่มีหลักฐาน", "No evidence found."))
        return

    for evd in all_evidence:
        name_key = f"ชื่อ_{lang}" if f"ชื่อ_{lang}" in evd else "ชื่อ_th"
        desc_key = f"รายละเอียด_{lang}" if f"รายละเอียด_{lang}" in evd else "รายละเอียด_th"

        print(f"\n{get_text('รหัสหลักฐาน', 'Evidence ID')}: {evd['รหัส']}")
        print(f"{get_text('รหัสคดี', 'Case ID')}: {evd['รหัสคดี']}")
        print(f"{get_text('ชื่อหลักฐาน', 'Evidence')}: {evd.get(name_key, evd.get('ชื่อ_th', ''))}")
        print(f"{get_text('รายละเอียด', 'Description')}: {evd.get(desc_key, evd.get('รายละเอียด_th', ''))}")


def add_evidence() -> None:
    """เพิ่มหลักฐานใหม่ โดยต้องระบุรหัสคดีที่มีอยู่จริงในระบบ"""
    import cases

    lang = get_language()
    case_id = input(get_text("รหัสคดี: ", "Case ID: ")).strip()
    case = cases.find_case_by_id(case_id)

    # กฎ: ไม่สามารถเพิ่มหลักฐานให้กับคดีที่ไม่มีอยู่จริงได้
    if case is None:
        print(get_text("ไม่พบคดี", "Case not found."))
        return

    name = input(get_text("ชื่อหลักฐาน: ", "Evidence name: ")).strip()
    desc = input(get_text("รายละเอียด: ", "Description: ")).strip()

    if not name or not desc:
        print(get_text("กรุณากรอกข้อมูลให้ครบ", "Please fill in all fields."))
        return

    create_evidence(case, name, desc)
    print(get_text("เพิ่มหลักฐานสำเร็จ", "Evidence added successfully."))


def manage_evidence() -> None:
    """เมนูจัดการห้องเก็บหลักฐาน"""
    while True:
        clear_screen()
        print(get_text(
            "\n========== ห้องเก็บหลักฐาน ==========",
            "\n========== EVIDENCE ROOM =========="
        ))
        print(get_text("1. แสดงหลักฐานทั้งหมด", "1. View All Evidence"))
        print(get_text("2. เพิ่มหลักฐาน", "2. Add Evidence"))
        print(get_text("3. กลับเมนูหลัก", "3. Back to Main Menu"))

        choice = input(get_text("เลือกเมนู: ", "Choose an option: ")).strip()

        if choice == "1":
            view_all_evidence()
            pause()

        elif choice == "2":
            clear_screen()
            add_evidence()
            pause()

        elif choice == "3":
            break

        else:
            print(get_text("เมนูไม่ถูกต้อง", "Invalid option."))
            pause()

