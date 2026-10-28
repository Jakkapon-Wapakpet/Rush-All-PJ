#!/usr/bin/env python3
"""
CASE ZERO - Mystery Investigation System
จุดเริ่มต้นโปรแกรม เลือกภาษาและเรียกเมนูหลัก
Entry point of the program: initialize storage, choose language, and launch menu.
"""

from language import choose_language, get_text
from menu import run_menu
import storage


def main() -> None:
    """ฟังก์ชันหลักสำหรับเริ่มต้นระบบ CASE ZERO"""
    # โหลดข้อมูลคดีและหลักฐานจาก JSON หรือชุดข้อมูลเริ่มต้น
    storage.init_storage()

    try:
        # เลือกภาษาเริ่มต้นของโปรแกรม
        choose_language()

        # เข้าสู่เมนูหลักและเริ่มการนำทาง
        run_menu()
    except (KeyboardInterrupt, EOFError):
        # ผู้ใช้กด Ctrl+C หรือ Ctrl+D: บันทึกข้อมูลแล้วออกโดยไม่ crash
        storage.auto_save()
        print("\n" + get_text("ออกจากระบบ ข้อมูลถูกบันทึกแล้ว", "Exiting. Data saved."))


if __name__ == "__main__":
    main()
