#!/usr/bin/env python3
"""
WITCH'S BREW - ร้านยาแม่มด: ซื้อสมุนไพร ปรุงยา ค้นพบสูตรลับ และรักษาชาวบ้าน
จุดเริ่มต้นโปรแกรม: โหลดเซฟ เลือกภาษา และเข้าเมนูหลัก
Entry point: load the save, choose a language, and open the main menu.
"""

from language import choose_language, get_text
from menu import run_menu
import storage


def main() -> None:
    """ฟังก์ชันหลักของโปรแกรม"""
    # โหลดเซฟเดิม (ถ้าไม่มีหรือไฟล์เสีย จะเริ่มร้านใหม่)
    storage.load_game()

    try:
        choose_language()
        run_menu()
    except (KeyboardInterrupt, EOFError):
        # ผู้ใช้กด Ctrl+C หรือ Ctrl+D: บันทึกแล้วออกโดยไม่ crash
        storage.save_game()
        print("\n" + get_text("ออกจากร้าน บันทึกความคืบหน้าแล้ว", "Exiting. Progress saved."))


if __name__ == "__main__":
    main()
