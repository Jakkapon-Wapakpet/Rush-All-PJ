#!/usr/bin/env python3
"""
GUI - GHOST REALM (หลุดมิติผี) (Bonus)
หน้าต่างเกมด้วย Tkinter ใช้ข้อมูลและกฎชุดเดียวกับเวอร์ชัน Terminal (ฟังก์ชัน do_* ทั้งหมด)
Tkinter window for the game, sharing data and rules with the terminal version.

หน้าจอ:
  บน   = โลโก้ วันที่ ทรัพยากร (พร้อมคาดการณ์) ปุ่มวิธีเล่น/เกมใหม่/ภาษา
  ซ้าย = การ์ดผู้รอดชีวิต (HP พลังพิเศษ ทักษะ และปุ่มเลือกงาน)
  ขวา  = แท็บ ประตู / สร้าง / ผี / บันทึก
  ล่าง = ข้อความล่าสุด พลังป้องกันคืนนี้ ปุ่มจัดงานอัตโนมัติ และปุ่มจบวัน

รัน: python3 gui.py
"""

import math
import random
import re
import sys

try:
    import tkinter as tk
except ImportError:
    print("Tkinter is not installed. Please run: python3 main.py")
    print("เครื่องนี้ไม่มี Tkinter กรุณาใช้: python3 main.py")
    sys.exit(1)

from language import get_text, get_language, set_language
from data import (RESOURCES, SKILLS, JOBS, BUILDINGS, ZOMBIES, MAX_CAMP, MAX_HP,
                  MIN_SCAVENGE_HP, RAID_START_DAY, STORY, DIFFICULTIES, LOCATIONS, COUNTERS, LIGHTS, VOWS, VOW_DAYS,
                  MERIT_COST, MAX_GRUDGE, TICKET_PIECES, tr)
import camp
import day
import menu
import realm
import storage
import survivors
from gui_theme import (COLORS, FONT, FONT_SMALL, FONT_SMALL_BOLD, FONT_BOLD, FONT_BIG, FONT_HUGE,
                       ScrollableFrame, add_hover, ask_confirm, ask_text, flat_button, label, meter, open_dialog, set_button_text,
                       picture, section_title, tk_safe, type_font, wait_dialog)
from sprites import sprite, ZOMBIE_SPRITES

NIGHT_LINE_DELAY = 350   # หน่วงเวลาระหว่างบรรทัดตอนเล่าเหตุการณ์กลางคืน (มิลลิวินาที)
ANIM_MS = 60             # ความถี่ของแอนิเมชัน (ผีลอย หมอก เทียนกะพริบ) มิลลิวินาทีต่อเฟรม
TYPE_MS = 40             # หน่วงเวลาต่อตัวอักษรในหน้าเปิดเรื่อง
SCENE_HEIGHT = 170       # ความสูงของฉากศาลาเหนือการ์ดผู้รอดชีวิต
TABS = ["gate", "build", "tonight", "shrine", "zombies", "log"]
ADVANCED_TABS = {"tonight", "shrine"}   # แท็บของระบบเสริม (ระดับปกติขึ้นไป)
FONT_LOGO = ("Courier", 20, "bold")
FONT_STORY = ("TkDefaultFont", 17)

# ชื่องานแบบสั้นสำหรับปุ่มบนการ์ด
JOB_SHORT = {"scavenge": {"th": "หาของ", "en": "Scavenge"}, "guard": {"th": "เฝ้ายาม", "en": "Guard"},
             "heal": {"th": "น้ำมนต์", "en": "Bless"}, "rest": {"th": "พักผ่อน", "en": "Rest"}}


def hp_color(hp: int) -> str:
    """สีของแถบ HP: เขียว / เหลือง / แดง (ต่ำกว่าเกณฑ์ออกไปทำงาน)"""
    if hp >= 70:
        return COLORS["accent"]
    if hp >= MIN_SCAVENGE_HP:
        return COLORS["amber"]
    return COLORS["red"]


def skills_grid(parent: tk.Widget, skills: dict, bg: str) -> tk.Frame:
    """ทักษะแบบดาว 3 คอลัมน์: ชื่อทักษะอยู่บน ดาวอยู่ล่าง (ดาวทอง = เก่ง)"""
    grid = tk.Frame(parent, bg=bg)
    for column, (skill, level) in enumerate(skills.items()):
        grid.columnconfigure(column, weight=1, uniform="skills")
        label(grid, tr(SKILLS[skill]), bg, COLORS["muted"], FONT_SMALL).grid(row=0, column=column, sticky="w")
        label(grid, survivors.stars(level), bg, COLORS["amber"] if level >= 4 else COLORS["text"],
              FONT_SMALL_BOLD).grid(row=1, column=column, sticky="w")
    return grid


def pretty(line: str) -> str:
    """
    แปลงอีโมจิที่ Tk แสดงไม่ได้ให้เป็นชื่อ เฉพาะตำแหน่งที่เป็นตัวเลข เช่น '👻x5' → 'วิญญาณเร่ร่อน x5', '🍚-3' → 'อาหาร -3'
    แล้วตัดอีโมจิที่เหลือออก
    """
    for zombie in ZOMBIES:
        line = re.sub(re.escape(zombie["icon"]) + r"(?=x\d)", tr(zombie["name"]) + " ", line)
    for info in RESOURCES.values():
        line = re.sub(re.escape(info["icon"]) + r"(?=[+-]\d)", tr(info["name"]) + " ", line)
    return tk_safe(line)


def line_color(line: str) -> str:
    """สีของบรรทัดในรายงานกลางคืน (ดูจากสัญลักษณ์ก่อนแปลงข้อความ)"""
    if horde_counts(line) or "🐯" in line:
        return COLORS["amber"]
    if any(mark in line for mark in ("ได้ผล!", " works!", "เจ้าที่คุ้มครอง", "spirit keeps watch", "🎫")):
        return COLORS["accent"]
    if any(mark in line for mark in ("✖", "🩸", "😈", "🪦", "💀", "😵", "😱", "🎭", "👤", "⚡")):
        return COLORS["red"]
    if any(mark in line for mark in ("✔", "🌀", "✚", "🎁")):
        return COLORS["accent"]
    return COLORS["text"]


