#!/usr/bin/env python3
"""
Game Module - CASE ZERO
โหมดเกมสืบสวน: อ่านแฟ้มคดี วิเคราะห์หลักฐานกับคำให้การ แล้วชี้ตัวคนร้ายพร้อมหลักฐาน
Investigation game: read the case file, compare evidence with testimonies,
then accuse the culprit and present the evidence that proves their lie.
"""

from language import get_text, get_language, clear_screen, pause
import cases
import evidence
import storage

# จำนวนครั้งที่ชี้ตัวผิดได้ก่อนคดีกลายเป็นคดีค้าง
MAX_WRONG = 3


def local(item: dict, field: str) -> str:
    """คืนค่าฟิลด์ตามภาษาปัจจุบัน เช่น local(case, 'ชื่อ') -> case['ชื่อ_th']"""
    return item.get(f"{field}_{get_language()}", item.get(f"{field}_th", ""))


def choose_from_list(items: list, prompt_th: str, prompt_en: str):
    """
    ให้ผู้ใช้เลือกรายการด้วยหมายเลข (1, 2, 3, ...)
    คืนค่ารายการที่เลือก หรือ None หากกรอกไม่ถูกต้อง
    """
    choice = input(get_text(prompt_th, prompt_en)).strip()
    try:
        number = int(choice)
    except ValueError:
        print(get_text("กรุณากรอกเป็นตัวเลข", "Please enter a number."))
        return None

    if number < 1 or number > len(items):
        print(get_text("ไม่มีหมายเลขนี้", "That number is not on the list."))
        return None
    return items[number - 1]


def playable_cases() -> list:
    """คืนรายการคดีที่ยังเปิดอยู่และมีผู้ต้องสงสัยให้สืบสวน"""
    result = []
    for case in cases.get_all_cases():
        if case["สถานะ"] == "open" and case.get("ผู้ต้องสงสัย"):
            result.append(case)
    return result


def check_accusation(case: dict, suspect_id: str, evidence_id: str) -> str:
    """
    ตรวจข้อกล่าวหา อัปเดตสถานะคดี และบันทึกข้อมูล (ใช้ร่วมกันทั้ง Terminal และ GUI)
    คืนค่า 'solved' (ไขคดีได้), 'wrong' (ผิดแต่ยังเล่นต่อได้) หรือ 'cold' (ผิดครบ คดีค้าง)
    """
    # กฎ: ต้องชี้ตัวถูกและเลือกหลักฐานถูก จึงจะปิดคดีได้
    if suspect_id == case["คนร้าย"] and evidence_id == case["หลักฐานสำคัญ"]:
        case["สถานะ"] = "closed"
        storage.auto_save()
        return "solved"

    # กฎ: ชี้ผิดครบ MAX_WRONG ครั้ง คดีจะกลายเป็นคดีค้าง
    case["ตอบผิด"] = case.get("ตอบผิด", 0) + 1
    if case["ตอบผิด"] >= MAX_WRONG:
        case["สถานะ"] = "cold"
        storage.auto_save()
        return "cold"

    storage.auto_save()
    return "wrong"


def print_evidence(case_evidence: list) -> None:
    """แสดงหลักฐานทั้งหมดของคดีพร้อมรายละเอียด"""
    print(get_text("\n🔍 หลักฐาน", "\n🔍 EVIDENCE"))
    for number, evd in enumerate(case_evidence, start=1):
        print(f"  {number}. {local(evd, 'ชื่อ')}")
        print(f"     {local(evd, 'รายละเอียด')}")


def print_suspects(suspects: list) -> None:
    """แสดงผู้ต้องสงสัยทุกคนพร้อมคำให้การ"""
    print(get_text("\n🗣  ผู้ต้องสงสัยและคำให้การ", "\n🗣  SUSPECTS AND TESTIMONIES"))
    for number, suspect in enumerate(suspects, start=1):
        print(f"  {number}. {local(suspect, 'ชื่อ')}")
        print(f"     \"{local(suspect, 'คำให้การ')}\"")


