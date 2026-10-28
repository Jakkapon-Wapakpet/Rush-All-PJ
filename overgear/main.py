#!/usr/bin/env python3
"""
OVERGEAR - ร้านตีอาวุธร้านสุดท้าย: ตีอาวุธให้ทหารและผู้กล้า ก่อนมังกรบุกหมู่บ้านในวันที่ 30
จุดเริ่มต้นโปรแกรม: โหลดเซฟ เลือกภาษา และเข้าหน้าแรก
Entry point: load the save, choose a language, and open the title screen.
"""

from language import choose_language, get_text
from menu import title_menu
import storage


def main() -> None:
    """ฟังก์ชันหลักของเกม"""
    # โหลดเซฟเดิม (ถ้าไม่มีหรือไฟล์เสีย จะเริ่มเกมใหม่)
    storage.load_game()

    try:
        choose_language()
        title_menu()
    except (KeyboardInterrupt, EOFError):
        # ผู้เล่นกด Ctrl+C หรือ Ctrl+D: บันทึกแล้วออกโดยไม่ crash
        storage.save_game()
        print("\n" + get_text("ออกจากเกม บันทึกความคืบหน้าแล้ว", "Exiting. Progress saved."))


if __name__ == "__main__":
    main()
