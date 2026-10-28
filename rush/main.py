#!/usr/bin/env python3
"""
LAST SHELTER - ศูนย์พักพิงสุดท้าย: บริหารคน เสบียง และการติดเชื้อ ให้รอดจนเฮลิคอปเตอร์มารับในวันที่ 15
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
