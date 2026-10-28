#!/usr/bin/env python3
"""
Storage Module - CASE ZERO
บันทึกและโหลดข้อมูล JSON สำหรับคดีและหลักฐาน
Save and load cases and evidence data in JSON format.
"""

import copy
import json
import os

# เก็บไฟล์ข้อมูลไว้ในโฟลเดอร์เดียวกับโปรแกรม ไม่ว่าจะสั่งรันจากโฟลเดอร์ไหน
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "case_zero_data.json")

# ข้อมูลเริ่มต้นสำหรับระบบ
# คดีที่มี "ผู้ต้องสงสัย" เล่นในโหมดเกมสืบสวนได้:
#   "คนร้าย"       = รหัสผู้ต้องสงสัยที่เป็นคนร้าย
#   "หลักฐานสำคัญ" = รหัสหลักฐานที่พิสูจน์ว่าคนร้ายโกหก
#   "ตอบผิด"       = จำนวนครั้งที่ผู้เล่นชี้ตัวผิด
DEFAULT_CASES = [
    {
        "รหัส": "CASE-001",
        "ชื่อ_th": "ห้องปิดตาย",
        "ชื่อ_en": "The Locked Room",
        "สถานะ": "open",
        "ระดับ": "medium",
        "รายละเอียด_th": "ผู้เช่าห้อง 304 ถูกทำร้ายเวลาประมาณ 23:10 ประตูห้องเปิดได้ด้วยคีย์การ์ดเท่านั้น",
        "รายละเอียด_en": "The tenant of room 304 was attacked at around 23:10. The door only opens with a key card.",
        "ผู้ต้องสงสัย": [
            {
                "รหัส": "S1",
                "ชื่อ_th": "มาลี (แม่บ้าน)",
                "ชื่อ_en": "Malee (Housekeeper)",
                "คำให้การ_th": "ฉันทำความสะอาดชั้น 3 เสร็จแล้วกลับบ้านตอน 4 ทุ่มค่ะ บัตรมาสเตอร์ฉันคืนไว้ที่ล็อบบี้แล้ว",
                "คำให้การ_en": "I finished cleaning the 3rd floor and went home at 22:00. I returned my master card at the lobby."
            },
            {
                "รหัส": "S2",
                "ชื่อ_th": "ธนา (เพื่อนบ้านห้อง 305)",
                "ชื่อ_en": "Thana (Neighbor in room 305)",
                "คำให้การ_th": "ผมแวะไปคุยกับเขาตอน 3 ทุ่ม แล้วออกไปร้านสะดวกซื้อตอนห้าทุ่ม กลับมาก็เห็นตำรวจแล้ว",
                "คำให้การ_en": "I chatted with him at 21:00, then went to the convenience store at 23:00. When I came back, the police were here."
            },
            {
                "รหัส": "S3",
                "ชื่อ_th": "วิชัย (ผู้จัดการอาคาร)",
                "ชื่อ_en": "Wichai (Building Manager)",
                "คำให้การ_th": "ผมนอนหลับอยู่ที่บ้านทั้งคืน บัตรมาสเตอร์ของผมก็อยู่กับตัวตลอด",
                "คำให้การ_en": "I was asleep at home all night, and my master card never left my side."
            }
        ],
        "คนร้าย": "S3",
        "หลักฐานสำคัญ": "EVD-004",
        "เฉลย_th": "บัตรมาสเตอร์มีแค่ 2 ใบ ใบของมาลีถูกคืนไว้ที่ล็อบบี้ตั้งแต่ 22:00 ดังนั้นใบที่เปิดห้อง 304 ตอน 23:10 ต้องเป็นของวิชัย ซึ่งอ้างว่าบัตรอยู่กับตัวและอยู่บ้านทั้งคืน ส่วนลายนิ้วมือของธนาบนแก้วมาจากตอนที่เขาแวะมาตอน 3 ทุ่ม",
        "เฉลย_en": "There are only 2 master cards. Malee's was returned to the lobby at 22:00, so the card that opened room 304 at 23:10 must be Wichai's, even though he claims he kept it with him at home. Thana's fingerprints on the glass are from his 21:00 visit.",
        "ตอบผิด": 0
    },
    {
        "รหัส": "CASE-002",
        "ชื่อ_th": "จดหมายฉบับสุดท้าย",
        "ชื่อ_en": "The Last Letter",
        "สถานะ": "closed",
        "ระดับ": "easy",
        "รายละเอียด_th": "จดหมายที่หายไปซ่อนความลับสำคัญ",
        "รายละเอียด_en": "A missing letter hides an important secret."
    },
    {
        "รหัส": "CASE-003",
        "ชื่อ_th": "ภาพวาดที่หายไป",
        "ชื่อ_en": "The Missing Painting",
        "สถานะ": "open",
        "ระดับ": "hard",
        "รายละเอียด_th": "ภาพวาดชิ้นเอกของหอศิลป์ถูกขโมยไประหว่างเวลา 00:55 ถึง 01:20 ระหว่างนั้นกล้องวงจรปิดถูกปิดอยู่",
        "รายละเอียด_en": "The gallery's masterpiece was stolen between 00:55 and 01:20, while the cameras were switched off.",
        "ผู้ต้องสงสัย": [
            {
                "รหัส": "S1",
                "ชื่อ_th": "นิดา (ภัณฑารักษ์)",
                "ชื่อ_en": "Nida (Curator)",
                "คำให้การ_th": "ฉันไปงานเลี้ยงวันเกิดเพื่อนที่ร้านอาหารจนถึงตีสองค่ะ",
                "คำให้การ_en": "I was at a friend's birthday party at a restaurant until 02:00."
            },
            {
                "รหัส": "S2",
                "ชื่อ_th": "สมชาย (ยามกะดึก)",
                "ชื่อ_en": "Somchai (Night Guard)",
                "คำให้การ_th": "ผมเดินตรวจชั้นสองตามจุดสแกนครบทุกรอบทั้งคืน ไม่ได้เข้าห้องควบคุมเลยครับ",
                "คำให้การ_en": "I scanned every checkpoint on the second floor all night. I never entered the control room."
            },
            {
                "รหัส": "S3",
                "ชื่อ_th": "ต้น (นักศึกษาฝึกงาน)",
                "ชื่อ_en": "Ton (Intern)",
                "คำให้การ_th": "ผมช่วยติดตั้งภาพนี้เมื่อวานตอนบ่าย แล้วกลับหอตั้งแต่ 6 โมงเย็นครับ",
                "คำให้การ_en": "I helped hang this painting yesterday afternoon and went back to my dorm at 18:00."
            }
        ],
        "คนร้าย": "S2",
        "หลักฐานสำคัญ": "EVD-008",
        "เฉลย_th": "กล้องถูกปิดด้วยรหัสที่มีแค่ยามกับภัณฑารักษ์รู้ ต้นจึงทำไม่ได้ (ลายนิ้วมือของเขามาจากตอนติดตั้งภาพ) นิดาอยู่ในรูปที่ร้านตอน 01:05 ส่วนสมชายอ้างว่าสแกนจุดตรวจครบทุกรอบ แต่บันทึกไม่มีการสแกนเลยช่วง 00:40-01:30",
        "เฉลย_en": "The cameras were switched off with a code only the guard and the curator know, so Ton couldn't have done it (his fingerprints are from hanging the painting). Nida is in a photo at the restaurant at 01:05. Somchai claims he scanned every checkpoint, but the log shows no scans from 00:40 to 01:30.",
        "ตอบผิด": 0
    }
]

