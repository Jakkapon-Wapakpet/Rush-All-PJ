#!/usr/bin/env python3
"""
Cases Module - CASE ZERO
จัดการข้อมูลคดี: เพิ่ม แสดง และค้นหาคดี
Case management: add, view, detail, update, and search cases.
"""

from language import get_text, get_language, clear_screen, pause
import storage

# รายการคดีทั้งหมดในระบบ
all_cases = []


def get_all_cases() -> list:
    """คืนค่ารายการคดีทั้งหมด"""
    return all_cases


def set_all_cases(cases_list: list) -> None:
    """ตั้งค่ารายการคดีทั้งหมด"""
    global all_cases
    all_cases = cases_list


def find_case_by_id(case_id: str):
    """
    ค้นหาคดีจากรหัสคดี (Case-insensitive)
    คืนค่า dict ของคดี หรือ None หากไม่พบ
    """
    for case in all_cases:
        if case["รหัส"].strip().lower() == case_id.strip().lower():
            return case
    return None


# ระดับความยากที่ผู้ใช้พิมพ์ได้ -> ค่าที่เก็บในระบบ
DIFFICULTY_INPUT = {
    "ง่าย": "easy",
    "ปานกลาง": "medium",
    "ยาก": "hard",
    "easy": "easy",
    "medium": "medium",
    "hard": "hard"
}


def parse_difficulty(text: str):
    """แปลงข้อความระดับความยากเป็น 'easy'/'medium'/'hard' หรือ None หากไม่ถูกต้อง"""
    return DIFFICULTY_INPUT.get(text.strip().lower())


def difficulty_text(level: str) -> str:
    """คืนชื่อระดับความยากตามภาษาปัจจุบัน"""
    difficulty_map = {
        "easy": get_text("ง่าย", "Easy"),
        "medium": get_text("ปานกลาง", "Medium"),
        "hard": get_text("ยาก", "Hard")
    }
    return difficulty_map.get(level, level)


def status_text(status: str) -> str:
    """คืนชื่อสถานะคดีตามภาษาปัจจุบัน"""
    if status == "open":
        return get_text("กำลังสืบสวน", "Under Investigation")
    if status == "cold":
        return get_text("คดีค้าง (ชี้ตัวผิดเกินกำหนด)", "Cold Case (too many wrong accusations)")
    return get_text("ปิดคดีแล้ว", "Closed")


# ---------- ฟังก์ชันกลาง: กฎและการเปลี่ยนข้อมูล (ใช้ร่วมกันทั้ง Terminal และ GUI) ----------

def validate_case_id(case_id: str) -> str:
    """ตรวจรหัสคดีใหม่ คืนข้อความผิดพลาด หรือ "" หากใช้ได้"""
    # กฎ: รหัสคดีต้องไม่ว่างเปล่า
    if not case_id:
        return get_text("รหัสคดีห้ามว่าง", "Case ID cannot be empty.")
    # กฎ: รหัสคดีต้องไม่ซ้ำกับที่มีอยู่
    if find_case_by_id(case_id) is not None:
        return get_text("รหัสคดีนี้มีอยู่แล้ว", "This case ID already exists.")
    return ""


def validate_case_fields(name: str, description: str, difficulty_input: str) -> str:
    """ตรวจชื่อ รายละเอียด และระดับความยาก คืนข้อความผิดพลาด หรือ "" หากถูกต้อง"""
    # กฎ: ชื่อและรายละเอียดต้องไม่ว่างเปล่า
    if not name or not description:
        return get_text("กรุณากรอกข้อมูลให้ครบ", "Please fill in all fields.")
    # กฎ: ระดับความยากต้องเป็น ง่าย/ปานกลาง/ยาก
    if parse_difficulty(difficulty_input) is None:
        return get_text("ระดับความยากไม่ถูกต้อง", "Invalid difficulty level.")
    return ""


def create_case(case_id: str, name: str, description: str, difficulty: str) -> dict:
    """สร้างคดีใหม่ (สถานะเริ่มต้น 'open') เพิ่มเข้าระบบ บันทึก และคืนค่าคดีที่สร้าง"""
    new_case = {
        "รหัส": case_id,
        "ชื่อ_th": name,
        "ชื่อ_en": name,
        "สถานะ": "open",
        "ระดับ": difficulty,
        "รายละเอียด_th": description,
        "รายละเอียด_en": description
    }
    all_cases.append(new_case)
    storage.auto_save()
    return new_case


