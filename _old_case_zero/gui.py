#!/usr/bin/env python3
"""
GUI Module - CASE ZERO (Bonus)
หน้าต่างเกมสืบสวนด้วย Tkinter ใช้ข้อมูลและกฎของเกมชุดเดียวกับเวอร์ชัน Terminal
Tkinter window for the investigation game, sharing data and rules with the terminal version.

มี 3 แท็บ:
  สืบสวน  = กระดานสืบสวน (รายการคดี / การ์ดหลักฐานและผู้ต้องสงสัย / แถบข้อกล่าวหา)
  แฟ้มคดี = ค้นหา กรอง เรียง เพิ่ม แก้ไข ลบคดี และเพิ่มหลักฐาน (gui_manage.py)
  รายงาน  = สถิติและกราฟ (gui_manage.py)
"""

import sys

try:
    import tkinter as tk
except ImportError:
    print("Tkinter is not installed. Please run: python3 main.py")
    print("เครื่องนี้ไม่มี Tkinter กรุณาใช้: python3 main.py")
    sys.exit(1)

from language import get_text, get_language, set_language
import cases
import evidence
import game
import storage
from gui_theme import (COLORS, AVATAR_COLORS, FONT, FONT_SMALL, FONT_BOLD, FONT_NAME, FONT_QUOTE,
                       FONT_LOGO, STATUS_STYLE, ScrollableFrame, add_hover, bind_click, initial_of,
                       show_dialog, split_name, text_of, type_font)
from gui_manage import ManageView, ReportView