DEFAULT_EVIDENCE = [
    {
        "รหัส": "EVD-001",
        "รหัสคดี": "CASE-001",
        "ชื่อ_th": "รอยรองเท้า",
        "ชื่อ_en": "Footprints",
        "รายละเอียด_th": "รอยรองเท้าผู้ชายเบอร์ 44 จากประตูเข้าไปในห้อง",
        "รายละเอียด_en": "Men's size 44 shoe prints leading from the door into the room."
    },
    {
        "รหัส": "EVD-002",
        "รหัสคดี": "CASE-001",
        "ชื่อ_th": "แก้วน้ำบนโต๊ะ",
        "ชื่อ_en": "Glass on the Table",
        "รายละเอียด_th": "แก้วน้ำที่มีลายนิ้วมือของธนา น้ำในแก้วแห้งไปเกือบหมดแล้ว",
        "รายละเอียด_en": "A glass with Thana's fingerprints. The water in it has almost dried up."
    },
    {
        "รหัส": "EVD-003",
        "รหัสคดี": "CASE-001",
        "ชื่อ_th": "ใบเสร็จร้านสะดวกซื้อ",
        "ชื่อ_en": "Convenience Store Receipt",
        "รายละเอียด_th": "ใบเสร็จของธนา เวลา 23:05 กล้องในร้านถ่ายเขาไว้ได้จนถึง 23:30",
        "รายละเอียด_en": "Thana's receipt at 23:05. The store camera shows him there until 23:30."
    },
    {
        "รหัส": "EVD-004",
        "รหัสคดี": "CASE-001",
        "ชื่อ_th": "บันทึกคีย์การ์ด",
        "ชื่อ_en": "Key Card Log",
        "รายละเอียด_th": "ประตูห้อง 304 ถูกเปิดเวลา 23:10 ด้วยบัตรมาสเตอร์ อาคารนี้มีบัตรมาสเตอร์แค่ 2 ใบ (แม่บ้านและผู้จัดการ)",
        "รายละเอียด_en": "Room 304 was opened at 23:10 with a master card. The building has only 2 master cards (housekeeper and manager)."
    },
    {
        "รหัส": "EVD-005",
        "รหัสคดี": "CASE-003",
        "ชื่อ_th": "แผงควบคุมกล้อง",
        "ชื่อ_en": "Camera Control Panel",
        "รายละเอียด_th": "กล้องถูกปิดจากห้องควบคุมเวลา 00:55 ด้วยรหัสที่มีแค่ยามและภัณฑารักษ์รู้",
        "รายละเอียด_en": "The cameras were switched off from the control room at 00:55 using a code only the guard and the curator know."
    },
    {
        "รหัส": "EVD-006",
        "รหัสคดี": "CASE-003",
        "ชื่อ_th": "ลายนิ้วมือบนกรอบรูป",
        "ชื่อ_en": "Fingerprints on the Frame",
        "รายละเอียด_th": "พบลายนิ้วมือของต้นหลายจุดบนกรอบรูปที่ว่างเปล่า",
        "รายละเอียด_en": "Ton's fingerprints were found all over the empty frame."
    },
    {
        "รหัส": "EVD-007",
        "รหัสคดี": "CASE-003",
        "ชื่อ_th": "รูปถ่ายงานเลี้ยง",
        "ชื่อ_en": "Party Photo",
        "รายละเอียด_th": "รูปในโซเชียลของเพื่อนนิดา ถ่ายที่ร้านอาหารเวลา 01:05 มีนิดาอยู่ในรูป",
        "รายละเอียด_en": "A photo on Nida's friend's social media, taken at the restaurant at 01:05, shows Nida."
    },
    {
        "รหัส": "EVD-008",
        "รหัสคดี": "CASE-003",
        "ชื่อ_th": "บันทึกจุดสแกนของยาม",
        "ชื่อ_en": "Guard Checkpoint Log",
        "รายละเอียด_th": "จุดสแกนชั้นสองมีการสแกนทุก 15 นาที ยกเว้นช่วง 00:40-01:30 ที่ไม่มีการสแกนเลย",
        "รายละเอียด_en": "The second-floor checkpoints were scanned every 15 minutes, except from 00:40 to 01:30 when there were no scans at all."
    }
]