def update_case(case: dict, name: str, description: str, difficulty: str) -> None:
    """แก้ไขคดี (ชื่อและรายละเอียดของภาษาปัจจุบัน ค่าว่าง = ใช้ค่าเดิม) แล้วบันทึก"""
    lang = get_language()
    if name:
        case[f"ชื่อ_{lang}"] = name
    if description:
        case[f"รายละเอียด_{lang}"] = description
    case["ระดับ"] = difficulty
    storage.auto_save()


def set_case_status(case: dict, status: str) -> None:
    """เปลี่ยนสถานะคดีแล้วบันทึก"""
    case["สถานะ"] = status
    if status == "open":
        # เปิดคดีใหม่: ล้างจำนวนครั้งที่ชี้ตัวผิด เพื่อให้เล่นเกมสืบสวนได้อีกครั้ง
        case["ตอบผิด"] = 0
    storage.auto_save()


def remove_case(case: dict) -> int:
    """ลบคดีพร้อมหลักฐานที่เชื่อมโยง บันทึก และคืนค่าจำนวนหลักฐานที่ถูกลบ"""
    import evidence

    all_cases.remove(case)
    removed = evidence.remove_evidence_by_case(case["รหัส"])
    storage.auto_save()
    return removed


def match_cases(query: str) -> list:
    """ค้นหาคดีที่มีคำค้นอยู่ในรหัส ชื่อ หรือรายละเอียด (ทั้งสองภาษา ไม่สนตัวพิมพ์เล็ก/ใหญ่)"""
    query = query.strip().lower()
    result = []
    for case in all_cases:
        if (
            query in case["รหัส"].lower()
            or query in case.get("ชื่อ_th", "").lower()
            or query in case.get("ชื่อ_en", "").lower()
            or query in case.get("รายละเอียด_th", "").lower()
            or query in case.get("รายละเอียด_en", "").lower()
        ):
            result.append(case)
    return result


def case_statistics() -> dict:
    """คำนวณสถิติคดี: จำนวนตามสถานะ จำนวนตามระดับ จำนวนหลักฐาน และอัตราปิดคดี (%)"""
    import evidence

    stats = {
        "total": len(all_cases),
        "open": 0, "closed": 0, "cold": 0,
        "easy": 0, "medium": 0, "hard": 0,
        "evidence": len(evidence.get_all_evidence()),
        "rate": 0.0,
    }
    for case in all_cases:
        if case["สถานะ"] in stats:
            stats[case["สถานะ"]] += 1
        if case["ระดับ"] in stats:
            stats[case["ระดับ"]] += 1

    if stats["total"] > 0:
        stats["rate"] = stats["closed"] / stats["total"] * 100
    return stats


def view_all_cases() -> None:
    """แสดงรายการแฟ้มคดีทั้งหมดพร้อมสถานะและระดับความยาก"""
    lang = get_language()
    print(get_text(
        "\n========== แฟ้มคดีทั้งหมด ==========",
        "\n========== ALL CASE FILES =========="
    ))

    if not all_cases:
        print(get_text("ยังไม่มีข้อมูลคดี", "No cases found."))
        return

    for case in all_cases:
        status = status_text(case["สถานะ"])
        diff = difficulty_text(case["ระดับ"])

        name_key = f"ชื่อ_{lang}" if f"ชื่อ_{lang}" in case else "ชื่อ_th"
        print(f"\n{get_text('รหัสคดี', 'Case ID')}: {case['รหัส']}")
        print(f"{get_text('ชื่อคดี', 'Case Name')}: {case.get(name_key, case.get('ชื่อ_th', ''))}")
        print(f"{get_text('สถานะ', 'Status')}: {status}")
        print(f"{get_text('ระดับความยาก', 'Difficulty')}: {diff}")