def show_case_file(case: dict, case_evidence: list) -> None:
    """แสดงแฟ้มคดีทั้งหมดในหน้าเดียว: รายละเอียด หลักฐาน และคำให้การ"""
    print("=" * 60)
    print(f"🕵  [{case['รหัส']}] {local(case, 'ชื่อ')}  ({cases.difficulty_text(case['ระดับ'])})")
    print("=" * 60)
    print(local(case, "รายละเอียด"))
    print_evidence(case_evidence)
    print_suspects(case["ผู้ต้องสงสัย"])
    print(f"\n{get_text('ชี้ตัวผิดไปแล้ว', 'Wrong accusations')}: {case.get('ตอบผิด', 0)}/{MAX_WRONG}")


def accuse_suspect(case: dict, case_evidence: list) -> bool:
    """
    ให้ผู้เล่นชี้ตัวคนร้าย แล้วเลือกหลักฐานที่พิสูจน์ว่าคนนั้นโกหก
    คืนค่า True หากเกมจบ (ไขคดีได้ หรือชี้ผิดครบจำนวนครั้ง) และ False หากยังเล่นต่อได้
    """
    suspects = case["ผู้ต้องสงสัย"]

    print_suspects(suspects)
    suspect = choose_from_list(suspects, "\nใครคือคนร้าย? ", "\nWho is the culprit? ")
    if suspect is None:
        return False

    print_evidence(case_evidence)
    proof = choose_from_list(
        case_evidence,
        f"\nหลักฐานชิ้นไหนพิสูจน์ว่า {local(suspect, 'ชื่อ')} โกหก? ",
        f"\nWhich evidence proves {local(suspect, 'ชื่อ')} is lying? "
    )
    if proof is None:
        return False

    result = check_accusation(case, suspect["รหัส"], proof["รหัส"])

    if result == "solved":
        print(get_text(
            f"\n🎉 ถูกต้อง! {local(suspect, 'ชื่อ')} คือคนร้าย ปิดคดีสำเร็จ",
            f"\n🎉 Correct! {local(suspect, 'ชื่อ')} is the culprit. Case closed."
        ))
        print(f"\n{get_text('เฉลย', 'Explanation')}: {local(case, 'เฉลย')}")
        return True

    if result == "cold":
        print(get_text(
            "\n❌ ข้อกล่าวหาไม่มีน้ำหนักอีกแล้ว... คดีนี้กลายเป็นคดีค้าง",
            "\n❌ Another weak accusation... The case has gone cold."
        ))
        return True

    chances = MAX_WRONG - case["ตอบผิด"]
    print(get_text(
        f"\n❌ ข้อกล่าวหาไม่มีน้ำหนักพอ ลองวิเคราะห์ใหม่ (เหลือโอกาส {chances} ครั้ง)",
        f"\n❌ The accusation doesn't hold up. Think again. ({chances} chance(s) left)"
    ))
    return False


def play_case(case: dict) -> None:
    """ลูปการสืบสวนของคดีหนึ่งคดี"""
    case_evidence = evidence.find_evidence_by_case(case["รหัส"])

    while True:
        clear_screen()
        show_case_file(case, case_evidence)
        print(get_text("\n1. ชี้ตัวคนร้าย", "\n1. Accuse the Culprit"))
        print(get_text("2. พักการสืบสวน (กลับเมนูหลัก)", "2. Pause Investigation (Main Menu)"))

        choice = input(get_text("เลือก: ", "Choose: ")).strip()

        if choice == "1":
            if accuse_suspect(case, case_evidence):
                return
        elif choice == "2":
            return
        else:
            print(get_text("เมนูไม่ถูกต้อง", "Invalid option."))

        pause(prompt_th="\nกด Enter เพื่อกลับไปที่แฟ้มคดี...", prompt_en="\nPress Enter to return to the case file...")


def start_investigation() -> None:
    """เลือกคดีที่ยังเปิดอยู่เพื่อเริ่มเล่นเกมสืบสวน"""
    available = playable_cases()
    print(get_text(
        "\n========== เริ่มการสืบสวน ==========",
        "\n========== START INVESTIGATION =========="
    ))

    if not available:
        print(get_text("ไม่มีคดีที่รอการสืบสวน", "No cases are waiting to be investigated."))
        return

    for number, case in enumerate(available, start=1):
        print(f"{number}. [{case['รหัส']}] {local(case, 'ชื่อ')} ({cases.difficulty_text(case['ระดับ'])})")

    case = choose_from_list(available, "\nเลือกคดี: ", "\nChoose a case: ")
    if case is None:
        return

    play_case(case)