class CaseZeroApp:
    """หน้าต่างหลักของเกมแบบกระดานสืบสวน"""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.case = None              # คดีที่เลือกอยู่
        self.story_cases = []         # คดีที่มีเนื้อเรื่องให้เล่น ตามลำดับใน listbox
        self.suspect_id = None        # ผู้ต้องสงสัยที่ผู้เล่นคลิกเลือก
        self.evidence_id = None       # หลักฐานที่ผู้เล่นคลิกเลือก
        self.suspect_cards = {}       # รหัสผู้ต้องสงสัย -> (การ์ด, ป้าย)
        self.evidence_cards = {}      # รหัสหลักฐาน -> (การ์ด, ป้าย)
        self.current_tab = "play"

        root.title("CASE ZERO")
        root.geometry("1320x820")
        root.minsize(1200, 680)
        root.configure(bg=COLORS["bg"])
        self.build_layout()
        self.refresh_all()

    # ---------- โครงหน้าต่าง ----------

    def build_layout(self) -> None:
        """สร้างส่วนที่อยู่คงที่ของหน้าต่าง: หัว รายการคดี พื้นที่การ์ด และแถบข้อกล่าวหา"""
        header = tk.Frame(self.root, bg=COLORS["bg"], padx=20, pady=12)
        header.pack(fill="x")
        tk.Label(header, text="CASE ZERO", font=FONT_LOGO,
                 bg=COLORS["bg"], fg=COLORS["accent"]).pack(side="left")
        self.subtitle_label = tk.Label(header, font=FONT, bg=COLORS["bg"], fg=COLORS["muted"])
        self.subtitle_label.pack(side="left", padx=16, pady=(10, 0))

        self.lang_buttons = {}
        for lang, label in (("en", "EN"), ("th", "ไทย")):
            button = tk.Button(header, text=label, font=FONT_BOLD, width=4, relief="flat", bd=0,
                               cursor="hand2", command=lambda l=lang: self.change_language(l))
            button.pack(side="right", padx=3)
            self.lang_buttons[lang] = button

        # แท็บ: สืบสวน / แฟ้มคดี / รายงาน
        self.tabs = tk.Frame(header, bg=COLORS["bg"])
        self.tabs.pack(side="left", padx=(40, 0), pady=(8, 0))
        self.tab_buttons = {}
        for tab in ("play", "manage", "report"):
            button = tk.Button(self.tabs, relief="flat", bd=0, padx=16, pady=6, cursor="hand2",
                               command=lambda t=tab: self.show_tab(t))
            button.pack(side="left", padx=2)
            self.tab_buttons[tab] = button

        tk.Frame(self.root, bg=COLORS["accent"], height=2).pack(fill="x", padx=20)

        self.status_label = tk.Label(self.root, font=FONT_SMALL, anchor="w", padx=20, pady=6,
                                     bg=COLORS["bg"], fg=COLORS["muted"])
        self.status_label.pack(side="bottom", fill="x")

        content = tk.Frame(self.root, bg=COLORS["bg"], padx=20, pady=14)
        content.pack(fill="both", expand=True)
        body = tk.Frame(content, bg=COLORS["bg"])
        self.views = {
            "play": body,
            "manage": ManageView(content, self),
            "report": ReportView(content, self),
        }

        # ซ้าย: รายการคดี
        left = tk.Frame(body, bg=COLORS["panel"], padx=14, pady=14)
        left.pack(side="left", fill="y")
        self.cases_label = tk.Label(left, bg=COLORS["panel"], fg=COLORS["accent"])
        self.cases_label.pack(anchor="w", pady=(0, 8))
        self.case_list = tk.Listbox(
            left, width=28, font=FONT, exportselection=False, activestyle="none",
            bg=COLORS["panel"], fg=COLORS["text"], bd=0, highlightthickness=0,
            selectbackground=COLORS["accent"], selectforeground=COLORS["ink"]
        )
        self.case_list.pack(fill="y", expand=True)
        self.case_list.bind("<<ListboxSelect>>", self.on_select_case)
        self.legend_label = tk.Label(left, font=FONT_SMALL, justify="left",
                                     bg=COLORS["panel"], fg=COLORS["muted"])
        self.legend_label.pack(anchor="w", pady=(10, 0))

        # กลาง: พื้นที่การ์ด + แถบข้อกล่าวหาด้านล่าง
        center = tk.Frame(body, bg=COLORS["bg"])
        center.pack(side="left", fill="both", expand=True, padx=(16, 0))
        self.accuse_bar = tk.Frame(center, bg=COLORS["panel"], padx=18, pady=12,
                                   highlightthickness=2, highlightbackground=COLORS["panel"])
        self.accuse_bar.pack(side="bottom", fill="x", pady=(12, 0))
        self.board = ScrollableFrame(center, COLORS["bg"])
        self.board.pack(fill="both", expand=True)

    # ---------- การ์ด ----------

    def section_header(self, text: str, count: str) -> None:
        """หัวข้อของกลุ่มการ์ด เช่น 'หลักฐาน · 4 ชิ้น'"""
        row = tk.Frame(self.board.inner, bg=COLORS["bg"])
        row.pack(fill="x", pady=(18, 6))
        tk.Label(row, text=text, font=type_font(text, 14), bg=COLORS["bg"],
                 fg=COLORS["accent"]).pack(side="left")
        tk.Label(row, text=count, font=FONT_SMALL, bg=COLORS["bg"],
                 fg=COLORS["muted"]).pack(side="left", padx=10, pady=(4, 0))
        tk.Frame(row, bg=COLORS["panel_light"], height=1).pack(side="left", fill="x", expand=True, padx=(4, 0))

    def brief_card(self, case: dict) -> None:
        """การ์ดกระดาษสรุปคดีด้านบน"""
        card = tk.Frame(self.board.inner, bg=COLORS["paper"], padx=24, pady=16,
                        highlightthickness=1, highlightbackground=COLORS["paper_edge"])
        card.pack(fill="x")

        top = tk.Frame(card, bg=COLORS["paper"])
        top.pack(fill="x")
        tk.Label(top, text="CONFIDENTIAL  ·  " + case["รหัส"], font=type_font("A", 11),
                 bg=COLORS["paper"], fg=COLORS["danger"]).pack(side="left")
        tk.Label(top, font=FONT_SMALL, bg=COLORS["paper"], fg=COLORS["ink_soft"],
                 text=f"{get_text('ระดับ', 'Difficulty')}: {cases.difficulty_text(case['ระดับ'])}"
                      f"   |   {get_text('สถานะ', 'Status')}: {cases.status_text(case['สถานะ'])}"
                 ).pack(side="right")

        name = text_of(case, "ชื่อ")
        tk.Label(card, text=name, font=type_font(name, 22), bg=COLORS["paper"],
                 fg=COLORS["ink"]).pack(anchor="w", pady=(6, 4))
        tk.Label(card, text=text_of(case, "รายละเอียด"), font=FONT, wraplength=820, justify="left",
                 bg=COLORS["paper"], fg=COLORS["ink"]).pack(anchor="w")

    def evidence_card(self, parent: tk.Frame, number: int, evd: dict, clickable: bool) -> None:
        """การ์ดป้ายหลักฐานสีกระดาษ"""
        card = tk.Frame(parent, bg=COLORS["paper"], padx=16, pady=12, highlightthickness=3,
                        highlightbackground=COLORS["paper_edge"], cursor="hand2" if clickable else "")
        card.grid(row=(number - 1) // 2, column=(number - 1) % 2, sticky="nsew", padx=6, pady=6)

        top = tk.Frame(card, bg=COLORS["paper"])
        top.pack(fill="x")
        tag = get_text(f"หลักฐาน #{number}", f"EVIDENCE #{number}")
        tk.Label(top, text=tag, font=type_font(tag, 11), bg=COLORS["paper"],
                 fg=COLORS["danger"]).pack(side="left")
        badge = tk.Label(top, font=FONT_SMALL + ("bold",), bg=COLORS["paper"], fg=COLORS["ink"], padx=6)
        badge.pack(side="right")

        tk.Label(card, text=text_of(evd, "ชื่อ"), font=FONT_BOLD, wraplength=370, justify="left",
                 bg=COLORS["paper"], fg=COLORS["ink"]).pack(anchor="w", pady=(6, 2))
        tk.Label(card, text=text_of(evd, "รายละเอียด"), font=FONT, wraplength=370, justify="left",
                 bg=COLORS["paper"], fg=COLORS["ink_soft"]).pack(anchor="w")

        self.evidence_cards[evd["รหัส"]] = (card, badge)
        if clickable:
            bind_click(card, lambda: self.select_evidence(evd["รหัส"]))

    def suspect_card(self, parent: tk.Frame, number: int, suspect: dict, clickable: bool) -> None:
        """การ์ดโปรไฟล์ผู้ต้องสงสัยแนวนอน: รูปตัวละคร ชื่อ อาชีพ (ซ้าย) และคำให้การ (ขวา)"""
        bg = COLORS["panel_light"]
        card = tk.Frame(parent, bg=bg, padx=16, pady=12, highlightthickness=3,
                        highlightbackground=bg, cursor="hand2" if clickable else "")
        card.pack(fill="x", padx=6, pady=6)

        # ซ้าย: รูปตัวละคร + ชื่อ + อาชีพ + ป้าย "ผู้ต้องหา"
        profile = tk.Frame(card, bg=bg, width=250, height=64)
        profile.pack(side="left", fill="y")
        profile.pack_propagate(False)

        avatar = tk.Canvas(profile, width=56, height=56, bg=bg, bd=0, highlightthickness=0)
        avatar.pack(side="left", anchor="n")
        color = AVATAR_COLORS[(number - 1) % len(AVATAR_COLORS)]
        avatar.create_oval(2, 2, 54, 54, fill=color, outline=COLORS["text"], width=2)
        name, role = split_name(text_of(suspect, "ชื่อ"))
        avatar.create_text(28, 29, text=initial_of(name), fill="white", font=("TkDefaultFont", 20, "bold"))

        info = tk.Frame(profile, bg=bg)
        info.pack(side="left", anchor="n", padx=12)
        tk.Label(info, text=name, font=FONT_NAME, bg=bg, fg=COLORS["text"]).pack(anchor="w")
        tk.Label(info, text=role, font=FONT_SMALL, bg=bg, fg=COLORS["muted"]).pack(anchor="w")
        badge = tk.Label(info, font=FONT_SMALL + ("bold",), bg=bg, fg="white", padx=6)
        badge.pack(anchor="w", pady=(4, 0))

        # เส้นคั่น แล้วตามด้วยคำให้การ
        tk.Frame(card, bg=COLORS["muted"], width=1).pack(side="left", fill="y", padx=(4, 18))
        testimony = tk.Frame(card, bg=bg)
        testimony.pack(side="left", fill="both", expand=True)
        tk.Label(testimony, text=get_text("คำให้การ", "Testimony"), font=FONT_SMALL, bg=bg,
                 fg=COLORS["accent"]).pack(anchor="w")
        tk.Label(testimony, text=f"\u201c{text_of(suspect, 'คำให้การ')}\u201d", font=FONT_QUOTE,
                 wraplength=560, justify="left", bg=bg, fg=COLORS["text"]).pack(anchor="w", pady=(2, 0))

        self.suspect_cards[suspect["รหัส"]] = (card, badge)
        if clickable:
            bind_click(card, lambda: self.select_suspect(suspect["รหัส"]))

    def solution_card(self, case: dict) -> None:
        """การ์ดเฉลย (แสดงเมื่อปิดคดีแล้ว)"""
        card = tk.Frame(self.board.inner, bg=COLORS["panel"], padx=20, pady=14,
                        highlightthickness=2, highlightbackground=COLORS["success"])
        card.pack(fill="x", pady=(18, 4))
        title = get_text("เฉลย", "SOLUTION")
        tk.Label(card, text=title, font=type_font(title, 13), bg=COLORS["panel"],
                 fg=COLORS["success"]).pack(anchor="w")
        tk.Label(card, text=text_of(case, "เฉลย"), font=FONT, wraplength=820, justify="left",
                 bg=COLORS["panel"], fg=COLORS["text"]).pack(anchor="w", pady=(4, 0))

    # ---------- วาดหน้าจอ ----------

    def show_tab(self, tab: str) -> None:
        """สลับไปแท็บที่เลือก แล้ววาดข้อมูลล่าสุด"""
        self.current_tab = tab
        self.refresh_all()

    def refresh_all(self) -> None:
        """วาดทุกส่วนใหม่ (ใช้ตอนเริ่มโปรแกรม เปลี่ยนแท็บ เปลี่ยนภาษา และหลังชี้ตัว)"""
        self.subtitle_label.config(text=get_text("เกมสืบสวนคดีปริศนา", "Mystery Investigation"))
        tab_names = {
            "play": get_text("สืบสวน", "INVESTIGATE"),
            "manage": get_text("แฟ้มคดี", "CASE FILES"),
            "report": get_text("รายงาน", "REPORTS"),
        }
        for tab, button in self.tab_buttons.items():
            active = tab == self.current_tab
            normal = COLORS["panel_light"] if active else COLORS["bg"]
            button.config(text=tab_names[tab], font=type_font(tab_names[tab], 12), bg=normal,
                          fg=COLORS["accent"] if active else COLORS["muted"],
                          activebackground=COLORS["panel_light"], activeforeground=COLORS["accent"])
            add_hover(button, normal, COLORS["panel_light"])

        for tab, view in self.views.items():
            if tab == self.current_tab:
                view.pack(fill="both", expand=True)
            else:
                view.pack_forget()
        if self.current_tab != "play":
            self.status_label.config(text="")
            self.views[self.current_tab].render()
            for lang, button in self.lang_buttons.items():
                self.style_language_button(lang, button)
            return

        cases_title = get_text("แฟ้มคดี", "CASE FILES")
        self.cases_label.config(text=cases_title, font=type_font(cases_title))
        self.legend_label.config(text=get_text(
            "●  กำลังสืบสวน\n✔  ปิดคดีแล้ว\n❄  คดีค้าง",
            "●  Open\n✔  Closed\n❄  Cold case"
        ))
        self.status_label.config(text=get_text(
            "เคล็ดลับ: หลักฐานบางชิ้นเป็นหลักฐานหลอก ให้หาคำให้การที่ขัดกับหลักฐาน",
            "Tip: some evidence is a red herring. Look for a testimony that contradicts the evidence."
        ))

        for lang, button in self.lang_buttons.items():
            self.style_language_button(lang, button)

        # คดีที่เลือกไว้อาจถูกลบในแท็บแฟ้มคดี
        if self.case is not None and self.case not in cases.get_all_cases():
            self.case = None

        self.story_cases = [c for c in cases.get_all_cases() if c.get("ผู้ต้องสงสัย")]
        self.case_list.delete(0, "end")
        for index, case in enumerate(self.story_cases):
            mark, color = STATUS_STYLE.get(case["สถานะ"], ("", COLORS["text"]))
            self.case_list.insert("end", f" {mark}  {case['รหัส']}   {text_of(case, 'ชื่อ')}")
            self.case_list.itemconfig(index, fg=color)

        if self.case in self.story_cases:
            self.case_list.selection_set(self.story_cases.index(self.case))
        self.render_board()

    @staticmethod
    def style_language_button(lang: str, button: tk.Button) -> None:
        """ปุ่มภาษาที่ใช้อยู่เป็นสีทอง"""
        active = lang == get_language()
        normal = COLORS["accent"] if active else COLORS["panel"]
        button.config(bg=normal, fg=COLORS["ink"] if active else COLORS["text"],
                      activebackground=COLORS["panel_light"], activeforeground=COLORS["accent"])
        add_hover(button, normal, COLORS["panel_light"])

    def render_board(self) -> None:
        """วาดกระดานสืบสวนของคดีที่เลือก"""
        self.board.clear()
        self.suspect_cards = {}
        self.evidence_cards = {}

        if self.case is None:
            self.render_welcome()
        else:
            case = self.case
            clickable = case["สถานะ"] == "open"
            self.brief_card(case)

            case_evidence = evidence.find_evidence_by_case(case["รหัส"])
            self.section_header(get_text("หลักฐาน", "EVIDENCE"),
                                get_text(f"{len(case_evidence)} ชิ้น", f"{len(case_evidence)} items"))
            grid = tk.Frame(self.board.inner, bg=COLORS["bg"])
            grid.pack(fill="x")
            grid.columnconfigure((0, 1), weight=1, uniform="evidence")
            for number, evd in enumerate(case_evidence, start=1):
                self.evidence_card(grid, number, evd, clickable)

            suspects = case["ผู้ต้องสงสัย"]
            self.section_header(get_text("ผู้ต้องสงสัย", "SUSPECTS"),
                                get_text(f"{len(suspects)} คน", f"{len(suspects)} people"))
            for number, suspect in enumerate(suspects, start=1):
                self.suspect_card(self.board.inner, number, suspect, clickable)

            if case["สถานะ"] == "closed":
                self.solution_card(case)

        self.update_selection()

    def render_welcome(self) -> None:
        """หน้าต้อนรับเมื่อยังไม่ได้เลือกคดี"""
        card = tk.Frame(self.board.inner, bg=COLORS["paper"], padx=40, pady=36,
                        highlightthickness=1, highlightbackground=COLORS["paper_edge"])
        card.pack(fill="x", pady=(40, 0))
        tk.Label(card, text="CONFIDENTIAL", font=type_font("A", 12), bg=COLORS["paper"],
                 fg=COLORS["danger"]).pack(anchor="w")
        welcome = get_text("ยินดีต้อนรับ นักสืบ", "Welcome, Detective")
        tk.Label(card, text=welcome, font=type_font(welcome, 24), bg=COLORS["paper"],
                 fg=COLORS["ink"]).pack(anchor="w", pady=(8, 14))
        tk.Label(card, font=FONT, justify="left", bg=COLORS["paper"], fg=COLORS["ink"], text=get_text(
            "1.  เลือกแฟ้มคดีทางซ้าย\n"
            "2.  อ่านหลักฐานและคำให้การของผู้ต้องสงสัย\n"
            "3.  คลิกการ์ดผู้ต้องสงสัยที่คิดว่าโกหก\n"
            "4.  คลิกการ์ดหลักฐานที่พิสูจน์ว่าเขาโกหก\n"
            "5.  กด \"ชี้ตัวคนร้าย\"  (ผิดได้ไม่เกิน 3 ครั้ง)",
            "1.  Choose a case file on the left\n"
            "2.  Read the evidence and the suspects' testimonies\n"
            "3.  Click the suspect you think is lying\n"
            "4.  Click the evidence that proves the lie\n"
            "5.  Press \"ACCUSE\"  (at most 3 wrong accusations)"
        )).pack(anchor="w")

    def update_selection(self) -> None:
        """ระบายกรอบและป้ายของการ์ดที่ถูกเลือก แล้ววาดแถบข้อกล่าวหาใหม่"""
        for suspect_id, (card, badge) in self.suspect_cards.items():
            selected = suspect_id == self.suspect_id
            card.config(highlightbackground=COLORS["danger"] if selected else COLORS["panel_light"])
            badge.config(text=get_text("ผู้ต้องหา", "ACCUSED") if selected else "",
                         bg=COLORS["danger"] if selected else COLORS["panel_light"])

        for evidence_id, (card, badge) in self.evidence_cards.items():
            selected = evidence_id == self.evidence_id
            card.config(highlightbackground=COLORS["accent"] if selected else COLORS["paper_edge"])
            badge.config(text=get_text("หลักฐานมัด", "KEY EVIDENCE") if selected else "",
                         bg=COLORS["accent"] if selected else COLORS["paper"])

        self.render_accuse_bar()

    def render_accuse_bar(self) -> None:
        """แถบด้านล่าง: ผู้ต้องหาและหลักฐานที่เลือก โอกาสที่เหลือ และปุ่มชี้ตัว"""
        bar = self.accuse_bar
        for widget in bar.winfo_children():
            widget.destroy()
        bar.config(highlightbackground=COLORS["panel"])

        if self.case is None:
            tk.Label(bar, font=FONT, bg=COLORS["panel"], fg=COLORS["muted"], text=get_text(
                "เลือกแฟ้มคดีทางซ้ายเพื่อเริ่มการสืบสวน", "Choose a case file on the left to begin."
            )).pack(anchor="w")
            return

        # คดีที่จบแล้ว: แสดงตราประทับ
        if self.case["สถานะ"] != "open":
            closed = self.case["สถานะ"] == "closed"
            color = COLORS["success"] if closed else COLORS["cold"]
            bar.config(highlightbackground=color)
            tk.Label(bar, text="CASE CLOSED" if closed else "COLD CASE", font=type_font("A", 18),
                     bg=COLORS["panel"], fg=color, padx=10, highlightthickness=2,
                     highlightbackground=color).pack(side="left")
            tk.Label(bar, text=cases.status_text(self.case["สถานะ"]), font=FONT,
                     bg=COLORS["panel"], fg=COLORS["text"]).pack(side="left", padx=16)
            return

        # ฝั่งซ้าย: ผู้ต้องหาและหลักฐานที่เลือก
        picks = tk.Frame(bar, bg=COLORS["panel"])
        picks.pack(side="left", fill="x", expand=True)
        rows = (
            (get_text("ผู้ต้องหา", "Accused"), self.suspect_name(), COLORS["danger"],
             get_text("คลิกการ์ดผู้ต้องสงสัย", "click a suspect card")),
            (get_text("หลักฐานมัด", "Key evidence"), self.evidence_name(), COLORS["accent"],
             get_text("คลิกการ์ดหลักฐาน", "click an evidence card")),
        )
        for row, (label, value, color, hint) in enumerate(rows):
            tk.Label(picks, text=label, font=FONT_SMALL, bg=COLORS["panel"],
                     fg=COLORS["muted"]).grid(row=row, column=0, sticky="w", padx=(0, 12))
            tk.Label(picks, text=value or "—  " + hint, font=FONT_BOLD if value else FONT,
                     bg=COLORS["panel"], fg=color if value else COLORS["muted"]
                     ).grid(row=row, column=1, sticky="w")

        # ฝั่งขวา: ปุ่มชี้ตัว (กดได้เมื่อเลือกครบ) และโอกาสที่เหลือ
        ready = self.suspect_id is not None and self.evidence_id is not None
        accuse_text = get_text("ชี้ตัวคนร้าย", "ACCUSE")
        accuse = tk.Button(
            bar, text=accuse_text, font=type_font(accuse_text, 14), command=self.on_accuse,
            width=14, pady=10, relief="flat", bd=0, cursor="hand2" if ready else "",
            state="normal" if ready else "disabled",
            bg=COLORS["danger"] if ready else COLORS["disabled"], fg="white",
            disabledforeground=COLORS["muted"],
            activebackground=COLORS["danger_dark"], activeforeground="white"
        )
        accuse.pack(side="right")
        if ready:
            add_hover(accuse, COLORS["danger"], COLORS["danger_dark"])

        # โอกาสที่เหลือ: ◆ = ยังเหลือ, ◇ = ใช้ไปแล้ว
        wrong = self.case.get("ตอบผิด", 0)
        chances = tk.Frame(bar, bg=COLORS["panel"])
        chances.pack(side="right", padx=24)
        tk.Label(chances, text=get_text("โอกาส", "Chances"), font=FONT_SMALL,
                 bg=COLORS["panel"], fg=COLORS["muted"]).pack()
        tk.Label(chances, text="◆ " * (game.MAX_WRONG - wrong) + "◇ " * wrong, font=FONT_NAME,
                 bg=COLORS["panel"], fg=COLORS["danger"] if wrong else COLORS["accent"]).pack()

    def suspect_name(self) -> str:
        """ชื่อผู้ต้องสงสัยที่เลือกอยู่ หรือข้อความว่างถ้ายังไม่ได้เลือก"""
        for suspect in self.case["ผู้ต้องสงสัย"]:
            if suspect["รหัส"] == self.suspect_id:
                return text_of(suspect, "ชื่อ")
        return ""

    def evidence_name(self) -> str:
        """ชื่อหลักฐานที่เลือกอยู่ หรือข้อความว่างถ้ายังไม่ได้เลือก"""
        for evd in evidence.find_evidence_by_case(self.case["รหัส"]):
            if evd["รหัส"] == self.evidence_id:
                return text_of(evd, "ชื่อ")
        return ""

    def show_dialog(self, title: str, message: str, color: str) -> None:
        """กล่องข้อความในธีม (ดู gui_theme.show_dialog)"""
        show_dialog(self.root, title, message, color)

    # ---------- เหตุการณ์ ----------

    def change_language(self, lang: str) -> None:
        """เปลี่ยนภาษาแล้ววาดหน้าจอใหม่"""
        set_language(lang)
        self.refresh_all()

    def on_select_case(self, event) -> None:
        """ผู้เล่นคลิกเลือกคดีจากรายการ"""
        selection = self.case_list.curselection()
        if not selection:
            return
        self.case = self.story_cases[selection[0]]
        self.suspect_id = None
        self.evidence_id = None
        self.render_board()

    def select_suspect(self, suspect_id: str) -> None:
        """คลิกการ์ดผู้ต้องสงสัย (คลิกซ้ำเพื่อยกเลิก)"""
        self.suspect_id = None if self.suspect_id == suspect_id else suspect_id
        self.update_selection()

    def select_evidence(self, evidence_id: str) -> None:
        """คลิกการ์ดหลักฐาน (คลิกซ้ำเพื่อยกเลิก)"""
        self.evidence_id = None if self.evidence_id == evidence_id else evidence_id
        self.update_selection()

    def on_accuse(self) -> None:
        """ตรวจข้อกล่าวหาด้วยกฎเดียวกับเวอร์ชัน Terminal (game.check_accusation)"""
        # ต้องเลือกให้ครบทั้งผู้ต้องสงสัยและหลักฐานก่อน (ปุ่มจะกดไม่ได้อยู่แล้ว แต่กันไว้อีกชั้น)
        if self.suspect_id is None or self.evidence_id is None:
            self.show_dialog(get_text("ยังเลือกไม่ครบ", "NOT YET"), get_text(
                "กรุณาเลือกทั้งผู้ต้องสงสัยและหลักฐาน",
                "Please choose both a suspect and a piece of evidence."
            ), COLORS["accent"])
            return

        result = game.check_accusation(self.case, self.suspect_id, self.evidence_id)
        self.suspect_id = None
        self.evidence_id = None

        if result == "solved":
            self.show_dialog("CASE CLOSED", get_text("ถูกต้อง! ปิดคดีสำเร็จ\n\n", "Correct! Case closed.\n\n")
                             + text_of(self.case, "เฉลย"), COLORS["success"])
        elif result == "cold":
            self.show_dialog("COLD CASE", get_text(
                "ข้อกล่าวหาไม่มีน้ำหนักอีกแล้ว... คดีนี้กลายเป็นคดีค้าง",
                "Another weak accusation... The case has gone cold."
            ), COLORS["cold"])
        else:
            chances = game.MAX_WRONG - self.case["ตอบผิด"]
            self.show_dialog(get_text("ผิด!", "WRONG!"), get_text(
                f"ข้อกล่าวหาไม่มีน้ำหนักพอ ลองวิเคราะห์ใหม่\nเหลือโอกาส {chances} ครั้ง",
                f"The accusation doesn't hold up. Think again.\n{chances} chance(s) left."
            ), COLORS["danger"])

        self.refresh_all()


def main() -> None:
    """เริ่มเกมเวอร์ชัน GUI"""
    storage.init_storage()
    try:
        root = tk.Tk()
    except tk.TclError:
        # เช่น รันผ่าน SSH ที่ไม่มีหน้าจอ
        print("Cannot open a window here. Please run: python3 main.py")
        print("เปิดหน้าต่างไม่ได้ กรุณาใช้: python3 main.py")
        sys.exit(1)

    CaseZeroApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