def load_data(filepath: str = DATA_FILE) -> tuple:
    """
    โหลดข้อมูลคดีและหลักฐานจากไฟล์ JSON
    หากไม่พบไฟล์หรือไฟล์มีปัญหา จะคืนค่าข้อมูลเริ่มต้นกลับไป
    """
    if not os.path.exists(filepath):
        # สร้างสำเนาข้อมูลเริ่มต้น (deepcopy เพราะมี list ผู้ต้องสงสัยซ้อนอยู่ข้างใน)
        return copy.deepcopy(DEFAULT_CASES), copy.deepcopy(DEFAULT_EVIDENCE)

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            loaded_cases = data.get("cases", copy.deepcopy(DEFAULT_CASES))
            loaded_evidence = data.get("evidence", copy.deepcopy(DEFAULT_EVIDENCE))
            return loaded_cases, loaded_evidence
    except (json.JSONDecodeError, OSError):
        return copy.deepcopy(DEFAULT_CASES), copy.deepcopy(DEFAULT_EVIDENCE)


def save_data(cases_list: list, evidence_list: list, filepath: str = DATA_FILE) -> bool:
    """
    บันทึกข้อมูลคดีและหลักฐานลงไฟล์ JSON ด้วยการจัดรูปแบบ UTF-8
    """
    try:
        payload = {
            "cases": cases_list,
            "evidence": evidence_list
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=4)
        return True
    except OSError:
        return False


def init_storage(filepath: str = DATA_FILE) -> None:
    """
    เตรียมข้อมูลเริ่มต้นให้กับโมดูล cases และ evidence
    """
    import cases
    import evidence

    loaded_cases, loaded_evidence = load_data(filepath)
    cases.set_all_cases(loaded_cases)
    evidence.set_all_evidence(loaded_evidence)


def auto_save(filepath: str = DATA_FILE) -> bool:
    """
    ฟังก์ชันช่วยบันทึกข้อมูลอัตโนมัติจากโมดูล cases และ evidence
    """
    import cases
    import evidence

    return save_data(cases.get_all_cases(), evidence.get_all_evidence(), filepath)