def view_case_details() -> None:
    """เปิดดูรายละเอียดเชิงลึกของคดี พร้อมแสดงหลักฐานที่เกี่ยวข้อง"""
    import evidence

    lang = get_language()
    case_id = input(get_text("\nกรอกรหัสคดี: ", "\nEnter case ID: ")).strip()
    case = find_case_by_id(case_id)

    if case is None:
        print(get_text("ไม่พบคดี", "Case not found."))
        return

    status = status_text(case["สถานะ"])
    diff = difficulty_text(case["ระดับ"])

    name_key = f"ชื่อ_{lang}" if f"ชื่อ_{lang}" in case else "ชื่อ_th"
    desc_key = f"รายละเอียด_{lang}" if f"รายละเอียด_{lang}" in case else "รายละเอียด_th"

    print("\n" + "=" * 40)
    print(f"{get_text('รหัสคดี', 'Case ID')}: {case['รหัส']}")
    print(f"{get_text('ชื่อคดี', 'Case Name')}: {case.get(name_key, case.get('ชื่อ_th', ''))}")
    print(f"{get_text('สถานะ', 'Status')}: {status}")
    print(f"{get_text('ระดับความยาก', 'Difficulty')}: {diff}")
    print(f"{get_text('รายละเอียด', 'Description')}: {case.get(desc_key, case.get('รายละเอียด_th', ''))}")

    # แสดงหลักฐานที่เชื่อมโยงกับคดีนี้
    linked_evidence = evidence.find_evidence_by_case(case["รหัส"])
    print("\n" + get_text("--- หลักฐานที่เกี่ยวข้อง ---", "--- Linked Evidence ---"))
    if linked_evidence:
        for evd in linked_evidence:
            evd_name_key = f"ชื่อ_{lang}" if f"ชื่อ_{lang}" in evd else "ชื่อ_th"
            print(f"- [{evd['รหัส']}] {evd.get(evd_name_key, evd.get('ชื่อ_th', ''))}")
    else:
        print(get_text("ไม่มีหลักฐานที่เชื่อมโยงกับคดีนี้", "No evidence linked to this case."))
    print("=" * 40)


def add_new_case() -> None:
    """เพิ่มคดีใหม่เข้าสู่ระบบ พร้อมการตรวจสอบความถูกต้องของข้อมูล"""
    print(get_text(
        "\n========== เพิ่มคดีใหม่ ==========",
        "\n========== ADD NEW CASE =========="
    ))

    # กฎ: รหัสคดีต้องไม่ว่างและไม่ซ้ำ (ตรวจก่อนถามข้อมูลอื่น)
    case_id = input(get_text("รหัสคดี (เช่น CASE-003): ", "Case ID (e.g. CASE-003): ")).strip()
    error = validate_case_id(case_id)
    if error:
        print(error)
        return

    name = input(get_text("ชื่อคดี: ", "Case name: ")).strip()
    description = input(get_text("รายละเอียดคดี: ", "Case description: ")).strip()
    diff_input = input(get_text(
        "ระดับความยาก (ง่าย/ปานกลาง/ยาก หรือ easy/medium/hard): ",
        "Difficulty (easy/medium/hard): "
    )).strip()

    # กฎ: ชื่อและรายละเอียดห้ามว่าง และระดับความยากต้องถูกต้อง
    error = validate_case_fields(name, description, diff_input)
    if error:
        print(error)
        return

    create_case(case_id, name, description, parse_difficulty(diff_input))
    print(get_text("เพิ่มคดีใหม่สำเร็จ", "Case added successfully."))


def search_cases() -> None:
    """ค้นหาคดีจากชื่อหรือรหัส (Case-insensitive substring search)"""
    lang = get_language()
    query = input(get_text(
        "\nกรอกชื่อหรือรหัสคดีที่ต้องการค้นหา: ",
        "\nEnter a case name or ID to search: "
    )).strip().lower()

    if not query:
        print(get_text("กรุณากรอกคำค้นหา", "Please enter a search term."))
        return

    found = match_cases(query)
    for case in found:
        name_key = f"ชื่อ_{lang}" if f"ชื่อ_{lang}" in case else "ชื่อ_th"
        print(f"\n[{case['รหัส']}] {case.get(name_key, case.get('ชื่อ_th', ''))} | {status_text(case['สถานะ'])}")

    if not found:
        print(get_text("ไม่พบคดีที่ตรงกัน", "No matching cases found."))