def horde_counts(line: str) -> list:
    """อ่านองค์ประกอบฝูงจากบรรทัดรายงาน เช่น '👻x5 🔥x2' → [(1, 5), (2, 2)]"""
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
        self.message = (get_text("ยินดีต้อนรับสู่มิติผี มอบงานให้ทุกคน แล้วกดจบวัน",
                                 "Welcome to the ghost realm. Give everyone a job, then end the day."), COLORS["muted"])
        root.title("GHOST REALM - หลุดมิติผี")
        root.geometry("1360x860")
        root.minsize(1220, 760)
        root.configure(bg=COLORS["bg"])
        self.tick = 0            # นับเฟรมแอนิเมชัน
        self.floaters = []       # ผีในฉากที่ลอยขึ้นลง: (item, x, y, phase)
        self.fog = []            # แถบหมอกที่เลื่อนไปทางขวา
        self.blink_cards = []    # การ์ดคนที่ถูกผีสิง (ขอบกะพริบแดง)
        self.build_layout()
        self.refresh()
        root.after(ANIM_MS, self.animate)

    # ---------- โครงหน้าต่าง ----------

    def build_layout(self) -> None:
        """สร้างส่วนที่อยู่คงที่ของหน้าต่าง"""
        header = tk.Frame(self.root, bg=COLORS["bg"], padx=20, pady=10)
        header.pack(fill="x")
        self.logo = tk.Label(header, font=FONT_LOGO, bg=COLORS["bg"], fg=COLORS["accent"])
        self.logo.pack(side="left")

        # ปุ่มด้านขวา pack ก่อนแถบสถานะ เพื่อไม่ให้ถูกดันจนหลุดจอ
        self.lang_buttons = {}
        for lang, text in (("en", "EN"), ("th", "ไทย")):
            button = tk.Button(header, text=text, font=FONT_SMALL_BOLD, width=4, relief="flat", bd=0,
                               cursor="hand2", highlightthickness=0, command=lambda l=lang: self.change_language(l))
            button.pack(side="right", padx=2)
            self.lang_buttons[lang] = button
        self.new_button = flat_button(header, "", self.new_game, COLORS["panel"], COLORS["red_dark"], size=10)
        self.new_button.pack(side="right", padx=(0, 12))
        self.help_button = flat_button(header, "", self.show_help, COLORS["panel"], COLORS["card_hover"], size=10)
        self.help_button.pack(side="right", padx=(0, 6))

        self.top_bar = tk.Frame(header, bg=COLORS["bg"])
        self.top_bar.pack(side="left", padx=14)

        tk.Frame(self.root, bg=COLORS["accent"], height=2).pack(fill="x", padx=20)

        # แถบล่าง pack ก่อนส่วนกลาง เพื่อให้อยู่บนจอเสมอ
        footer = tk.Frame(self.root, bg=COLORS["panel"], padx=20, pady=12)
        footer.pack(side="bottom", fill="x")
        self.end_button = flat_button(footer, "", self.end_day, COLORS["red"], COLORS["red_dark"], size=13, padx=22, pady=8)
        self.end_button.pack(side="right")
        self.auto_button = flat_button(footer, "", self.auto_assign, COLORS["accent"], COLORS["accent_dark"],
                                       fg=COLORS["ink"], size=12, padx=16, pady=8)
        self.auto_button.pack(side="right", padx=10)
        threat_box = tk.Frame(footer, bg=COLORS["panel"])
        threat_box.pack(side="right", padx=10)
        self.defense_label = label(threat_box, "", COLORS["panel"], COLORS["muted"], FONT_SMALL_BOLD)
        self.defense_label.pack(anchor="w")
        self.threat_bar = tk.Canvas(threat_box, width=260, height=10, bg=COLORS["disabled"], highlightthickness=0)
        self.threat_bar.pack(anchor="w", pady=(4, 0))
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
        self.scene = tk.Canvas(left, height=SCENE_HEIGHT, bg=COLORS["screen"], highlightthickness=0)
        self.scene.pack(fill="x", pady=(0, 10))
        self.scene.bind("<Configure>", lambda event: self.draw_scene())
        self.left_title = tk.Frame(left, bg=COLORS["bg"])
        self.left_title.pack(fill="x", pady=(0, 6))
        self.people_view = ScrollableFrame(left, COLORS["bg"])
        self.people_view.pack(fill="both", expand=True)

    def refresh(self) -> None:
        """วาดข้อมูลทั้งหมดใหม่ตามสถานะเกมปัจจุบัน"""
        self.draw_header()
        self.draw_scene()
        self.draw_people()
        self.draw_tabs()
        self.draw_footer()

    # ---------- ฉากศาลาและแอนิเมชัน ----------

    def draw_scene(self) -> None:
        """
        ฉากหนังตะลุงเหนือการ์ด: จอผ้า พระจันทร์ เงาศาลา ผู้รอดชีวิตหน้าศาลา
        และเงาผีที่อาจบุกคืนนี้ลอยอยู่ในควัน (ยิ่งหลายวันยิ่งเยอะ)
        """
        canvas = self.scene
        canvas.delete("all")
        self.floaters, self.fog = [], []
        width = canvas.winfo_width()
        if width < 50:
            return
        state = storage.state
        rng = random.Random(state["day"])
        base = SCENE_HEIGHT - 16
        center = width // 2

        # จอผ้า: ขอบซ้ายขวาเข้มกว่า (ไฟส่องไม่ถึง) และพระจันทร์ดวงใหญ่หลังศาลา
        canvas.create_rectangle(0, 0, 60, SCENE_HEIGHT, fill=COLORS["screen_edge"], width=0)
        canvas.create_rectangle(width - 60, 0, width, SCENE_HEIGHT, fill=COLORS["screen_edge"], width=0)
        canvas.create_rectangle(60, 0, 90, SCENE_HEIGHT, fill=COLORS["screen_edge"], stipple="gray50", width=0)
        canvas.create_rectangle(width - 90, 0, width - 60, SCENE_HEIGHT, fill=COLORS["screen_edge"], stipple="gray50",
                                width=0)
        canvas.create_oval(center - 80, base - 150, center + 80, base + 10, fill=COLORS["moon"], width=0)

        # เงาผีด้านซ้ายและขวาของศาลา (ชนิดที่โผล่แล้วเท่านั้น, คืนสุดท้ายมีเสือสมิงด้วย)
        today = state["day"]
        if state["status"] == "playing" and today >= RAID_START_DAY:
            kinds = [ZOMBIE_SPRITES[z["level"] - 1] for z in ZOMBIES if storage.ghost_day(z["level"]) <= today and z["level"] < 5]
            count = min(10, 2 + today // 2)
            for index in range(count):
                side = index % 2
                low, high = (130, center - 150) if side == 0 else (center + 150, width - 30)
                x = rng.randrange(low, max(low + 1, high))
                self.add_floater(sprite(rng.choice(kinds), 3), x, base - rng.randrange(0, 18))
            if today >= storage.goal_day():
                self.add_floater(sprite(ZOMBIE_SPRITES[4], 4), width - 140, base - 4)
        elif state["status"] == "playing":
            canvas.create_text(width - 100, 14, anchor="ne", fill=COLORS["puppet"], font=FONT_SMALL,
                               text=tk_safe(get_text(f"ยังเงียบอยู่... ผีจะเริ่มออกมาวันที่ {RAID_START_DAY}",
                                                     f"Quiet for now... ghosts come out on day {RAID_START_DAY}")))

        # ลางของวันนี้เขียนไว้มุมซ้ายบนของจอผ้า
        if realm.omen_text() and state["status"] == "playing":
            canvas.create_text(100, 10, anchor="nw", width=center - 100, fill=COLORS["puppet"], font=FONT_SMALL_BOLD,
                               text=tk_safe(realm.omen_text()))

        # ศาลา (หลังคาจั่ว + ประตูมีแสงเทียน)
        canvas.create_polygon(center - 115, base - 62, center, base - 118, center + 115, base - 62,
                              fill=COLORS["far"], outline="")
        canvas.create_rectangle(center - 88, base - 62, center + 88, base, fill=COLORS["far"], width=0)
        canvas.create_rectangle(center - 14, base - 42, center + 14, base, fill=COLORS["moon"], width=0)
        canvas.create_rectangle(center - 7, base - 34, center + 7, base, fill="#e88a3a", width=0, tags="flame")
        canvas.create_rectangle(0, base, width, SCENE_HEIGHT, fill=COLORS["puppet"], width=0)

        # ผู้รอดชีวิตยืนหน้าศาลา (คนที่ถูกผีสิงมีจุดแดงเหนือหัว)
        people = state["survivors"]
        for index, person in enumerate(people):
            x = center + (index - (len(people) - 1) / 2) * 44
            canvas.create_image(x, base + 4, image=sprite(survivors.look_of(person), 3), anchor="s")
            if person["infected"]:
                canvas.create_rectangle(x - 3, base - 56, x + 3, base - 50, fill=COLORS["red"], width=0)

        # ควันลายจุดเลื่อนช้าๆ ตามพื้น
        for index in range(4):
            x = index * width // 4
            y = base - 12 + (index % 2) * 6
            self.fog.append(canvas.create_rectangle(x, y, x + 220, y + 12, fill=COLORS["screen_edge"],
                                                    stipple="gray12", width=0))

    def add_floater(self, image: tk.PhotoImage, x: int, y: int) -> None:
        """วางภาพผีในฉาก แล้วจำไว้ให้ animate() ทำให้ลอยขึ้นลง"""
        item = self.scene.create_image(x, y, image=image, anchor="s")
        self.floaters.append((item, x, y, random.randrange(100)))

    def animate(self) -> None:
        """เฟรมแอนิเมชัน: ผีลอย ควันเลื่อน เปลวเทียนไหว และการ์ดคนถูกผีสิงกะพริบ"""
        self.tick += 1
        canvas = self.scene
        width = canvas.winfo_width()
        for item, x, y, phase in self.floaters:
            canvas.coords(item, x + math.sin((self.tick + phase) / 25) * 5, y + math.sin((self.tick + phase) / 9) * 4)
        for item in self.fog:
            canvas.move(item, 1, 0)
            if canvas.coords(item) and canvas.coords(item)[0] > width:
                canvas.move(item, -(width + 240), 0)
        if self.tick % 12 == 0:
            canvas.itemconfig("flame", fill=random.choice(["#e88a3a", COLORS["amber"]]))
        if self.tick % 8 == 0:
            color = COLORS["red"] if self.tick % 16 else COLORS["red_dark"]
            for card in self.blink_cards:
                if card.winfo_exists():
                    card.config(highlightbackground=color)
        self.root.after(ANIM_MS, self.animate)

    def show_intro(self) -> None:
        """หน้าเปิดเรื่อง: ฟ้ามืดมีดาว จอหนังตะลุงด้านล่างมีเงาผีลอย และเรื่องเล่าค่อยๆ พิมพ์ขึ้นทีละตัวอักษร"""
        root = self.root
        root.update_idletasks()
        width, height = root.winfo_width(), root.winfo_height()
        overlay = tk.Canvas(root, bg=COLORS["bg"], highlightthickness=0)
        overlay.place(x=0, y=0, relwidth=1, relheight=1)
        rng = random.Random(31)
        for _ in range(90):
            x, y = rng.randrange(width), rng.randrange(height * 2 // 3)
            overlay.create_rectangle(x, y, x + 2, y + 2, fill=rng.choice([COLORS["line"], COLORS["muted"]]), width=0)
        overlay.create_oval(width - 210, 60, width - 130, 140, fill=COLORS["moon"], width=0)
        overlay.create_oval(width - 188, 48, width - 112, 124, fill=COLORS["bg"], width=0)
        # จอหนังตะลุงแถบล่าง: เงาผีลอยไปมาบนจอผ้าสีส้ม
        stage = height - 250
        overlay.create_rectangle(0, stage, width, height, fill=COLORS["screen"], width=0)
        overlay.create_rectangle(0, stage, width, stage + 6, fill=COLORS["puppet"], width=0)
        overlay.create_oval(width // 2 - 110, stage + 20, width // 2 + 110, stage + 240, fill=COLORS["moon"], width=0)
        overlay.create_rectangle(0, height - 24, width, height, fill=COLORS["puppet"], width=0)
        ghosts = []
        for name, x, scale in (("spirit", 150, 10), ("preta", 420, 8), ("pop", width - 420, 8), ("krasue", width - 170, 10)):
            ghosts.append((overlay.create_image(x, height - 30, image=sprite(name, scale), anchor="s"), x, height - 30))
        text = overlay.create_text(width // 2, stage // 2, text="", fill=COLORS["text"], font=FONT_STORY,
                                   justify="center")
        lines = STORY[get_language()]
        progress = {"line": 0, "char": 0, "frame": 0}

        def close(event=None) -> None:
            root.unbind("<Return>")
            root.unbind("<Escape>")
            overlay.destroy()

        button = flat_button(overlay, get_text("ข้าม", "Skip"), close, COLORS["panel"], COLORS["card_hover"], size=12,
                             padx=20, pady=6)
        overlay.create_window(width // 2, stage - 50, window=button)
        root.bind("<Return>", close)
        root.bind("<Escape>", close)

        def float_ghosts() -> None:
            if not overlay.winfo_exists():
                return
            progress["frame"] += 1
            for index, (item, x, y) in enumerate(ghosts):
                overlay.coords(item, x + math.sin((progress["frame"] + index * 40) / 30) * 8,
                               y + math.sin((progress["frame"] + index * 25) / 12) * 8)
            overlay.after(ANIM_MS, float_ghosts)

        def type_next() -> None:
            if not overlay.winfo_exists():
                return
            line, char = progress["line"], progress["char"] + 1
            if line >= len(lines):
                overlay.itemconfig(text, text="\n".join(lines))
                set_button_text(button, get_text("เข้าสู่มิติผี  ▶", "Enter the ghost realm  ▶"), 12)
                button.config(bg=COLORS["accent"], fg=COLORS["ink"], activebackground=COLORS["accent_dark"],
                              activeforeground=COLORS["ink"])
                add_hover(button, COLORS["accent"], COLORS["accent_dark"])
                return
            overlay.itemconfig(text, text="\n".join(lines[:line] + [lines[line][:char] + "▌"]))
            if char >= len(lines[line]):
                progress["line"], progress["char"] = line + 1, 0
                overlay.after(600, type_next)
            else:
                progress["char"] = char
                overlay.after(TYPE_MS, type_next)

        float_ghosts()
        overlay.after(500, type_next)

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
        """โลโก้ วันที่ (แถบ 15 ช่อง) และทรัพยากรพร้อมคาดการณ์"""
        logo = get_text("หลุดมิติผี", "GHOST REALM")
        self.logo.config(text=logo, font=FONT_LOGO if logo.isascii() else type_font(logo, 20))
        for widget in self.top_bar.winfo_children():
            widget.destroy()
        state = storage.state
        bg = COLORS["bg"]

        day_box = tk.Frame(self.top_bar, bg=bg)
        day_box.pack(side="left", padx=(0, 14))
        level = tr(DIFFICULTIES[state["difficulty"]]["name"])
        day_text = get_text(f"วันที่ {state['day']}/{storage.goal_day()}  ·  {level}", f"DAY {state['day']}/{storage.goal_day()}  ·  {level}")
        tk.Label(day_box, text=day_text, font=type_font(day_text, 13), bg=bg, fg=COLORS["text"]).pack(anchor="w")
        # แถบวันเป็นเทียน 15 เล่ม: วันที่ผ่านไปแล้วเทียนดับ วันนี้เปลวไฟใหญ่ เล่มสุดท้ายสีแดง (คืนบอส)
        track = tk.Canvas(day_box, width=storage.goal_day() * 11, height=18, bg=bg, highlightthickness=0)
        track.pack(anchor="w", pady=(3, 0))
        for number in range(1, storage.goal_day() + 1):
            x = (number - 1) * 11
            if number == state["day"] and state["status"] == "playing":
                track.create_rectangle(x, 6, x + 10, 18, fill=COLORS["card_hover"], width=0)
            if number < state["day"] or state["status"] != "playing":
                body, flame = COLORS["disabled"], None
            elif number == state["day"]:
                body, flame = COLORS["text"], (COLORS["amber"], 0)
            else:
                body, flame = COLORS["muted"], ("#e88a3a", 3)
            if number == storage.goal_day() and body != COLORS["disabled"]:
                body = COLORS["red"]
            track.create_rectangle(x + 2, 8, x + 8, 18, fill=body, width=0)
            if flame:
                track.create_rectangle(x + 3, flame[1], x + 7, 7, fill=flame[0], width=0)

        for key in RESOURCES:
            chip = tk.Frame(self.top_bar, bg=COLORS["panel"], padx=7, pady=3)
            chip.pack(side="left", padx=3)
            picture(chip, sprite(key, 2)).pack(side="left")
            text_box = tk.Frame(chip, bg=COLORS["panel"])
            text_box.pack(side="left", padx=(6, 0))
            label(text_box, str(state["resources"][key]), COLORS["panel"], font=FONT_BOLD).pack(anchor="w")
            if key in ("food", "water"):
                days = camp.days_left(key)
                color = COLORS["red"] if days <= 1 else COLORS["amber"] if days <= 2 else COLORS["muted"]
                label(text_box, camp.days_text(key), COLORS["panel"], color, FONT_SMALL).pack(anchor="w")

        if realm.advanced():
            chip = tk.Frame(self.top_bar, bg=COLORS["panel"], padx=8, pady=3)
            chip.pack(side="left", padx=(10, 3))
            grudge = state["grudge"]
            label(chip, get_text(f"ความแค้น {grudge}/{MAX_GRUDGE}", f"Grudge {grudge}/{MAX_GRUDGE}"), COLORS["panel"],
                  COLORS["red"] if grudge >= 5 else COLORS["text"], FONT_SMALL_BOLD).pack(anchor="w")
            bar = meter(chip, grudge / MAX_GRUDGE, COLORS["red"], height=5)
            bar.config(width=90)
            bar.pack(anchor="w", pady=(3, 0))
            chip = tk.Frame(self.top_bar, bg=COLORS["panel"], padx=8, pady=3)
            chip.pack(side="left", padx=3)
            label(chip, get_text("ตั๋ว", "Ticket"), COLORS["panel"], COLORS["muted"], FONT_SMALL).pack(anchor="w")
            label(chip, f"{state['tickets']}/{TICKET_PIECES}", COLORS["panel"],
                  COLORS["accent"] if state["tickets"] else COLORS["text"], FONT_BOLD).pack(anchor="w")

        lang = get_language()
        for code, button in self.lang_buttons.items():
            active = code == lang
            button.config(bg=COLORS["accent"] if active else COLORS["panel"],
                          fg=COLORS["ink"] if active else COLORS["muted"],
                          activebackground=COLORS["accent_dark"])
        set_button_text(self.help_button, get_text("? วิธีเล่น", "? Help"), 10)
        set_button_text(self.new_button, get_text("เริ่มเกมใหม่", "New Game"), 10)

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
        self.blink_cards = []
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
        # ปุ่ม pack ก่อนข้อความ เพื่อไม่ให้ข้อความยาวดันปุ่มหลุดจอ
        flat_button(banner, get_text("เริ่มเกมใหม่", "New Game"), self.new_game, COLORS["accent"],
                    COLORS["accent_dark"], fg=COLORS["ink"]).pack(side="right")
        if state["status"] == "won":
            saved = len(day.rescued())
            stars, title = day.ending_grade(saved, state["escaped"])
            label(banner, "★" * stars + "☆" * (3 - stars), COLORS["card"], COLORS["amber"], FONT_HUGE).pack(side="left")
            text = get_text(f"ประตูมิติเปิดแล้ว! กลับบ้านได้ {saved} คน — {title}",
                            f"The portal opened! {saved} survivor(s) made it home — {title}")
        else:
            text = get_text("ทุกคนติดอยู่ในมิติผี... ไม่มีใครได้กลับบ้าน", "Everyone is lost in the ghost realm... No one made it home.")
        label(banner, text, COLORS["card"], font=FONT_BIG, wraplength=420, justify="left").pack(side="left", padx=14)

    def person_card(self, parent: tk.Widget, person: dict) -> tk.Frame:
        """การ์ดของผู้รอดชีวิต 1 คน"""
        bg = COLORS["card"]
        card = tk.Frame(parent, bg=bg, padx=12, pady=10,
                        highlightthickness=2 if person["infected"] else 0, highlightbackground=COLORS["red"])
        if person["infected"]:
            self.blink_cards.append(card)
        top = tk.Frame(card, bg=bg)
        top.pack(fill="x")
        picture(top, sprite(survivors.look_of(person), 4)).pack(side="left", anchor="n")

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


        skills_grid(card, person["skills"], bg).pack(fill="x", pady=(8, 0))

        if person["infected"]:
            warn = tk.Frame(card, bg=COLORS["red_dark"], padx=8, pady=3)
            warn.pack(fill="x", pady=(6, 0))
            label(warn, survivors.infection_text(person) + get_text("  ต้องได้น้ำมนต์!", "  Needs holy water!"),
                  COLORS["red_dark"], "white", FONT_SMALL_BOLD, wraplength=340, justify="left").pack(anchor="w")

        if storage.state["status"] != "playing":
            return card
        jobs = tk.Frame(card, bg=bg)
        jobs.pack(fill="x", pady=(8, 0))
        if person["job"] == "inspect":
            label(jobs, get_text("กำลังส่องดูเงาคนแปลกหน้าที่ประตู (ทั้งวัน)", "Checking the newcomer's shadow (all day)"),
                  bg, COLORS["blue"], FONT_SMALL_BOLD).pack(anchor="w")
            return card

        best = survivors.recommend_job(person)
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
            text = tr(JOB_SHORT[job]) + (" ★" if job == best and not chosen else "")
            button = flat_button(jobs, text, lambda j=job: self.assign(person, j), color,
                                 COLORS["accent_dark"] if allowed else COLORS["disabled"], fg=fg, size=9, padx=4, pady=4)
            button.grid(row=0, column=column, sticky="ew", padx=1)
        if person["job"] == "scavenge" and person.get("target") and realm.advanced():
            label(card, get_text("ไปที่: ", "Going to: ") + tr(LOCATIONS[person["target"]]["name"]), bg, COLORS["amber"],
                  FONT_SMALL_BOLD).pack(anchor="w", pady=(4, 0))
        return card

    # ---------- แท็บด้านขวา ----------

    def draw_tabs(self) -> None:
        """ปุ่มแท็บและเนื้อหาของแท็บที่เลือก"""
        for widget in self.tab_bar.winfo_children():
            widget.destroy()
        names = {"gate": get_text("ประตู", "Gate"), "build": get_text("สร้าง", "Build"),
                 "tonight": get_text("คืนนี้", "Tonight"), "shrine": get_text("ศาลเจ้า", "Shrine"),
                 "zombies": get_text("ผี", "Ghosts"), "log": get_text("บันทึก", "Log")}
        tabs = [key for key in TABS if realm.advanced() or key not in ADVANCED_TABS]
        if self.tab not in tabs:
            self.tab = "gate"
        for key in tabs:
            waiting = storage.state["wanderer"] and storage.state["status"] == "playing"
            text = names[key] + (" (!)" if key == "gate" and waiting else "")
            active = key == self.tab
            button = flat_button(self.tab_bar, text, lambda k=key: self.switch_tab(k),
                                 COLORS["accent"] if active else COLORS["panel"],
                                 COLORS["accent_dark"] if active else COLORS["card_hover"],
                                 fg=COLORS["ink"] if active else COLORS["text"], size=10, padx=9)
            button.pack(side="left", padx=(0, 2))

        self.tab_view.clear()
        self.tab_view.canvas.yview_moveto(0)
        {"gate": self.draw_gate, "build": self.draw_build, "tonight": self.draw_tonight, "shrine": self.draw_shrine,
         "zombies": self.draw_zombies, "log": self.draw_log}[self.tab](self.tab_view.inner)

    def switch_tab(self, key: str) -> None:
        self.tab = key
        self.draw_tabs()

    def draw_gate(self, parent: tk.Widget) -> None:
        """แท็บประตู: คนแปลกหน้าที่มาขอเข้าศาลา"""
        bg = COLORS["panel"]
        state = storage.state
        wanderer = state["wanderer"]
        section_title(parent, get_text("ประตูศาลา", "SALA GATE"), bg).pack(anchor="w")
        if state["status"] != "playing":
            wanderer = None
        if wanderer is None:
            picture(parent, sprite("stranger", 6, shadow=True)).pack(pady=(30, 10))
            label(parent, get_text("ไม่มีใครอยู่ที่ประตูวันนี้", "No one is at the gate today."), bg, COLORS["muted"],
                  FONT_BOLD).pack()
            label(parent, get_text("บางเช้าจะมีคนที่หลงเข้ามาในมิติผีมาขอเข้าศาลา (สูงสุด 6 คน)", "Some mornings a lost stranger asks to join (max 6)."),
                  bg, COLORS["muted"], FONT_SMALL).pack(pady=(4, 0))
            return

        card = tk.Frame(parent, bg=COLORS["card"], padx=14, pady=12)
        card.pack(fill="x", pady=(10, 0))
        top = tk.Frame(card, bg=COLORS["card"])
        top.pack(fill="x")
        picture(top, sprite("stranger", 5)).pack(side="left")
        info = tk.Frame(top, bg=COLORS["card"])
        info.pack(side="left", padx=14, fill="x", expand=True)
        label(info, wanderer["name"], COLORS["card"], font=FONT_BIG).pack(anchor="w")
        label(info, f"HP {wanderer['hp']}/{MAX_HP}", COLORS["card"], COLORS["muted"], FONT_SMALL_BOLD).pack(anchor="w")
        skills_grid(card, wanderer["skills"], COLORS["card"]).pack(fill="x", pady=(10, 0))
        for line in realm.story_lines(wanderer):
            label(card, line, COLORS["card"], COLORS["amber"], FONT_SMALL_BOLD).pack(anchor="w", pady=(6, 0))

        if wanderer["checked"] and wanderer["infected"]:
            result, color = get_text("ผลตรวจ: เงาไม่ขยับตามตัว! ถูกผีสิง", "Inspection: their shadow doesn't move! Possessed"), COLORS["red"]
        elif wanderer["checked"]:
            result, color = get_text("ผลตรวจ: เงาปกติ ปลอดภัย", "Inspection: normal shadow, safe"), COLORS["accent"]
        else:
            result, color = get_text("ยังไม่ได้ส่องดูเงา อาจถูกผีสิงมาแล้ว!", "Not inspected — could be possessed!"), COLORS["amber"]
        box = tk.Frame(card, bg=color, padx=8, pady=4)
        box.pack(fill="x", pady=(10, 0))
        label(box, result, color, COLORS["ink"], FONT_SMALL_BOLD).pack(anchor="w")

        label(parent, get_text(f"รับเข้ามาต้องเลี้ยงเพิ่ม: อาหาร +1 และน้ำ +1 ต่อวัน   (ศาลา {len(state['survivors'])}/{MAX_CAMP})",
                               f"One more mouth: +1 food and +1 water per day   (sala {len(state['survivors'])}/{MAX_CAMP})"),
              bg, COLORS["muted"], FONT_SMALL, wraplength=440, justify="left").pack(anchor="w", pady=(10, 6))

        row = tk.Frame(parent, bg=bg)
        row.pack(fill="x")
        flat_button(row, get_text("รับเข้าศาลา", "Let in"), self.accept, COLORS["accent"], COLORS["accent_dark"],
                    fg=COLORS["ink"]).pack(side="left", padx=(0, 6))
        flat_button(row, get_text("ไม่รับ", "Turn away"), self.reject, COLORS["red"], COLORS["red_dark"]).pack(side="left", padx=(0, 6))
        if not wanderer["checked"]:
            flat_button(row, get_text("ส่องดูเงาก่อน", "Check shadow"), self.inspect, COLORS["blue"], "#3d86c0").pack(side="left")
            label(parent, get_text("ส่องดูเงา = ใช้คนว่าง 1 คนทั้งวัน", "Checking a shadow uses one free survivor for the day"),
                  bg, COLORS["muted"], FONT_SMALL).pack(anchor="w", pady=(6, 0))

    def draw_build(self, parent: tk.Widget) -> None:
        """แท็บสร้างสิ่งก่อสร้าง"""
        bg = COLORS["panel"]
        section_title(parent, get_text("สร้างสิ่งก่อสร้าง", "BUILD"), bg).pack(anchor="w")
        for key, info in BUILDINGS.items():
            built = key in storage.state["buildings"]
            card = tk.Frame(parent, bg=COLORS["card"], padx=12, pady=10)
            card.pack(fill="x", pady=(10, 0))
            picture(card, sprite(key, 4)).pack(side="left")
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
        """แท็บผี: ภัยคุกคามทั้ง 5 เลเวล (ตัวที่ยังไม่โผล่เป็นเงาดำ)"""
        bg = COLORS["panel"]
        today = storage.state["day"]
        section_title(parent, get_text("ภัยคุกคาม", "THREATS"), bg).pack(anchor="w")
        if today < RAID_START_DAY:
            note = get_text(f"ผีจะเริ่มบุกตั้งแต่วันที่ {RAID_START_DAY}", f"Raids begin on day {RAID_START_DAY}")
        else:
            note = get_text("ทุกคืนมีโอกาสถูกบุก ฝูงใหญ่ขึ้นทุกวัน และคืนสุดท้ายบุกแน่นอน",
                            "Raids can come any night, hordes grow daily, and the last night is certain")
        label(parent, note, bg, COLORS["muted"], FONT_SMALL, wraplength=440, justify="left").pack(anchor="w")
        label(parent, get_text(f"พลังป้องกันคืนนี้: {day.defense()}  (เฝ้ายาม + สายสิญจน์)",
                               f"Defense tonight: {day.defense()}  (guards + sacred thread)"), bg, COLORS["accent"],
              FONT_BOLD).pack(anchor="w", pady=(4, 0))

        for zombie in ZOMBIES:
            seen = storage.ghost_day(zombie["level"]) <= today
            card = tk.Frame(parent, bg=COLORS["card"], padx=12, pady=8)
            card.pack(fill="x", pady=(10, 0))
            picture(card, sprite(ZOMBIE_SPRITES[zombie["level"] - 1], 5, shadow=not seen)).pack(side="left")
            text_box = tk.Frame(card, bg=COLORS["card"])
            text_box.pack(side="left", fill="x", expand=True, padx=12)
            name = f"Lv.{zombie['level']}  " + (tr(zombie["name"]) if seen else "???")
            label(text_box, name, COLORS["card"], COLORS["text"] if seen else COLORS["muted"], FONT_BOLD).pack(anchor="w")
            label(text_box, get_text(f"พลังโจมตี {zombie['power']}  ·  เริ่มโผล่วันที่ {storage.ghost_day(zombie['level'])}",
                                     f"Power {zombie['power']}  ·  appears from day {storage.ghost_day(zombie['level'])}"),
                  COLORS["card"], COLORS["muted"], FONT_SMALL).pack(anchor="w")
            label(text_box, tr(zombie["about"]), COLORS["card"], COLORS["amber"] if seen else COLORS["muted"],
                  FONT_SMALL).pack(anchor="w")

    def draw_log(self, parent: tk.Widget) -> None:
        """แท็บบันทึก: สถิติ กราฟอาหาร/น้ำรายวัน และผลเกมที่ผ่านมา"""
        bg = COLORS["panel"]
        state = storage.state
        log = state["log"]
        stats = day.camp_stats()
        section_title(parent, get_text("บันทึกศาลา", "SALA LOG"), bg).pack(anchor="w")
        rows = [
            (get_text("ผีบุก / ต้านได้", "Raids / repelled"), f"{log['raids']} / {log['repelled']}  ({stats['defense_rate']:.0f}%)"),
            (get_text("ถูกผีสิง / ไล่ผีออกได้", "Possessed / freed"), f"{log['infected']} / {log['cured']}  ({stats['cure_rate']:.0f}%)"),
            (get_text("กลายเป็นผี / เสียชีวิต", "Became ghosts / died"), f"{log['turned']} / {log['deaths']}"),
            (get_text("คนเข้าร่วมใหม่", "Joined"), str(log["joined"])),
            (get_text("หาของได้ทั้งหมด", "Total gathered"), str(stats["gathered"])),
            (get_text("ฝูงใหญ่ที่สุด (พลัง)", "Biggest horde (power)"), str(log["biggest_horde"])),
        ]
        if realm.advanced():
            rows += [(get_text("ความแค้นของมิติผี", "Realm grudge"), f"{state['grudge']}/{MAX_GRUDGE}"),
                     (get_text("ชิ้นส่วนตั๋ว", "Ticket pieces"), f"{state['tickets']}/{TICKET_PIECES}"),
                     (get_text("ผีเพื่อนที่ยังวนเวียน", "Restless friends"), ", ".join(state["fallen"]) or "-")]
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
                text = get_text(f"เกมที่ {game['game']}:  ติดอยู่ในมิติผีวันที่ {game['day']}", f"Game {game['game']}:  lost on day {game['day']}")
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
        step = (width - pad * 2) / (storage.goal_day() - 1)
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
        canvas.create_text(width - pad, height - 8, anchor="e", fill=COLORS["muted"], font=FONT_SMALL, text=str(storage.goal_day()))

    # ---------- แถบล่าง ----------

    def draw_footer(self) -> None:
        """ข้อความล่าสุด พลังป้องกัน และปุ่มหลัก"""
        self.message_label.config(text=tk_safe(self.message[0]), fg=self.message[1])
        playing = storage.state["status"] == "playing"
        # แถบพลังป้องกัน (เขียว) เทียบกับพลังผีเฉลี่ยที่อาจบุกคืนนี้ (เส้นแดง)
        guard, threat = day.defense(), day.expected_horde_power()
        if threat:
            text = get_text(f"พลังป้องกันคืนนี้ {guard}  ·  ผีที่อาจมา ~{threat}",
                            f"Defense tonight {guard}  ·  ghosts may bring ~{threat}")
        else:
            text = get_text(f"พลังป้องกันคืนนี้ {guard}  ·  ยังไม่มีผีบุก", f"Defense tonight {guard}  ·  no raids yet")
        self.defense_label.config(text=tk_safe(text), fg=COLORS["red"] if guard < threat else COLORS["muted"])
        bar = self.threat_bar
        bar.delete("all")
        scale = 260 / (max(guard, threat, 1) * 1.25)
        bar.create_rectangle(0, 0, guard * scale, 10, fill=COLORS["accent"], width=0)
        if threat:
            bar.create_rectangle(threat * scale - 1, 0, threat * scale + 1, 10, fill=COLORS["red"], width=0)
        set_button_text(self.auto_button, get_text("จัดงานอัตโนมัติ", "Auto-assign"), 12)
        if playing:
            set_button_text(self.end_button, get_text(f"จบวันที่ {storage.state['day']}  ▶", f"End Day {storage.state['day']}  ▶"), 13)
        else:
            set_button_text(self.end_button, get_text("เริ่มเกมใหม่  ▶", "New Game  ▶"), 13)

    # ---------- การกระทำ (เรียกฟังก์ชันกลาง do_* ชุดเดียวกับ Terminal) ----------

    def assign(self, person: dict, job: str) -> None:
        if not self.playing():
            return
        target = None
        if job == "scavenge" and realm.advanced():
            target = self.choose_location(person)
            if target is None:
                return
        error = survivors.do_assign(person, job, target)
        if error:
            self.say(error, COLORS["red"])
        else:
            self.say(f"{person['name']}: {tk_safe(survivors.job_text(person))}", COLORS["accent"])
        self.refresh()

    def choose_location(self, person: dict):
        """หน้าต่างเลือกสถานที่ออกไปหาของ (ระดับปกติขึ้นไป) คืนค่า key หรือ None"""
        chosen = {"key": None}
        dialog = open_dialog(self.root, get_text(f"{person['name']} จะไปหาของที่ไหน?", f"Where does {person['name']} go?"),
                             COLORS["amber"])
        best = realm.recommend_location()

        def pick(key: str) -> None:
            chosen["key"] = key
            dialog.destroy()

        for key, info in LOCATIONS.items():
            text = get_text(f"{tr(info['name'])}  —  {tr(info['about'])}  (ของเหลือ {realm.location_factor(key):.0%})",
                            f"{tr(info['name'])}  —  {tr(info['about'])}  ({realm.location_factor(key):.0%} left)")
            if key == best:
                text += get_text("  ★ แนะนำ", "  ★ suggested")
            color = COLORS["red_dark"] if key == "graveyard" else COLORS["card"]
            flat_button(dialog, text, lambda k=key: pick(k), color, COLORS["card_hover"], size=10,
                        anchor="w").pack(fill="x", padx=28, pady=3)
        cancel = flat_button(dialog, get_text("ยกเลิก", "Cancel"), dialog.destroy, COLORS["panel"])
        cancel.pack(pady=(10, 18))
        wait_dialog(self.root, dialog, cancel)
        return chosen["key"]

    # ---------- แท็บคืนนี้ / ศาลเจ้า (ระดับปกติขึ้นไป) ----------

    def act(self, error: str, done: str) -> None:
        """แสดงผลของการกระทำ (ผิดพลาด = แดง, สำเร็จ = เขียว) แล้ววาดใหม่"""
        self.say(error or done, COLORS["red"] if error else COLORS["accent"])
        self.refresh()

    def draw_tonight(self, parent: tk.Widget) -> None:
        """แท็บคืนนี้: ลาง ไฟ และของแก้ผี"""
        bg = COLORS["panel"]
        state = storage.state
        section_title(parent, get_text("เตรียมรับคืนนี้", "PREPARE FOR TONIGHT"), bg).pack(anchor="w")
        omen = realm.omen_text() or get_text(f"ยังไม่มีลาง (ผีเริ่มบุกวันที่ {RAID_START_DAY})",
                                             f"No omen yet (raids start on day {RAID_START_DAY})")
        label(parent, omen, bg, COLORS["amber"], FONT_BOLD, wraplength=440, justify="left").pack(anchor="w", pady=(4, 8))
        label(parent, get_text(f"พลังป้องกันคืนนี้ {day.defense()}  ·  ผีที่อาจมา ~{day.expected_horde_power()}  ·  "
                               f"โอกาสถูกบุก {realm.raid_chance():.0%}",
                               f"Defense {day.defense()}  ·  ghosts ~{day.expected_horde_power()}  ·  "
                               f"raid chance {realm.raid_chance():.0%}"), bg, COLORS["muted"], FONT_SMALL_BOLD).pack(anchor="w")

        section_title(parent, get_text("ไฟในศาลา", "LIGHT"), bg, 11).pack(anchor="w", pady=(12, 4))
        row = tk.Frame(parent, bg=bg)
        row.pack(fill="x")
        for column, (key, info) in enumerate(LIGHTS.items()):
            row.columnconfigure(column, weight=1, uniform="lights")
            active = state["light"] == key
            box = tk.Frame(row, bg=COLORS["card"], padx=8, pady=6, highlightthickness=2 if active else 0,
                           highlightbackground=COLORS["accent"])
            box.grid(row=0, column=column, sticky="nsew", padx=2)
            flat_button(box, tr(info["name"]), lambda k=key: self.act(realm.do_set_light(k), tr(LIGHTS[k]["about"])),
                        COLORS["accent"] if active else COLORS["card_hover"], COLORS["accent_dark"],
                        fg=COLORS["ink"] if active else COLORS["text"], size=9).pack(fill="x")
            label(box, tr(info["about"]), COLORS["card"], COLORS["muted"], FONT_SMALL, wraplength=130,
                  justify="left").pack(anchor="w", pady=(4, 0))
            if info["cost"]:
                label(box, realm.cost_label(info["cost"]), COLORS["card"], COLORS["amber"], FONT_SMALL).pack(anchor="w")

        section_title(parent, get_text("ของแก้ผี (ใช้ได้คืนเดียว)", "COUNTERS (TONIGHT ONLY)"), bg, 11).pack(anchor="w", pady=(12, 0))
        hinted = state["omen"]["shown"] if state["omen"] else None
        for key, info in COUNTERS.items():
            ready = key in state["prepared"]
            card = tk.Frame(parent, bg=COLORS["card"], padx=10, pady=8, highlightthickness=2 if info["ghost"] == hinted else 0,
                            highlightbackground=COLORS["amber"])
            card.pack(fill="x", pady=(8, 0))
            picture(card, sprite(ZOMBIE_SPRITES[info["ghost"] - 1], 3)).pack(side="left")
            text_box = tk.Frame(card, bg=COLORS["card"])
            text_box.pack(side="left", fill="x", expand=True, padx=10)
            ghost = tr(ZOMBIES[info["ghost"] - 1]["name"])
            label(text_box, f"{tr(info['name'])}  vs  {ghost}", COLORS["card"], font=FONT_BOLD).pack(anchor="w")
            label(text_box, tr(info["about"]), COLORS["card"], COLORS["muted"], FONT_SMALL, wraplength=250,
                  justify="left").pack(anchor="w")
            label(text_box, realm.cost_label(info["cost"]), COLORS["card"], COLORS["amber"], FONT_SMALL_BOLD).pack(anchor="w")
            if ready:
                label(card, get_text("เตรียมแล้ว ✔", "Ready ✔"), COLORS["card"], COLORS["accent"], FONT_SMALL_BOLD).pack(side="right")
            else:
                flat_button(card, get_text("เตรียม", "Prepare"),
                            lambda k=key: self.act(realm.do_prepare(k), get_text(f"เตรียม{tr(COUNTERS[k]['name'])}แล้ว",
                                                                                f"{tr(COUNTERS[k]['name'])} ready")),
                            COLORS["accent"], COLORS["accent_dark"], fg=COLORS["ink"], size=10).pack(side="right")

    def draw_shrine(self, parent: tk.Widget) -> None:
        """แท็บศาลเจ้าที่: ความแค้น ผีเพื่อน บนบาน แก้บน และทำบุญ"""
        bg = COLORS["panel"]
        state = storage.state
        section_title(parent, get_text("ศาลเจ้าที่", "SPIRIT SHRINE"), bg).pack(anchor="w")
        top = tk.Frame(parent, bg=bg)
        top.pack(fill="x", pady=(6, 0))
        picture(top, sprite("clinic", 4)).pack(side="left")
        info = tk.Frame(top, bg=bg)
        info.pack(side="left", fill="x", expand=True, padx=12)
        label(info, get_text(f"ความแค้นของมิติผี {state['grudge']}/{MAX_GRUDGE}", f"Realm grudge {state['grudge']}/{MAX_GRUDGE}"),
              bg, COLORS["red"] if state["grudge"] >= 5 else COLORS["text"], FONT_BOLD).pack(anchor="w")
        meter(info, state["grudge"] / MAX_GRUDGE, COLORS["red"]).pack(fill="x", pady=(4, 2))
        label(info, get_text("ยิ่งแค้น ผียิ่งมาเยอะ และลางยิ่งหลอกบ่อย (ป่าช้า ไล่คนออก ผิดคำบน = แค้นเพิ่ม)",
                             "More grudge = bigger hordes and lying omens (graveyard, exile, broken vows)"),
              bg, COLORS["muted"], FONT_SMALL, wraplength=320, justify="left").pack(anchor="w")
        label(parent, get_text("ผีเพื่อนที่ยังวนเวียน: ", "Restless friends: ") + (", ".join(state["fallen"]) or "-"),
              bg, COLORS["amber"] if state["fallen"] else COLORS["muted"], FONT_SMALL_BOLD).pack(anchor="w", pady=(8, 0))

        section_title(parent, get_text("บนบานศาลกล่าว", "MAKE A VOW"), bg, 11).pack(anchor="w", pady=(12, 0))
        if state["vow"]:
            vow = VOWS[state["vow"]["wish"]]
            card = tk.Frame(parent, bg=COLORS["red_dark"], padx=10, pady=8)
            card.pack(fill="x", pady=(8, 0))
            label(card, get_text(f"บนไว้: {tr(vow['name'])} — ต้องแก้บนภายในวันที่ {state['vow']['due']}",
                                 f"Vow: {tr(vow['name'])} — repay by day {state['vow']['due']}"),
                  COLORS["red_dark"], "white", FONT_BOLD, wraplength=300, justify="left").pack(side="left")
            flat_button(card, get_text("แก้บน: ", "Repay: ") + realm.cost_label(vow["repay"]),
                        lambda: self.act(realm.do_repay(), get_text("แก้บนเรียบร้อย", "Vow repaid")),
                        COLORS["accent"], COLORS["accent_dark"], fg=COLORS["ink"], size=9).pack(side="right")
        else:
            for key, vow in VOWS.items():
                card = tk.Frame(parent, bg=COLORS["card"], padx=10, pady=8)
                card.pack(fill="x", pady=(8, 0))
                text_box = tk.Frame(card, bg=COLORS["card"])
                text_box.pack(side="left", fill="x", expand=True)
                label(text_box, tr(vow["name"]), COLORS["card"], font=FONT_BOLD).pack(anchor="w")
                label(text_box, tr(vow["about"]), COLORS["card"], COLORS["accent"], FONT_SMALL).pack(anchor="w")
                label(text_box, get_text(f"ต้องแก้บน {realm.cost_label(vow['repay'])} ภายใน {VOW_DAYS} วัน",
                                         f"Repay {realm.cost_label(vow['repay'])} within {VOW_DAYS} days"),
                      COLORS["card"], COLORS["amber"], FONT_SMALL).pack(anchor="w")
                flat_button(card, get_text("บน", "Vow"),
                            lambda k=key: self.act(realm.do_vow(k), tr(VOWS[k]["about"])),
                            COLORS["accent"], COLORS["accent_dark"], fg=COLORS["ink"], size=10).pack(side="right")

        section_title(parent, get_text("ทำบุญอุทิศส่วนกุศล", "MAKE MERIT"), bg, 11).pack(anchor="w", pady=(12, 0))
        card = tk.Frame(parent, bg=COLORS["card"], padx=10, pady=8)
        card.pack(fill="x", pady=(8, 0))
        label(card, get_text(f"ความแค้น -2 และส่งผีเพื่อน 1 ตนไปสู่สุคติ (วันละครั้ง)\n{realm.cost_label(MERIT_COST)}",
                             f"Grudge -2 and lay one friend to rest (once a day)\n{realm.cost_label(MERIT_COST)}"),
              COLORS["card"], COLORS["text"], FONT_SMALL, justify="left").pack(side="left")
        if state["merit_day"] == state["day"]:
            label(card, get_text("วันนี้ทำแล้ว ✔", "Done today ✔"), COLORS["card"], COLORS["accent"], FONT_SMALL_BOLD).pack(side="right")
        else:
            flat_button(card, get_text("ทำบุญ", "Make merit"), self.merit, COLORS["accent"], COLORS["accent_dark"],
                        fg=COLORS["ink"], size=10).pack(side="right")

    def merit(self) -> None:
        if not self.playing():
            return
        laid = storage.state["fallen"][0] if storage.state["fallen"] else None
        error = realm.do_merit()
        done = get_text("ทำบุญแล้ว ความแค้นลดลง", "Merit made. The grudge eases.")
        if laid:
            done += get_text(f"  ผีของ{laid}ไปสู่สุคติแล้ว", f"  {laid}'s spirit is at peace.")
        self.act(error, done)

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
            self.say(get_text(f"{name} เข้ามาแล้ว... แต่เงาไม่ขยับตามตัว! ต้องได้น้ำมนต์วันนี้ ไม่งั้นจะกลายเป็นผีคืนนี้!",
                              f"{name} is in... but their shadow doesn't move! Holy water today or they become a ghost tonight!"), COLORS["red"])
        else:
            self.say(get_text(f"{name} เข้ามาอยู่ในศาลาแล้ว!", f"{name} joined the sala!"), COLORS["accent"])
        if not error and wanderer.get("ticket"):
            self.say(get_text(f"{name} ยื่นชิ้นส่วนตั๋วบ้านผีสิงให้! ({storage.state['tickets']}/{TICKET_PIECES})",
                              f"{name} hands you a ticket piece! ({storage.state['tickets']}/{TICKET_PIECES})"), COLORS["accent"])
        self.refresh()

    def reject(self) -> None:
        if not self.playing():
            return
        survivors.do_reject_wanderer()
        self.say(get_text("คุณปิดประตู... เขาเดินจากไป", "You close the gate... they walk away."), COLORS["muted"])
        self.refresh()

    def inspect(self) -> None:
        """เลือกคนว่าง 1 คนไปส่องดูเงาคนแปลกหน้า"""
        if not self.playing():
            return
        free = [p for p in storage.state["survivors"] if p["job"] is None]
        if not free:
            self.say(get_text("ไม่มีใครว่างวันนี้ ทุกคนมีงานแล้ว",
                              "No one is free today. Everyone already has a job."), COLORS["red"])
            return
        chosen = {"person": None}
        dialog = open_dialog(self.root, get_text("ใครจะไปส่องดูเงา?", "Who checks the shadow?"), COLORS["blue"])

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
            self.say(get_text(f"{person['name']} ส่องดูเงาของ {wanderer['name']}: เงาไม่ขยับตามตัว! ถูกผีสิง",
                              f"{person['name']} checks {wanderer['name']}: their shadow doesn't move! Possessed"), COLORS["red"])
        else:
            self.say(get_text(f"{person['name']} ส่องดูเงาของ {wanderer['name']}: เงาปกติ ปลอดภัย",
                              f"{person['name']} checks {wanderer['name']}: normal shadow, safe"), COLORS["accent"])
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
        if not ask_confirm(self.root, get_text("ไล่ออกจากศาลา", "Exile"),
                           get_text(f"ไล่ {person['name']} ออกไปในความมืดของมิติผี? เขาจะไม่กลับมาอีก"
                                    + ("\n(ผีจะแค้นเพิ่ม และเขาอาจกลับมาเป็นผี)" if realm.advanced() else ""),
                                    f"Send {person['name']} out into the dark of the ghost realm? They won't come back."
                                    + ("\n(The grudge grows, and they may return as a ghost)" if realm.advanced() else ""))):
            return
        error = survivors.do_exile(person)
        self.say(error or get_text(f"{person['name']} เดินหายไปในความมืดของมิติผี...",
                                   f"{person['name']} vanishes into the dark of the ghost realm..."),
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
        """
        หน้าต่างรายงานกลางคืน: ค่อยๆ แสดงทีละบรรทัด
        ตอนผีบุก ฝูงผีลอยเข้ามาจากขวา มีแถบพลังป้องกันสู้กับพลังผี และหน้าต่างสั่นถ้าผีบุกเข้าศาลาได้
        """
        dialog = open_dialog(self.root, get_text(f"คืนที่ {night}", f"NIGHT {night}"), COLORS["amber"])
        stage = tk.Frame(dialog, bg=COLORS["panel"], padx=28)
        stage.pack(fill="x")
        body = tk.Frame(dialog, bg=COLORS["panel"], padx=28)
        body.pack(fill="both")
        footer = tk.Frame(dialog, bg=COLORS["panel"])
        footer.pack(pady=(14, 18))
        lines = list(result["lines"])
        flyers = []              # ผีที่กำลังลอยเข้ามา: [canvas, item, x, target_x, y, phase]
        anim = {"frame": 0, "base": None}

        def show_horde(horde: list, line: str) -> None:
            """วาดฝูงผี (ภาพใหญ่ชนิดละ 1 ตัว + จำนวนจริง) และแถบพลังป้องกัน vs พลังผี"""
            canvas = tk.Canvas(stage, width=640, height=150, bg=COLORS["screen"], highlightthickness=0)
            canvas.pack(anchor="w")
            canvas.create_oval(250, 6, 390, 146, fill=COLORS["moon"], width=0)
            step = 600 / len(horde)
            for index, (level, count) in enumerate(horde):
                x = 20 + index * step + step / 2 - 20
                image = sprite(ZOMBIE_SPRITES[level - 1], 8 if level == 5 else 6)
                item = canvas.create_image(720 + x, 140, image=image, anchor="s")
                flyers.append([canvas, item, 720 + x, x, 140, random.randrange(100)])
                canvas.create_text(x + 50, 130, text=f"x{count}", fill=COLORS["puppet"], font=FONT_BIG, anchor="w")
            match = re.search(r"(\d+) vs \D*(\d+)", line)
            if not match:
                return
            power, guard = int(match.group(1)), int(match.group(2))
            row = tk.Frame(stage, bg=COLORS["panel"])
            row.pack(fill="x", pady=(2, 10))
            label(row, get_text(f"ป้องกัน {guard}", f"Defense {guard}"), COLORS["panel"], COLORS["accent"],
                  FONT_SMALL_BOLD).pack(side="left")
            label(row, get_text(f"ผี {power}", f"Ghosts {power}"), COLORS["panel"], COLORS["red"],
                  FONT_SMALL_BOLD).pack(side="right")
            bar = tk.Canvas(row, width=480, height=10, bg=COLORS["disabled"], highlightthickness=0)
            bar.pack(side="left", padx=10, expand=True)
            split = 480 * guard / max(guard + power, 1)
            bar.create_rectangle(0, 0, split, 10, fill=COLORS["accent"], width=0)
            bar.create_rectangle(split, 0, 480, 10, fill=COLORS["red"], width=0)

        def fly() -> None:
            """ผีค่อยๆ ลอยเข้าที่ แล้วลอยขึ้นลงต่อไปเรื่อยๆ"""
            if not dialog.winfo_exists():
                return
            anim["frame"] += 1
            for entry in flyers:
                canvas, item, x, target, y, phase = entry
                entry[2] = x + (target - x) * 0.18
                canvas.coords(item, entry[2], y + math.sin((anim["frame"] + phase) / 7) * 5)
            dialog.after(ANIM_MS, fly)

        def shake(step: int = 0) -> None:
            """หน้าต่างสั่นตอนผีบุกเข้าศาลา"""
            offsets = [-12, 12, -9, 9, -5, 5, -2, 0]
            if not dialog.winfo_exists() or step >= len(offsets):
                return
            if anim["base"] is None:
                anim["base"] = (dialog.winfo_x(), dialog.winfo_y())
            x, y = anim["base"]
            dialog.geometry(f"+{x + offsets[step]}+{y}")
            dialog.after(40, shake, step + 1)

        def show_next(index: int = 0) -> None:
            if not dialog.winfo_exists():
                return
            if index >= len(lines):
                finish()
                return
            line = lines[index]
            horde = horde_counts(line)
            if horde:
                show_horde(horde, line)
            if "✖" in line:
                shake()
            label(body, pretty(line), COLORS["panel"], line_color(line), FONT, wraplength=620,
                  justify="left", anchor="w").pack(anchor="w", pady=1)
            dialog.after(NIGHT_LINE_DELAY, show_next, index + 1)

        def finish() -> None:
            state = storage.state
            if result["status"] == "won":
                saved = len(day.rescued())
                stars, title = day.ending_grade(saved, result["early"])
                if result["early"]:
                    label(body, get_text(f"ตั๋วครบ {TICKET_PIECES} ชิ้น! ประตูบ้านผีสิงเปิดออกก่อนกำหนด (ดาวพิเศษ +1)",
                                         f"All {TICKET_PIECES} ticket pieces! The haunted-house door opens early (bonus star)"),
                          COLORS["panel"], COLORS["amber"], FONT_BOLD).pack(anchor="w", pady=(14, 0))
                label(body, get_text(f"ประตูมิติเปิดแล้ว! พากลับโลกมนุษย์ได้ {saved} คน",
                                     f"The portal opens! {saved} survivor(s) make it home"), COLORS["panel"],
                      COLORS["accent"], FONT_BIG).pack(anchor="w", pady=(14, 0))
                left = len(state["survivors"]) - saved
                if left:
                    label(body, get_text(f"(คนที่ถูกผีสิง {left} คนผ่านประตูมิติไม่ได้...)",
                                         f"({left} possessed survivor(s) could not pass through...)"),
                          COLORS["panel"], COLORS["red"], FONT_SMALL).pack(anchor="w")
                label(body, "★" * stars + "☆" * (3 - stars), COLORS["panel"], COLORS["amber"], FONT_HUGE).pack(pady=(8, 0))
                label(body, title, COLORS["panel"], font=FONT_BIG).pack()
            elif result["status"] == "lost":
                label(body, get_text("ศาลาเงียบงัน... ไม่มีใครได้กลับบ้าน", "The sala falls silent... No one made it home."),
                      COLORS["panel"], COLORS["red"], FONT_BIG).pack(anchor="w", pady=(14, 0))
            else:
                label(body, get_text(f"เช้าวันที่ {state['day']}/{storage.goal_day()}", f"Morning of day {state['day']}/{storage.goal_day()}"),
                      COLORS["panel"], COLORS["accent"], FONT_BOLD).pack(anchor="w", pady=(12, 0))
                if realm.omen_text():
                    label(body, realm.omen_text(), COLORS["panel"], COLORS["amber"], FONT_SMALL_BOLD, wraplength=620,
                          justify="left").pack(anchor="w")
                if state["wanderer"]:
                    label(body, get_text(f"มีคนมาขอเข้าศาลาที่ประตู: {state['wanderer']['name']}",
                                         f"Someone is at the gate: {state['wanderer']['name']}"),
                          COLORS["panel"], COLORS["blue"], FONT_SMALL_BOLD).pack(anchor="w")
            flat_button(footer, get_text("ตกลง", "OK"), dialog.destroy, COLORS["accent"], COLORS["accent_dark"],
                        fg=COLORS["ink"], padx=30).pack()
            dialog.bind("<Return>", lambda event: dialog.destroy())

        dialog.minsize(700, 0)
        dialog.after(250, show_next)
        fly()
        wait_dialog(self.root, dialog, footer)

    def new_game(self) -> None:
        state = storage.state
        if state["status"] == "playing" and state["day"] > 1 and \
                not ask_confirm(self.root, get_text("เริ่มเกมใหม่", "New Game"),
                                get_text(f"มีเกมค้างอยู่ (วันที่ {state['day']}) เริ่มใหม่เลย? ความคืบหน้าเดิมจะหาย",
                                         f"You're on day {state['day']}. Start over? Progress will be lost.")):
            return
        level = self.choose_difficulty()
        if level is None:
            return
        storage.new_game(level)
        self.tab = "gate"
        self.say(get_text("เริ่มเกมใหม่แล้ว ขอให้รอดกลับบ้าน!", "A fresh start. Make it home!"), COLORS["accent"])
        self.refresh()
        self.show_intro()

    def choose_difficulty(self):
        """หน้าต่างเลือกระดับความยาก คืนค่า key หรือ None"""
        chosen = {"key": None}
        dialog = open_dialog(self.root, get_text("เลือกระดับความยาก", "CHOOSE DIFFICULTY"), COLORS["accent"])

        def pick(key: str) -> None:
            chosen["key"] = key
            dialog.destroy()

        for key, info in DIFFICULTIES.items():
            color = COLORS["red_dark"] if key == "nightmare" else COLORS["card"]
            duration = get_text(f"{info['days']} วัน", f"{info['days']} days")
            flat_button(dialog, f"{tr(info['name'])} ({duration}) — {tr(info['about'])}", lambda k=key: pick(k), color,
                        COLORS["card_hover"], size=11, anchor="w").pack(fill="x", padx=28, pady=3)
        cancel = flat_button(dialog, get_text("ยกเลิก", "Cancel"), dialog.destroy, COLORS["panel"])
        cancel.pack(pady=(10, 18))
        wait_dialog(self.root, dialog, cancel)
        return chosen["key"]

    def show_help(self) -> None:
        """หน้าต่างวิธีเล่น (ข้อความเดียวกับ Terminal)"""
        dialog = open_dialog(self.root, get_text("วิธีเล่น", "HOW TO PLAY"), COLORS["accent"])
        # เก็บย่อหน้าเดิมไว้ (tk_safe ตัดช่องว่างหัวบรรทัดออก)
        text = "\n".join(" " * (len(line) - len(line.lstrip())) + tk_safe(line)
                         for line in menu.how_to_play_text().split("\n"))
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
    if "--legacy" not in sys.argv:
        from talung_ui.main import main as open_redesigned_game
        open_redesigned_game()
        return
    storage.load_game()
    root = tk.Tk()
    app = ShelterApp(root)
    # เกมใหม่ที่ยังไม่ได้เริ่มเล่น: เปิดด้วยหน้าเปิดเรื่อง
    state = storage.state
    if state["status"] == "playing" and state["day"] == 1 and all(p["job"] is None for p in state["survivors"]):
        root.after(200, app.show_intro)
    root.protocol("WM_DELETE_WINDOW", lambda: (storage.save_game(), root.destroy()))
    root.mainloop()


if __name__ == "__main__":
    main()
