#!/usr/bin/env python3
"""
GUI - LAST SHELTER (Bonus)
หน้าต่างเกมด้วย Tkinter ใช้ข้อมูลและกฎชุดเดียวกับเวอร์ชัน Terminal (ฟังก์ชัน do_* ทั้งหมด)
Tkinter window for the game, sharing data and rules with the terminal version.

หน้าจอ:
  บน   = โลโก้ วันที่ ทรัพยากร (พร้อมคาดการณ์) ปุ่มวิธีเล่น/เกมใหม่/ภาษา
  ซ้าย = การ์ดผู้รอดชีวิต (HP พลังพิเศษ ทักษะ และปุ่มเลือกงาน)
  ขวา  = แท็บ ประตู / สร้าง / ซอมบี้ / บันทึก
  ล่าง = ข้อความล่าสุด พลังป้องกันคืนนี้ ปุ่มจัดงานอัตโนมัติ และปุ่มจบวัน

รัน: python3 gui.py
"""

import re
import sys

try:
    import tkinter as tk
except ImportError:
    print("Tkinter is not installed. Please run: python3 main.py")
    print("เครื่องนี้ไม่มี Tkinter กรุณาใช้: python3 main.py")
    sys.exit(1)

from language import get_text, get_language, set_language
from data import (RESOURCES, SKILLS, JOBS, POWERS, BUILDINGS, ZOMBIES, GOAL_DAY, MAX_CAMP, MAX_HP,
                  MIN_SCAVENGE_HP, RAID_START_DAY, tr)
import camp
import day
import menu
import powers
import storage
import survivors
from gui_theme import (COLORS, FONT, FONT_SMALL, FONT_SMALL_BOLD, FONT_BOLD, FONT_BIG, FONT_HUGE, FONT_LOGO,
                       ScrollableFrame, ask_confirm, ask_text, flat_button, label, meter, open_dialog,
                       picture, section_title, tk_safe, type_font, wait_dialog)
from sprites import sprite, ZOMBIE_SPRITES

NIGHT_LINE_DELAY = 350   # หน่วงเวลาระหว่างบรรทัดตอนเล่าเหตุการณ์กลางคืน (มิลลิวินาที)
TABS = ["gate", "build", "zombies", "log"]


def hp_color(hp: int) -> str:
    """สีของแถบ HP: เขียว / เหลือง / แดง (ต่ำกว่าเกณฑ์ออกไปทำงาน)"""
    if hp >= 70:
        return COLORS["accent"]
    if hp >= MIN_SCAVENGE_HP:
        return COLORS["amber"]
    return COLORS["red"]


def skills_text(skills: dict) -> str:
    """ทักษะแบบดาว เช่น 'หาเสบียง ★★★★☆   ต่อสู้ ★★☆☆☆   รักษา ★☆☆☆☆'"""
    return "   ".join(f"{tr(SKILLS[s])} {survivors.stars(level)}" for s, level in skills.items())


def pretty(line: str) -> str:
    """
    แปลงอีโมจิที่ Tk แสดงไม่ได้ให้เป็นชื่อ เฉพาะตำแหน่งที่เป็นตัวเลข เช่น '🧟x5' → 'ซอมบี้เดิน x5', '🥫-3' → 'อาหาร -3'
    แล้วตัดอีโมจิที่เหลือออก
    """
    for zombie in ZOMBIES:
        line = re.sub(re.escape(zombie["icon"]) + r"(?=x\d)", tr(zombie["name"]) + " ", line)
    for info in RESOURCES.values():
        line = re.sub(re.escape(info["icon"]) + r"(?=[+-]\d)", tr(info["name"]) + " ", line)
    return tk_safe(line)


def line_color(line: str) -> str:
    """สีของบรรทัดในรายงานกลางคืน (ดูจากสัญลักษณ์ก่อนแปลงข้อความ)"""
    if horde_counts(line) or "👹" in line:
        return COLORS["amber"]
    if any(mark in line for mark in ("✖", "🩸", "🦠", "🪦", "🧟", "😵", "🤒")):
        return COLORS["red"]
    if any(mark in line for mark in ("✔", "⬆", "🚁", "✚", "💉")):
        return COLORS["accent"]
    return COLORS["text"]


def horde_counts(line: str) -> list:
    """อ่านองค์ประกอบฝูงจากบรรทัดรายงาน เช่น '🧟x5 🏃x2' → [(1, 5), (2, 2)]"""
    found = []
    for zombie in ZOMBIES:
        match = re.search(re.escape(zombie["icon"]) + r"x(\d+)", line)
        if match:
            found.append((zombie["level"], int(match.group(1))))
    return found