def investigation_report() -> None:
    """คำนวณและแสดงผลสถิติการสืบสวน (อัตราการปิดคดี จำนวนคดีและหลักฐาน)"""
    stats = case_statistics()

    print(get_text(
        "\n========== รายงานการสืบสวน ==========",
        "\n========== INVESTIGATION REPORT =========="
    ))
    print(f"{get_text('จำนวนคดีทั้งหมด', 'Total Cases')}: {stats['total']}")
    print(f"{get_text('คดีที่กำลังสืบสวน', 'Open Cases')}: {stats['open']}")
    print(f"{get_text('คดีที่ปิดแล้ว', 'Closed Cases')}: {stats['closed']}")
    print(f"{get_text('คดีค้าง', 'Cold Cases')}: {stats['cold']}")
    print(f"{get_text('จำนวนหลักฐานทั้งหมด', 'Total Evidence')}: {stats['evidence']}")
    print(f"{get_text('อัตราปิดคดี', 'Case Closure Rate')}: {stats['rate']:.1f}%")


# ลำดับระดับความยากสำหรับการเรียง (ง่าย -> ยาก)
DIFFICULTY_ORDER = {"easy": 1, "medium": 2, "hard": 3}


def print_case_rows(case_list: list) -> None:
    """แสดงรายการคดีแบบบรรทัดเดียวต่อคดี"""
    lang = get_language()
    if not case_list:
        print(get_text("ไม่พบคดีที่ตรงกับเงื่อนไข", "No cases match the criteria."))
        return

    for case in case_list:
        name_key = f"ชื่อ_{lang}" if f"ชื่อ_{lang}" in case else "ชื่อ_th"
        print(f"[{case['รหัส']}] {case.get(name_key, case.get('ชื่อ_th', ''))}"
              f" | {status_text(case['สถานะ'])} | {difficulty_text(case['ระดับ'])}")
    print(f"\n{get_text('รวม', 'Total')}: {len(case_list)}")


def filter_cases(field: str, value: str) -> list:
    """คืนรายการคดีที่ค่าในฟิลด์ที่ระบุ (เช่น 'สถานะ', 'ระดับ') ตรงกับ value"""
    result = []
    for case in all_cases:
        if case.get(field) == value:
            result.append(case)
    return result


def sort_cases(sort_by: str) -> list:
    """คืนสำเนารายการคดีที่เรียงตาม 'id', 'name' หรือ 'difficulty'"""
    lang = get_language()
    if sort_by == "name":
        return sorted(all_cases, key=lambda c: c.get(f"ชื่อ_{lang}", c.get("ชื่อ_th", "")).lower())
    if sort_by == "difficulty":
        return sorted(all_cases, key=lambda c: (DIFFICULTY_ORDER.get(c["ระดับ"], 99), c["รหัส"]))
    return sorted(all_cases, key=lambda c: c["รหัส"].lower())


def filter_by_status() -> None:
    """ให้ผู้ใช้เลือกสถานะ แล้วแสดงคดีที่มีสถานะนั้น"""
    print(get_text("1. กำลังสืบสวน", "1. Under Investigation"))
    print(get_text("2. ปิดคดีแล้ว", "2. Closed"))
    print(get_text("3. คดีค้าง", "3. Cold Case"))
    choice = input(get_text("เลือกสถานะ: ", "Select status: ")).strip()

    status_map = {"1": "open", "2": "closed", "3": "cold"}
    if choice not in status_map:
        print(get_text("ตัวเลือกไม่ถูกต้อง", "Invalid option."))
        return

    print()
    print_case_rows(filter_cases("สถานะ", status_map[choice]))


def filter_by_difficulty() -> None:
    """ให้ผู้ใช้พิมพ์ระดับความยาก แล้วแสดงคดีที่มีระดับนั้น"""
    difficulty = parse_difficulty(input(get_text(
        "ระดับความยาก (ง่าย/ปานกลาง/ยาก): ",
        "Difficulty (easy/medium/hard): "
    )))
    if difficulty is None:
        print(get_text("ระดับความยากไม่ถูกต้อง", "Invalid difficulty level."))
        return

    print()
    print_case_rows(filter_cases("ระดับ", difficulty))


def show_sorted_cases() -> None:
    """ให้ผู้ใช้เลือกวิธีเรียง แล้วแสดงคดีทั้งหมดตามลำดับนั้น"""
    print(get_text("1. เรียงตามรหัสคดี", "1. Sort by case ID"))
    print(get_text("2. เรียงตามชื่อคดี", "2. Sort by case name"))
    print(get_text("3. เรียงตามระดับความยาก (ง่าย -> ยาก)", "3. Sort by difficulty (easy -> hard)"))
    choice = input(get_text("เลือกวิธีเรียง: ", "Select sort order: ")).strip()

    sort_map = {"1": "id", "2": "name", "3": "difficulty"}
    if choice not in sort_map:
        print(get_text("ตัวเลือกไม่ถูกต้อง", "Invalid option."))
        return

    print()
    print_case_rows(sort_cases(sort_map[choice]))


