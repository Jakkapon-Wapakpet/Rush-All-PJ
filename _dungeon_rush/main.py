#!/usr/bin/env python3
"""
DUNGEON RUSH - เกม RPG จัดทีมฮีโร่ ซื้ออุปกรณ์ และพิชิตดันเจี้ยน 5 ชั้น
จุดเริ่มต้นโปรแกรม: โหลดเซฟ เลือกภาษา และเข้าเมนูหลัก
Entry point: load the save, choose a language, and open the main menu.
"""

from language import choose_language, get_text
from menu import run_menu
import storage


def main() -> None:
    """ฟังก์ชันหลักของเกม"""
    # โหลดเซฟเดิม (ถ้าไม่มีหรือไฟล์เสีย จะเริ่มเกมใหม่)
    storage.load_game()

    try:
        choose_language()
        run_menu()
    except (KeyboardInterrupt, EOFError):
        # ผู้เล่นกด Ctrl+C หรือ Ctrl+D: บันทึกแล้วออกโดยไม่ crash
        storage.save_game()
        print("\n" + get_text("ออกจากเกม บันทึกความคืบหน้าแล้ว", "Exiting. Progress saved."))


if __name__ == "__main__":
    main()