class ShelterApp:
    """หน้าต่างหลักของเกม"""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.tab = "gate"
        self.message = (get_text("ยินดีต้อนรับสู่ศูนย์พักพิง มอบงานให้ทุกคน แล้วกดจบวัน",
                                 "Welcome to the shelter. Give everyone a job, then end the day."), COLORS["muted"])
        root.title("LAST SHELTER")
        root.geometry("1360x860")
        root.minsize(1220, 760)
        root.configure(bg=COLORS["bg"])
        self.build_layout()
        self.refresh()

    # ---------- โครงหน้าต่าง ----------

    def build_layout(self) -> None:
        """สร้างส่วนที่อยู่คงที่ของหน้าต่าง"""
        header = tk.Frame(self.root, bg=COLORS["bg"], padx=20, pady=10)
        header.pack(fill="x")
        tk.Label(header, text="LAST SHELTER", font=FONT_LOGO, bg=COLORS["bg"], fg=COLORS["accent"]).pack(side="left")

        # ปุ่มด้านขวา pack ก่อนแถบสถานะ เพื่อไม่ให้ถูกดันจนหลุดจอ
        self.lang_buttons = {}
        for lang, text in (("en", "EN"), ("th", "ไทย")):
            button = tk.Button(header, text=text, font=FONT_BOLD, width=4, relief="flat", bd=0,
                               cursor="hand2", highlightthickness=0, command=lambda l=lang: self.change_language(l))
            button.pack(side="right", padx=2)
            self.lang_buttons[lang] = button
        self.new_button = flat_button(header, "", self.new_game, COLORS["panel"], COLORS["red_dark"], size=10)
        self.new_button.pack(side="right", padx=(0, 12))
        self.help_button = flat_button(header, "", self.show_help, COLORS["panel"], COLORS["card_hover"], size=10)
        self.help_button.pack(side="right", padx=(0, 6))

        self.top_bar = tk.Frame(header, bg=COLORS["bg"])
        self.top_bar.pack(side="left", padx=18)

        tk.Frame(self.root, bg=COLORS["accent"], height=2).pack(fill="x", padx=20)

        # แถบล่าง pack ก่อนส่วนกลาง เพื่อให้อยู่บนจอเสมอ
        footer = tk.Frame(self.root, bg=COLORS["panel"], padx=20, pady=12)
        footer.pack(side="bottom", fill="x")
        self.end_button = flat_button(footer, "", self.end_day, COLORS["red"], COLORS["red_dark"], size=13, padx=22, pady=8)
        self.end_button.pack(side="right")
        self.auto_button = flat_button(footer, "", self.auto_assign, COLORS["accent"], COLORS["accent_dark"],
                                       fg=COLORS["ink"], size=12, padx=16, pady=8)
        self.auto_button.pack(side="right", padx=10)
        self.defense_label = label(footer, "", COLORS["panel"], COLORS["muted"], FONT_SMALL_BOLD, justify="right")
        self.defense_label.pack(side="right", padx=10)
        self.message_label = label(footer, "", COLORS["panel"], font=FONT_BOLD, anchor="w", justify="left", wraplength=640)
        self.message_label.pack(side="left", fill="x", expand=True)

        body = tk.Frame(self.root, bg=COLORS["bg"], padx=20, pady=12)
        body.pack(fill="both", expand=True)

        right = tk.Frame(body, bg=COLORS["panel"], width=500)
        right.pack(side="right", fill="y", padx=(14, 0))
        right.pack_propagate(False)
        self.tab_bar = tk.Frame(right, bg=COLORS["panel"])
        self.tab_bar.pack(fill="x", padx=12, pady=(12, 0))
        tk.Frame(right, bg=COLORS["line"], height=1).pack(fill="x", padx=12)
        self.tab_view = ScrollableFrame(right, COLORS["panel"])
        self.tab_view.pack(fill="both", expand=True, padx=(12, 4), pady=10)

        left = tk.Frame(body, bg=COLORS["bg"])
        left.pack(side="left", fill="both", expand=True)
        self.left_title = tk.Frame(left, bg=COLORS["bg"])
        self.left_title.pack(fill="x", pady=(0, 6))
        self.people_view = ScrollableFrame(left, COLORS["bg"])
        self.people_view.pack(fill="both", expand=True)

    def refresh(self) -> None:
        """วาดข้อมูลทั้งหมดใหม่ตามสถานะเกมปัจจุบัน"""
        self.draw_header()
        self.draw_people()
        self.draw_tabs()
        self.draw_footer()

    def say(self, text: str, color: str = None) -> None:
        """แสดงข้อความที่แถบล่าง"""
        self.message = (text, color or COLORS["text"])
        self.message_label.config(text=tk_safe(text), fg=self.message[1])

    def playing(self) -> bool:
        """เกมยังไม่จบ (ถ้าจบแล้วจะแจ้งเตือน)"""
        if storage.state["status"] == "playing":
            return True
        self.say(get_text("เกมจบแล้ว กด 'เริ่มเกมใหม่' เพื่อเล่นอีกรอบ", "The game is over. Press 'New Game' to play again."),
                 COLORS["amber"])
        return False

    # ---------- แถบบน ----------

    def draw_header(self) -> None:
        """วันที่ (แถบ 15 ช่อง) และทรัพยากรพร้อมคาดการณ์"""
        for widget in self.top_bar.winfo_children():
            widget.destroy()
        state = storage.state
        bg = COLORS["bg"]

        day_box = tk.Frame(self.top_bar, bg=bg)
        day_box.pack(side="left", padx=(0, 22))
        day_text = get_text(f"วันที่ {state['day']}/{GOAL_DAY}", f"DAY {state['day']}/{GOAL_DAY}")
        tk.Label(day_box, text=day_text, font=type_font(day_text, 13), bg=bg, fg=COLORS["text"]).pack(anchor="w")
        track = tk.Canvas(day_box, width=GOAL_DAY * 11, height=10, bg=bg, highlightthickness=0)
        track.pack(anchor="w", pady=(3, 0))
        for number in range(1, GOAL_DAY + 1):
            if number < state["day"] or state["status"] == "won":
                color = COLORS["accent_dark"]
            elif number == state["day"]:
                color = COLORS["accent"]
            else:
                color = COLORS["disabled"]
            if number == GOAL_DAY and color == COLORS["disabled"]:
                color = COLORS["red_dark"]
            x = (number - 1) * 11
            track.create_rectangle(x, 0, x + 8, 10, fill=color, width=0)

        for key in RESOURCES:
            chip = tk.Frame(self.top_bar, bg=COLORS["panel"], padx=10, pady=4)
            chip.pack(side="left", padx=4)
            picture(chip, sprite(key, 2), COLORS["panel"]).pack(side="left")
            text_box = tk.Frame(chip, bg=COLORS["panel"])
            text_box.pack(side="left", padx=(6, 0))
            label(text_box, f"{tr(RESOURCES[key]['name'])} {state['resources'][key]}", COLORS["panel"],
                  font=FONT_BOLD).pack(anchor="w")
            if key in ("food", "water"):
                days = camp.days_left(key)
                color = COLORS["red"] if days <= 1 else COLORS["amber"] if days <= 2 else COLORS["muted"]
                label(text_box, camp.days_text(key), COLORS["panel"], color, FONT_SMALL).pack(anchor="w")

        lang = get_language()
        for code, button in self.lang_buttons.items():
            active = code == lang
            button.config(bg=COLORS["accent"] if active else COLORS["panel"],
                          fg=COLORS["ink"] if active else COLORS["muted"],
                          activebackground=COLORS["accent_dark"])
        self.help_button.config(text=tk_safe(get_text("? วิธีเล่น", "? How to Play")))
        self.new_button.config(text=tk_safe(get_text("เริ่มเกมใหม่", "New Game")))

    # ---------- การ์ดผู้รอดชีวิต ----------

    def draw_people(self) -> None:
        """การ์ดผู้รอดชีวิตทุกคน (2 คอลัมน์)"""
        for widget in self.left_title.winfo_children():
            widget.destroy()
        state = storage.state
        section_title(self.left_title, get_text(f"ผู้รอดชีวิต {len(state['survivors'])}/{MAX_CAMP}",
                                                f"SURVIVORS {len(state['survivors'])}/{MAX_CAMP}"), COLORS["bg"]).pack(side="left")
        idle = sum(1 for p in state["survivors"] if p["job"] is None)
        if idle and state["status"] == "playing":
            label(self.left_title, get_text(f"ยังไม่มีงาน {idle} คน", f"{idle} without a job"), COLORS["bg"],
                  COLORS["amber"], FONT_SMALL_BOLD).pack(side="left", padx=12)

        self.people_view.clear()
        grid = self.people_view.inner
        if state["status"] != "playing":
            self.draw_ending_banner(grid)
        for column in range(2):
            grid.columnconfigure(column, weight=1, uniform="cards")
        for index, person in enumerate(state["survivors"]):
            card = self.person_card(grid, person)
            card.grid(row=index // 2 + 1, column=index % 2, sticky="nsew", padx=(0, 10), pady=(0, 10))

    def draw_ending_banner(self, parent: tk.Widget) -> None:
        """แถบผลลัพธ์ตอนจบเกม"""
        state = storage.state
        banner = tk.Frame(parent, bg=COLORS["card"], padx=16, pady=12)
        banner.grid(row=0, column=0, columnspan=2, sticky="ew", padx=(0, 10), pady=(0, 10))
        if state["status"] == "won":
            saved = len(day.rescued())
            stars, title = day.ending_grade(saved)
            label(banner, "★" * stars + "☆" * (3 - stars), COLORS["card"], COLORS["amber"], FONT_HUGE).pack(side="left")
            text = get_text(f"เฮลิคอปเตอร์มารับแล้ว! รอด {saved} คน — {title}",
                            f"Rescued! {saved} survivor(s) made it — {title}")
        else:
            text = get_text("ศูนย์พักพิงล่มสลาย... ไม่มีใครรอด", "The shelter has fallen... No one survived.")
        label(banner, text, COLORS["card"], font=FONT_BIG).pack(side="left", padx=14)
        flat_button(banner, get_text("เริ่มเกมใหม่", "New Game"), self.new_game, COLORS["accent"],
                    COLORS["accent_dark"], fg=COLORS["ink"]).pack(side="right")

    def person_card(self, parent: tk.Widget, person: dict) -> tk.Frame:
        """การ์ดของผู้รอดชีวิต 1 คน"""
        bg = COLORS["card"]
        card = tk.Frame(parent, bg=bg, padx=12, pady=10,
                        highlightthickness=2 if person["infected"] else 0, highlightbackground=COLORS["red"])
        top = tk.Frame(card, bg=bg)
        top.pack(fill="x")
        picture(top, sprite(person["power"], 4), bg).pack(side="left", anchor="n")

        info = tk.Frame(top, bg=bg)
        info.pack(side="left", fill="x", expand=True, padx=(12, 0))
        name_row = tk.Frame(info, bg=bg)
        name_row.pack(fill="x")
        label(name_row, person["name"], bg, font=FONT_BIG).pack(side="left")
        flat_button(name_row, "✖", lambda: self.exile(person), bg, COLORS["red_dark"], fg=COLORS["muted"],
                    size=9, padx=6, pady=1).pack(side="right")
        flat_button(name_row, "✎", lambda: self.rename(person), bg, COLORS["card_hover"], fg=COLORS["muted"],
                    size=9, padx=6, pady=1).pack(side="right")

        hp_row = tk.Frame(info, bg=bg)
        hp_row.pack(fill="x", pady=(4, 0))
        label(hp_row, f"HP {person['hp']}/{MAX_HP}", bg, COLORS["muted"], FONT_SMALL_BOLD, width=10, anchor="w").pack(side="left")
        meter(hp_row, person["hp"] / MAX_HP, hp_color(person["hp"])).pack(side="left", fill="x", expand=True)

        power = POWERS[person["power"]]
        xp_row = tk.Frame(info, bg=bg)
        xp_row.pack(fill="x", pady=(4, 0))
        label(xp_row, powers.power_label(person), bg, COLORS["purple"], FONT_SMALL_BOLD).pack(side="left")
        if person["level"] < 5:
            ratio = person["xp"] / powers.xp_needed(person["level"])
            meter(xp_row, ratio, COLORS["purple"], height=5).pack(side="left", fill="x", expand=True, padx=(8, 0))
        else:
            label(xp_row, "MAX", bg, COLORS["amber"], FONT_SMALL_BOLD).pack(side="left", padx=8)
        label(info, tr(power["about"]), bg, COLORS["muted"], FONT_SMALL, anchor="w").pack(fill="x")

        label(card, skills_text(person["skills"]), bg, COLORS["text"], FONT_SMALL, anchor="w").pack(fill="x", pady=(8, 0))

        if person["infected"]:
            warn = tk.Frame(card, bg=COLORS["red_dark"], padx=8, pady=3)
            warn.pack(fill="x", pady=(6, 0))
            label(warn, survivors.infection_text(person) + get_text("  ต้องได้ยา!", "  Needs medicine!"),
                  COLORS["red_dark"], "white", FONT_SMALL_BOLD).pack(anchor="w")

        jobs = tk.Frame(card, bg=bg)
        jobs.pack(fill="x", pady=(8, 0))
        if person["job"] == "inspect":
            label(jobs, get_text("กำลังตรวจคนแปลกหน้าที่ประตู (ทั้งวัน)", "Inspecting the newcomer (all day)"),
                  bg, COLORS["blue"], FONT_SMALL_BOLD).pack(anchor="w")
            return card

        best = survivors.recommend_job(person) if storage.state["status"] == "playing" else None
        for column, job in enumerate(survivors.assignable_jobs()):
            jobs.columnconfigure(column, weight=1, uniform="jobs")
            chosen = person["job"] == job
            allowed = not survivors.check_job(person, job)
            if chosen:
                color, fg = COLORS["accent"], COLORS["ink"]
            elif allowed:
                color, fg = COLORS["card_hover"], COLORS["amber"] if job == best else COLORS["text"]
            else:
                color, fg = COLORS["disabled"], COLORS["muted"]
            text = tr(JOBS[job]["name"]) + (" ★" if job == best and not chosen else "")
            button = flat_button(jobs, text, lambda j=job: self.assign(person, j), color,
                                 COLORS["accent_dark"] if allowed else COLORS["disabled"], fg=fg, size=9, padx=4, pady=4)
            button.grid(row=0, column=column, sticky="ew", padx=1)
        return card

    # ---------- แท็บด้านขวา ----------

    def draw_tabs(self) -> None:
        """ปุ่มแท็บและเนื้อหาของแท็บที่เลือก"""
        for widget in self.tab_bar.winfo_children():
            widget.destroy()
        names = {"gate": get_text("ประตู", "Gate"), "build": get_text("สร้าง", "Build"),
                 "zombies": get_text("ซอมบี้", "Zombies"), "log": get_text("บันทึก", "Log")}
        for key in TABS:
            text = names[key] + (" •" if key == "gate" and storage.state["wanderer"] else "")
            active = key == self.tab
            button = flat_button(self.tab_bar, text, lambda k=key: self.switch_tab(k),
                                 COLORS["accent"] if active else COLORS["panel"],
                                 COLORS["accent_dark"] if active else COLORS["card_hover"],
                                 fg=COLORS["ink"] if active else COLORS["text"], size=11, padx=14)
            button.pack(side="left", padx=(0, 2))

        self.tab_view.clear()
        self.tab_view.canvas.yview_moveto(0)
        {"gate": self.draw_gate, "build": self.draw_build,
         "zombies": self.draw_zombies, "log": self.draw_log}[self.tab](self.tab_view.inner)

    def switch_tab(self, key: str) -> None:
        self.tab = key
        self.draw_tabs()

    def draw_gate(self, parent: tk.Widget) -> None:
        """แท็บประตู: คนแปลกหน้าที่มาขอเข้าศูนย์"""
        bg = COLORS["panel"]
        state = storage.state
        wanderer = state["wanderer"]
        section_title(parent, get_text("ประตูศูนย์พักพิง", "SHELTER GATE"), bg).pack(anchor="w")
        if wanderer is None:
            picture(parent, sprite("stranger", 6, shadow=True), bg).pack(pady=(30, 10))
            label(parent, get_text("ไม่มีใครอยู่ที่ประตูวันนี้", "No one is at the gate today."), bg, COLORS["muted"],
                  FONT_BOLD).pack()
            label(parent, get_text("บางเช้าจะมีคนมาขอเข้าศูนย์ (สูงสุด 6 คน)", "Some mornings a stranger asks to join (max 6)."),
                  bg, COLORS["muted"], FONT_SMALL).pack(pady=(4, 0))
            return

        card = tk.Frame(parent, bg=COLORS["card"], padx=14, pady=12)
        card.pack(fill="x", pady=(10, 0))
        top = tk.Frame(card, bg=COLORS["card"])
        top.pack(fill="x")
        picture(top, sprite("stranger", 5), COLORS["card"]).pack(side="left")
        info = tk.Frame(top, bg=COLORS["card"])
        info.pack(side="left", padx=14, fill="x", expand=True)
        label(info, wanderer["name"], COLORS["card"], font=FONT_BIG).pack(anchor="w")
        label(info, f"HP {wanderer['hp']}/{MAX_HP}", COLORS["card"], COLORS["muted"], FONT_SMALL_BOLD).pack(anchor="w")
        power = POWERS[wanderer["power"]]
        label(info, f"{tr(power['name'])} Lv.{wanderer['level']}", COLORS["card"], COLORS["purple"], FONT_BOLD).pack(anchor="w", pady=(4, 0))
        label(info, tr(power["about"]), COLORS["card"], COLORS["muted"], FONT_SMALL, wraplength=300,
              justify="left").pack(anchor="w")
        label(card, skills_text(wanderer["skills"]), COLORS["card"], font=FONT_SMALL).pack(anchor="w", pady=(10, 0))

        if wanderer["checked"] and wanderer["infected"]:
            result, color = get_text("ผลตรวจ: พบรอยกัด! ติดเชื้อ", "Inspection: BITE FOUND! Infected"), COLORS["red"]
        elif wanderer["checked"]:
            result, color = get_text("ผลตรวจ: ไม่พบรอยกัด ปลอดภัย", "Inspection: no bites, safe"), COLORS["accent"]
        else:
            result, color = get_text("ยังไม่ได้ตรวจร่างกาย อาจติดเชื้อมาแล้ว!", "Not inspected — could be infected!"), COLORS["amber"]
        box = tk.Frame(card, bg=color, padx=8, pady=4)
        box.pack(fill="x", pady=(10, 0))
        label(box, result, color, COLORS["ink"], FONT_SMALL_BOLD).pack(anchor="w")

        label(parent, get_text(f"รับเข้ามาต้องเลี้ยงเพิ่ม: อาหาร +1 และน้ำ +1 ต่อวัน   (ศูนย์ {len(state['survivors'])}/{MAX_CAMP})",
                               f"One more mouth: +1 food and +1 water per day   (shelter {len(state['survivors'])}/{MAX_CAMP})"),
              bg, COLORS["muted"], FONT_SMALL, wraplength=440, justify="left").pack(anchor="w", pady=(10, 6))

        row = tk.Frame(parent, bg=bg)
        row.pack(fill="x")
        flat_button(row, get_text("รับเข้าศูนย์", "Let in"), self.accept, COLORS["accent"], COLORS["accent_dark"],
                    fg=COLORS["ink"]).pack(side="left", padx=(0, 6))
        flat_button(row, get_text("ไม่รับ", "Turn away"), self.reject, COLORS["red"], COLORS["red_dark"]).pack(side="left", padx=(0, 6))
        if not wanderer["checked"]:
            flat_button(row, get_text("ตรวจร่างกายก่อน", "Inspect first"), self.inspect, COLORS["blue"], "#3d86c0").pack(side="left")
            label(parent, get_text("ตรวจร่างกาย = ใช้คนว่าง 1 คนทั้งวัน", "Inspecting uses one free survivor for the day"),
                  bg, COLORS["muted"], FONT_SMALL).pack(anchor="w", pady=(6, 0))

    def draw_build(self, parent: tk.Widget) -> None:
        """แท็บสร้างสิ่งก่อสร้าง"""
        bg = COLORS["panel"]
        section_title(parent, get_text("สร้างสิ่งก่อสร้าง", "BUILD"), bg).pack(anchor="w")
        discount = powers.build_discount()
        if discount:
            label(parent, get_text(f"ช่างซ่อม Lv.{discount} ช่วยลดค่าเศษวัสดุ -{discount}",
                                   f"Mechanic Lv.{discount} saves -{discount} scrap"), bg, COLORS["purple"],
                  FONT_SMALL_BOLD).pack(anchor="w")
        for key, info in BUILDINGS.items():
            built = key in storage.state["buildings"]
            card = tk.Frame(parent, bg=COLORS["card"], padx=12, pady=10)
            card.pack(fill="x", pady=(10, 0))
            picture(card, sprite(key, 3, shadow=False), COLORS["card"]).pack(side="left")
            text_box = tk.Frame(card, bg=COLORS["card"])
            text_box.pack(side="left", fill="x", expand=True, padx=12)
            label(text_box, tr(info["name"]), COLORS["card"], font=FONT_BOLD).pack(anchor="w")
            label(text_box, tr(info["about"]), COLORS["card"], COLORS["accent"], FONT_SMALL).pack(anchor="w")
            cost = camp.build_cost(key)
            cost_text = "  +  ".join(f"{tr(RESOURCES[k]['name'])} {v}" for k, v in cost.items())
            enough = not storage.check_resources(cost)
            label(text_box, cost_text, COLORS["card"], COLORS["muted"] if enough or built else COLORS["red"],
                  FONT_SMALL_BOLD).pack(anchor="w")
            if built:
                label(card, get_text("สร้างแล้ว ✔", "Built ✔"), COLORS["card"], COLORS["accent"], FONT_SMALL_BOLD).pack(side="right")
            else:
                flat_button(card, get_text("สร้าง", "Build"), lambda k=key: self.build(k),
                            COLORS["accent"] if enough else COLORS["disabled"],
                            COLORS["accent_dark"] if enough else COLORS["disabled"],
                            fg=COLORS["ink"] if enough else COLORS["muted"], size=10).pack(side="right")

    def draw_zombies(self, parent: tk.Widget) -> None:
        """แท็บซอมบี้: ภัยคุกคามทั้ง 5 เลเวล (ตัวที่ยังไม่โผล่เป็นเงาดำ)"""
        bg = COLORS["panel"]
        today = storage.state["day"]
        section_title(parent, get_text("ภัยคุกคาม", "THREATS"), bg).pack(anchor="w")
        if today < RAID_START_DAY:
            note = get_text(f"ซอมบี้จะเริ่มบุกตั้งแต่วันที่ {RAID_START_DAY}", f"Raids begin on day {RAID_START_DAY}")
        else:
            note = get_text("ทุกคืนมีโอกาสถูกบุก ฝูงใหญ่ขึ้นทุกวัน และคืนสุดท้ายบุกแน่นอน",
                            "Raids can come any night, hordes grow daily, and the last night is certain")
        label(parent, note, bg, COLORS["muted"], FONT_SMALL, wraplength=440, justify="left").pack(anchor="w")
        label(parent, get_text(f"พลังป้องกันคืนนี้: {day.defense()}  (เฝ้ายาม + แนวกั้น)",
                               f"Defense tonight: {day.defense()}  (guards + barricade)"), bg, COLORS["accent"],
              FONT_BOLD).pack(anchor="w", pady=(4, 0))

        for zombie in ZOMBIES:
            seen = zombie["from_day"] <= today
            card = tk.Frame(parent, bg=COLORS["card"], padx=12, pady=8)
            card.pack(fill="x", pady=(10, 0))
            picture(card, sprite(ZOMBIE_SPRITES[zombie["level"] - 1], 3, shadow=not seen), COLORS["card"]).pack(side="left")
            text_box = tk.Frame(card, bg=COLORS["card"])
            text_box.pack(side="left", fill="x", expand=True, padx=12)
            name = f"Lv.{zombie['level']}  " + (tr(zombie["name"]) if seen else "???")
            label(text_box, name, COLORS["card"], COLORS["text"] if seen else COLORS["muted"], FONT_BOLD).pack(anchor="w")
            label(text_box, get_text(f"พลังโจมตี {zombie['power']}  ·  เริ่มโผล่วันที่ {zombie['from_day']}",
                                     f"Power {zombie['power']}  ·  appears from day {zombie['from_day']}"),
                  COLORS["card"], COLORS["muted"], FONT_SMALL).pack(anchor="w")
            label(text_box, tr(zombie["about"]), COLORS["card"], COLORS["amber"] if seen else COLORS["muted"],
                  FONT_SMALL).pack(anchor="w")

    def draw_log(self, parent: tk.Widget) -> None:
        """แท็บบันทึก: สถิติ กราฟอาหาร/น้ำรายวัน และผลเกมที่ผ่านมา"""
        bg = COLORS["panel"]
        state = storage.state
        log = state["log"]
        stats = day.camp_stats()
        section_title(parent, get_text("บันทึกศูนย์พักพิง", "SHELTER LOG"), bg).pack(anchor="w")
        rows = [
            (get_text("ซอมบี้บุก / ต้านได้", "Raids / repelled"), f"{log['raids']} / {log['repelled']}  ({stats['defense_rate']:.0f}%)"),
            (get_text("ติดเชื้อ / รักษาหาย", "Infected / cured"), f"{log['infected']} / {log['cured']}  ({stats['cure_rate']:.0f}%)"),
            (get_text("กลายเป็นซอมบี้ / เสียชีวิต", "Turned / died"), f"{log['turned']} / {log['deaths']}"),
            (get_text("คนเข้าร่วมใหม่", "Joined"), str(log["joined"])),
            (get_text("หาเสบียงได้ทั้งหมด", "Total gathered"), str(stats["gathered"])),
            (get_text("ฝูงใหญ่ที่สุด (พลัง)", "Biggest horde (power)"), str(log["biggest_horde"])),
            (get_text("เลเวลอัปทั้งหมด", "Level-ups"), str(log["level_ups"])),
        ]
        if stats["top_level"]:
            top = stats["top_level"]
            rows.append((get_text("พลังสูงสุด", "Top power"), f"{top['name']}  {tk_safe(powers.power_label(top))}"))
        table = tk.Frame(parent, bg=bg)
        table.pack(fill="x", pady=(6, 0))
        for index, (name, value) in enumerate(rows):
            label(table, name, bg, COLORS["muted"], FONT_SMALL).grid(row=index, column=0, sticky="w", pady=1)
            label(table, value, bg, COLORS["text"], FONT_SMALL_BOLD).grid(row=index, column=1, sticky="w", padx=14)

        section_title(parent, get_text("อาหาร / น้ำ ตอนจบแต่ละวัน", "FOOD / WATER AT DAY END"), bg, 11).pack(anchor="w", pady=(14, 4))
        self.draw_chart(parent, log["days"])

        history = storage.load_history()
        section_title(parent, get_text("ผลเกมที่ผ่านมา", "PAST RESULTS"), bg, 11).pack(anchor="w", pady=(14, 4))
        if not history:
            label(parent, get_text("ยังไม่มีเกมที่เล่นจบ", "No finished games yet."), bg, COLORS["muted"], FONT_SMALL).pack(anchor="w")
            return
        summary = menu.history_summary(history)
        best = summary["best"]
        label(parent, get_text(f"เล่นจบ {summary['games']} เกม  ·  รอด {summary['wins']} เกม  ·  เฉลี่ยรอด {summary['average']:.1f} คน",
                               f"{summary['games']} finished  ·  {summary['wins']} rescued  ·  avg {summary['average']:.1f} saved"),
              bg, COLORS["text"], FONT_SMALL_BOLD).pack(anchor="w")
        label(parent, get_text(f"ดีที่สุด: เกมที่ {best['game']}  {'★' * best['stars'] or '-'}  รอด {best['rescued']} คน",
                               f"Best: game {best['game']}  {'★' * best['stars'] or '-'}  {best['rescued']} rescued"),
              bg, COLORS["amber"], FONT_SMALL_BOLD).pack(anchor="w")
        for game in reversed(history[-6:]):
            if game["status"] == "won":
                text = get_text(f"เกมที่ {game['game']}:  {'★' * game['stars'] or '-'}  รอด {game['rescued']} คน",
                                f"Game {game['game']}:  {'★' * game['stars'] or '-'}  {game['rescued']} rescued")
            else:
                text = get_text(f"เกมที่ {game['game']}:  ล่มสลายวันที่ {game['day']}", f"Game {game['game']}:  fell on day {game['day']}")
            label(parent, text, bg, COLORS["muted"], FONT_SMALL).pack(anchor="w")

    def draw_chart(self, parent: tk.Widget, days: list) -> None:
        """กราฟเส้นอาหาร (เขียว) และน้ำ (ฟ้า) ตอนจบแต่ละวัน"""
        width, height, pad = 440, 140, 24
        canvas = tk.Canvas(parent, width=width, height=height, bg=COLORS["card"], highlightthickness=0)
        canvas.pack(anchor="w")
        if len(days) < 2:
            canvas.create_text(width // 2, height // 2, fill=COLORS["muted"], font=FONT_SMALL,
                               text=tk_safe(get_text("กราฟจะแสดงหลังผ่านไป 2 วัน", "The chart appears after 2 days")))
            return
        top = max(max(d["food"], d["water"]) for d in days) or 1
        step = (width - pad * 2) / (GOAL_DAY - 1)
        for key, color in (("food", COLORS["accent"]), ("water", COLORS["blue"])):
            points = []
            for index, entry in enumerate(days):
                points += [pad + index * step, height - pad - entry[key] / top * (height - pad * 2)]
            canvas.create_line(*points, fill=color, width=2)
        canvas.create_text(pad, 10, anchor="w", fill=COLORS["accent"], font=FONT_SMALL_BOLD,
                           text=tk_safe(tr(RESOURCES["food"]["name"])))
        canvas.create_text(pad + 70, 10, anchor="w", fill=COLORS["blue"], font=FONT_SMALL_BOLD,
                           text=tk_safe(tr(RESOURCES["water"]["name"])))
        canvas.create_text(pad, height - 8, anchor="w", fill=COLORS["muted"], font=FONT_SMALL, text="1")
        canvas.create_text(width - pad, height - 8, anchor="e", fill=COLORS["muted"], font=FONT_SMALL, text=str(GOAL_DAY))

    # ---------- แถบล่าง ----------

    def draw_footer(self) -> None:
        """ข้อความล่าสุด พลังป้องกัน และปุ่มหลัก"""
        self.message_label.config(text=tk_safe(self.message[0]), fg=self.message[1])
        playing = storage.state["status"] == "playing"
        guards = sum(1 for p in storage.state["survivors"] if p["job"] == "guard")
        self.defense_label.config(text=tk_safe(get_text(f"พลังป้องกันคืนนี้ {day.defense()}\nคนเฝ้ายาม {guards} คน",
                                                        f"Defense tonight {day.defense()}\n{guards} guard(s)")))
        self.auto_button.config(text=tk_safe(get_text("จัดงานอัตโนมัติ", "Auto-assign")))
        if playing:
            self.end_button.config(text=tk_safe(get_text(f"จบวันที่ {storage.state['day']}  ▶", f"End Day {storage.state['day']}  ▶")))
        else:
            self.end_button.config(text=tk_safe(get_text("เริ่มเกมใหม่  ▶", "New Game  ▶")))

    # ---------- การกระทำ (เรียกฟังก์ชันกลาง do_* ชุดเดียวกับ Terminal) ----------

    def assign(self, person: dict, job: str) -> None:
        if not self.playing():
            return
        error = survivors.do_assign(person, job)
        if error:
            self.say(error, COLORS["red"])
        else:
            self.say(f"{person['name']}: {tr(JOBS[job]['name'])}", COLORS["accent"])
        self.refresh()

    def auto_assign(self) -> None:
        if not self.playing():
            return
        plan = survivors.do_auto_assign()
        self.say(get_text("จัดงานแล้ว: ", "Assigned: ") + ",  ".join(f"{p['name']} → {tr(JOBS[j]['name'])}" for p, j in plan),
                 COLORS["accent"])
        self.refresh()

    def build(self, key: str) -> None:
        if not self.playing():
            return
        error = camp.do_build(key)
        if error:
            self.say(error, COLORS["red"])
        else:
            name = tr(BUILDINGS[key]["name"])
            self.say(get_text(f"สร้าง{name}เสร็จแล้ว! ({tr(BUILDINGS[key]['about'])})",
                              f"{name} built! ({tr(BUILDINGS[key]['about'])})"), COLORS["accent"])
        self.refresh()

    def accept(self) -> None:
        if not self.playing():
            return
        wanderer = storage.state["wanderer"]
        name, infected = wanderer["name"], wanderer["infected"]
        error = survivors.do_accept_wanderer()
        if error:
            self.say(error, COLORS["red"])
        elif infected:
            self.say(get_text(f"{name} เข้ามาแล้ว... แต่มีรอยกัดที่แขน! ต้องได้ยาวันนี้ ไม่งั้นจะกลายร่างคืนนี้!",
                              f"{name} is in... but there's a bite! Medicine today or they turn tonight!"), COLORS["red"])
        else:
            self.say(get_text(f"{name} เข้าร่วมศูนย์พักพิงแล้ว!", f"{name} joined the shelter!"), COLORS["accent"])
        self.refresh()

    def reject(self) -> None:
        if not self.playing():
            return
        survivors.do_reject_wanderer()
        self.say(get_text("คุณปิดประตู... เขาเดินจากไป", "You close the gate... they walk away."), COLORS["muted"])
        self.refresh()

    def inspect(self) -> None:
        """เลือกคนว่าง 1 คนไปตรวจร่างกายคนแปลกหน้า"""
        if not self.playing():
            return
        free = [p for p in storage.state["survivors"] if p["job"] is None]
        if not free:
            self.say(get_text("ไม่มีใครว่างวันนี้ ทุกคนมีงานแล้ว",
                              "No one is free today. Everyone already has a job."), COLORS["red"])
            return
        chosen = {"person": None}
        dialog = open_dialog(self.root, get_text("ใครจะไปตรวจ?", "Who inspects?"), COLORS["blue"])

        def pick(person: dict) -> None:
            chosen["person"] = person
            dialog.destroy()

        for person in free:
            row = flat_button(dialog, f"{person['name']}   HP {person['hp']}", lambda p=person: pick(p), size=11)
            row.pack(fill="x", padx=28, pady=3)
        cancel = flat_button(dialog, get_text("ยกเลิก", "Cancel"), dialog.destroy, COLORS["panel"])
        cancel.pack(pady=(10, 18))
        wait_dialog(self.root, dialog, cancel)

        person = chosen["person"]
        if person is None:
            return
        error = survivors.do_inspect(person)
        wanderer = storage.state["wanderer"]
        if error:
            self.say(error, COLORS["red"])
        elif wanderer["infected"]:
            self.say(get_text(f"{person['name']} ตรวจ {wanderer['name']}: พบรอยกัด! ติดเชื้อ",
                              f"{person['name']} inspects {wanderer['name']}: BITE FOUND!"), COLORS["red"])
        else:
            self.say(get_text(f"{person['name']} ตรวจ {wanderer['name']}: ไม่พบรอยกัด ปลอดภัย",
                              f"{person['name']} inspects {wanderer['name']}: no bites, safe"), COLORS["accent"])
        self.refresh()

    def rename(self, person: dict) -> None:
        old = person["name"]
        name = ask_text(self.root, get_text("เปลี่ยนชื่อ", "Rename"), get_text("ชื่อใหม่", "New name"), old,
                        lambda text: survivors.validate_name(text, person))
        if name is None:
            return
        error = survivors.do_rename(person, name)
        self.say(error or get_text(f"{old} เปลี่ยนชื่อเป็น {name}", f"{old} is now {name}"),
                 COLORS["red"] if error else COLORS["accent"])
        self.refresh()

    def exile(self, person: dict) -> None:
        if not self.playing():
            return
        if not ask_confirm(self.root, get_text("ไล่ออกจากศูนย์", "Exile"),
                           get_text(f"ไล่ {person['name']} ออกไปในเมืองร้าง? เขาจะไม่กลับมาอีก",
                                    f"Send {person['name']} out into the dead city? They won't come back.")):
            return
        error = survivors.do_exile(person)
        self.say(error or get_text(f"{person['name']} เดินจากไปในเมืองร้าง...", f"{person['name']} walks off into the dead city..."),
                 COLORS["red"] if error else COLORS["muted"])
        self.refresh()

    def end_day(self) -> None:
        """จบวัน แล้วเล่าเหตุการณ์กลางคืนทีละบรรทัด"""
        state = storage.state
        if state["status"] != "playing":
            self.new_game()
            return
        idle = [p["name"] for p in state["survivors"] if p["job"] is None]
        if idle and not ask_confirm(self.root, get_text("ยังมีคนไม่มีงาน", "Idle survivors"),
                                    get_text(f"{', '.join(idle)} ยังไม่มีงาน จบวันเลย?",
                                             f"{', '.join(idle)} have no job. End the day anyway?")):
            return
        night = state["day"]
        result = day.do_end_day()
        self.show_night(night, result)
        if storage.state["status"] == "playing":
            self.say(get_text(f"เช้าวันที่ {storage.state['day']} มอบงานให้ทุกคนอีกครั้ง",
                              f"Morning of day {storage.state['day']}. Give everyone a job again."), COLORS["muted"])
        self.refresh()

    def show_night(self, night: int, result: dict) -> None:
        """หน้าต่างรายงานกลางคืน: ค่อยๆ แสดงทีละบรรทัด พร้อมภาพฝูงซอมบี้ตอนบุก"""
        dialog = open_dialog(self.root, get_text(f"คืนที่ {night}", f"NIGHT {night}"), COLORS["amber"])
        body = tk.Frame(dialog, bg=COLORS["panel"], padx=28)
        body.pack(fill="both")
        footer = tk.Frame(dialog, bg=COLORS["panel"])
        footer.pack(pady=(14, 18))
        lines = list(result["lines"])

        def show_next(index: int = 0) -> None:
            if not dialog.winfo_exists():
                return
            if index >= len(lines):
                finish()
                return
            line = lines[index]
            horde = horde_counts(line)
            if horde:
                row = tk.Frame(body, bg=COLORS["panel"])
                row.pack(anchor="w", pady=(6, 2))
                for level, count in horde:
                    picture(row, sprite(ZOMBIE_SPRITES[level - 1], 3), COLORS["panel"]).pack(side="left")
                    label(row, f"x{count}", COLORS["panel"], COLORS["amber"], FONT_BOLD).pack(side="left", padx=(2, 12))
            label(body, pretty(line), COLORS["panel"], line_color(line), FONT, wraplength=620,
                  justify="left", anchor="w").pack(anchor="w", pady=1)
            dialog.after(NIGHT_LINE_DELAY, show_next, index + 1)

        def finish() -> None:
            state = storage.state
            if result["status"] == "won":
                saved = len(day.rescued())
                stars, title = day.ending_grade(saved)
                label(body, get_text(f"เสียงใบพัดเฮลิคอปเตอร์! พาผู้รอดชีวิตออกไปได้ {saved} คน",
                                     f"Rotor blades overhead! {saved} survivor(s) rescued"), COLORS["panel"],
                      COLORS["accent"], FONT_BIG).pack(anchor="w", pady=(14, 0))
                left = len(state["survivors"]) - saved
                if left:
                    label(body, get_text(f"(คนติดเชื้อ {left} คนไม่ได้รับอนุญาตให้ขึ้นเครื่อง...)",
                                         f"({left} infected survivor(s) were not allowed on board...)"),
                          COLORS["panel"], COLORS["red"], FONT_SMALL).pack(anchor="w")
                label(body, "★" * stars + "☆" * (3 - stars), COLORS["panel"], COLORS["amber"], FONT_HUGE).pack(pady=(8, 0))
                label(body, title, COLORS["panel"], font=FONT_BIG).pack()
            elif result["status"] == "lost":
                label(body, get_text("ศูนย์พักพิงเงียบงัน... ไม่มีใครรอดชีวิต", "The shelter falls silent... No one survived."),
                      COLORS["panel"], COLORS["red"], FONT_BIG).pack(anchor="w", pady=(14, 0))
            else:
                label(body, get_text(f"เช้าวันที่ {state['day']}/{GOAL_DAY}", f"Morning of day {state['day']}/{GOAL_DAY}"),
                      COLORS["panel"], COLORS["accent"], FONT_BOLD).pack(anchor="w", pady=(12, 0))
                if state["wanderer"]:
                    label(body, get_text(f"มีคนมาขอเข้าศูนย์ที่ประตู: {state['wanderer']['name']}",
                                         f"Someone is at the gate: {state['wanderer']['name']}"),
                          COLORS["panel"], COLORS["blue"], FONT_SMALL_BOLD).pack(anchor="w")
            flat_button(footer, get_text("ตกลง", "OK"), dialog.destroy, COLORS["accent"], COLORS["accent_dark"],
                        fg=COLORS["ink"], padx=30).pack()
            dialog.bind("<Return>", lambda event: dialog.destroy())

        dialog.minsize(680, 0)
        dialog.after(250, show_next)
        wait_dialog(self.root, dialog, footer)

    def new_game(self) -> None:
        state = storage.state
        if state["status"] == "playing" and state["day"] > 1 and \
                not ask_confirm(self.root, get_text("เริ่มเกมใหม่", "New Game"),
                                get_text(f"มีเกมค้างอยู่ (วันที่ {state['day']}) เริ่มใหม่เลย? ความคืบหน้าเดิมจะหาย",
                                         f"You're on day {state['day']}. Start over? Progress will be lost.")):
            return
        storage.new_game()
        self.tab = "gate"
        self.say(get_text("เริ่มเกมใหม่แล้ว ขอให้รอด!", "A fresh start. Stay alive!"), COLORS["accent"])
        self.refresh()

    def show_help(self) -> None:
        """หน้าต่างวิธีเล่น (ข้อความเดียวกับ Terminal)"""
        dialog = open_dialog(self.root, get_text("วิธีเล่น", "HOW TO PLAY"), COLORS["accent"])
        text = "\n".join(tk_safe(line) if line.strip() else "" for line in menu.how_to_play_text().split("\n"))
        tk.Label(dialog, text=text, font=FONT, justify="left", bg=COLORS["panel"], fg=COLORS["text"],
                 padx=28).pack(anchor="w")
        close = flat_button(dialog, get_text("เข้าใจแล้ว", "Got it"), dialog.destroy, COLORS["accent"],
                            COLORS["accent_dark"], fg=COLORS["ink"], padx=24)
        close.pack(pady=(14, 18))
        wait_dialog(self.root, dialog, close)

    def change_language(self, lang: str) -> None:
        set_language(lang)
        self.message = ("", COLORS["muted"])
        self.refresh()


def main() -> None:
    """เปิดหน้าต่างเกม (โหลดเซฟเดียวกับเวอร์ชัน Terminal)"""
    storage.load_game()
    root = tk.Tk()
    ShelterApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (storage.save_game(), root.destroy()))
    root.mainloop()


if __name__ == "__main__":
    main()