def report_menu() -> None:
    """เมนูรายงาน: สถิติสรุป การกรอง และการเรียงลำดับคดี"""
    actions = {
        "1": investigation_report,
        "2": filter_by_status,
        "3": filter_by_difficulty,
        "4": show_sorted_cases,
    }

    while True:
        clear_screen()
        print(get_text(
            "\n========== รายงานการสืบสวน ==========",
            "\n========== INVESTIGATION REPORTS =========="
        ))
        print(get_text("1. สถิติสรุป", "1. Summary Statistics"))
        print(get_text("2. กรองคดีตามสถานะ", "2. Filter Cases by Status"))
        print(get_text("3. กรองคดีตามระดับความยาก", "3. Filter Cases by Difficulty"))
        print(get_text("4. เรียงลำดับคดี", "4. Sort Cases"))
        print(get_text("5. กลับเมนูหลัก", "5. Back to Main Menu"))

        choice = input(get_text("เลือกเมนู: ", "Choose an option: ")).strip()

        if choice in actions:
            clear_screen()
            actions[choice]()
            pause(prompt_th="\nกด Enter เพื่อกลับ...", prompt_en="\nPress Enter to go back...")
        elif choice == "5":
            break
        else:
            print(get_text("เมนูไม่ถูกต้อง", "Invalid option."))
            pause(prompt_th="\nกด Enter เพื่อกลับ...", prompt_en="\nPress Enter to go back...")


def update_case_status() -> None:
    """อัปเดตสถานะคดี (กำลังสืบสวน <-> ปิดคดีแล้ว)"""
    case_id = input(get_text("\nกรอกรหัสคดีที่ต้องการอัปเดต: ", "\nEnter case ID to update: ")).strip()
    case = find_case_by_id(case_id)

    if case is None:
        print(get_text("ไม่พบคดี", "Case not found."))
        return

    print(f"{get_text('สถานะปัจจุบัน', 'Current Status')}: {status_text(case['สถานะ'])}")
    print(get_text("1. กำลังสืบสวน (open)", "1. Under Investigation (open)"))
    print(get_text("2. ปิดคดีแล้ว (closed)", "2. Closed"))

    choice = input(get_text("เลือกสถานะใหม่ (1 หรือ 2): ", "Select new status (1 or 2): ")).strip()
    if choice == "1":
        set_case_status(case, "open")
        print(get_text("อัปเดตสถานะเป็น 'กำลังสืบสวน' เรียบร้อย", "Status updated to 'Open'."))
    elif choice == "2":
        set_case_status(case, "closed")
        print(get_text("อัปเดตสถานะเป็น 'ปิดคดีแล้ว' เรียบร้อย", "Status updated to 'Closed'."))
    else:
        print(get_text("ตัวเลือกไม่ถูกต้อง ยกเลิกการอัปเดต", "Invalid option. Update cancelled."))


def edit_case() -> None:
    """แก้ไขชื่อ รายละเอียด และระดับความยากของคดี (กด Enter เพื่อใช้ค่าเดิม)"""
    lang = get_language()
    case_id = input(get_text("\nกรอกรหัสคดีที่ต้องการแก้ไข: ", "\nEnter case ID to edit: ")).strip()
    case = find_case_by_id(case_id)

    # กฎ: ห้ามแก้ไขคดีที่ไม่มีอยู่จริง
    if case is None:
        print(get_text("ไม่พบคดี", "Case not found."))
        return

    name_key = f"ชื่อ_{lang}"
    desc_key = f"รายละเอียด_{lang}"
    old_name = case.get(name_key, case.get("ชื่อ_th", ""))
    old_desc = case.get(desc_key, case.get("รายละเอียด_th", ""))

    print(get_text("(กด Enter เพื่อใช้ค่าเดิม)", "(Press Enter to keep the current value)"))
    name = input(f"{get_text('ชื่อคดี', 'Case name')} [{old_name}]: ").strip()
    description = input(f"{get_text('รายละเอียดคดี', 'Case description')} [{old_desc}]: ").strip()
    diff_input = input(
        f"{get_text('ระดับความยาก (ง่าย/ปานกลาง/ยาก)', 'Difficulty (easy/medium/hard)')} "
        f"[{difficulty_text(case['ระดับ'])}]: "
    ).strip()

    # ตรวจสอบระดับความยากก่อนเปลี่ยนข้อมูลใดๆ เพื่อไม่ให้แก้ไขไปเพียงบางส่วน
    difficulty = case["ระดับ"]
    if diff_input:
        difficulty = parse_difficulty(diff_input)
        if difficulty is None:
            print(get_text("ระดับความยากไม่ถูกต้อง ยกเลิกการแก้ไข",
                           "Invalid difficulty level. Edit cancelled."))
            return

    if not name and not description and difficulty == case["ระดับ"]:
        print(get_text("ไม่มีการเปลี่ยนแปลง", "No changes made."))
        return

    update_case(case, name, description, difficulty)
    print(get_text("แก้ไขข้อมูลคดีสำเร็จ", "Case updated successfully."))


def delete_case() -> None:
    """ลบคดีออกจากระบบ พร้อมหลักฐานที่เชื่อมโยงกับคดีนั้น (ต้องยืนยันก่อน)"""
    import evidence

    lang = get_language()
    case_id = input(get_text("\nกรอกรหัสคดีที่ต้องการลบ: ", "\nEnter case ID to delete: ")).strip()
    case = find_case_by_id(case_id)

    # กฎ: ห้ามลบคดีที่ไม่มีอยู่จริง
    if case is None:
        print(get_text("ไม่พบคดี", "Case not found."))
        return

    name_key = f"ชื่อ_{lang}" if f"ชื่อ_{lang}" in case else "ชื่อ_th"
    linked_count = len(evidence.find_evidence_by_case(case["รหัส"]))

    print(f"[{case['รหัส']}] {case.get(name_key, case.get('ชื่อ_th', ''))}")
    if linked_count > 0:
        print(get_text(
            f"คำเตือน: หลักฐานที่เกี่ยวข้อง {linked_count} รายการจะถูกลบไปด้วย",
            f"Warning: {linked_count} linked evidence item(s) will also be deleted."
        ))

    confirm = input(get_text("ยืนยันการลบ? (y/n): ", "Confirm delete? (y/n): ")).strip().lower()
    if confirm != "y":
        print(get_text("ยกเลิกการลบ", "Delete cancelled."))
        return

    remove_case(case)
    print(get_text("ลบคดีสำเร็จ", "Case deleted successfully."))


def manage_cases() -> None:
    """เมนูจัดการแฟ้มคดี: ดู เพิ่ม ค้นหา แก้ไข อัปเดตสถานะ และลบคดี"""
    actions = {
        "1": view_all_cases,
        "2": view_case_details,
        "3": add_new_case,
        "4": search_cases,
        "5": edit_case,
        "6": update_case_status,
        "7": delete_case,
    }

    while True:
        clear_screen()
        print(get_text(
            "\n========== แฟ้มคดี ==========",
            "\n========== CASE FILES =========="
        ))
        print(get_text("1. แสดงคดีทั้งหมด", "1. View All Cases"))
        print(get_text("2. เปิดดูรายละเอียดคดี", "2. View Case Details"))
        print(get_text("3. เพิ่มคดีใหม่", "3. Add New Case"))
        print(get_text("4. ค้นหาคดี", "4. Search Cases"))
        print(get_text("5. แก้ไขข้อมูลคดี", "5. Edit Case"))
        print(get_text("6. อัปเดตสถานะคดี", "6. Update Case Status"))
        print(get_text("7. ลบคดี", "7. Delete Case"))
        print(get_text("8. กลับเมนูหลัก", "8. Back to Main Menu"))

        choice = input(get_text("เลือกเมนู: ", "Choose an option: ")).strip()

        if choice in actions:
            clear_screen()
            actions[choice]()
            pause(prompt_th="\nกด Enter เพื่อกลับ...", prompt_en="\nPress Enter to go back...")
        elif choice == "8":
            break
        else:
            print(get_text("เมนูไม่ถูกต้อง", "Invalid option."))
            pause(prompt_th="\nกด Enter เพื่อกลับ...", prompt_en="\nPress Enter to go back...")
