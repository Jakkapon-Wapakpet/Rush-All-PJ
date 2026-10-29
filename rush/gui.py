#!/usr/bin/env python3
"""
GUI - GHOST REALM (มิติผี) (Bonus)
ส่วนกลางของหน้าต่าง Tkinter: การกระทำของผู้เล่น (เรียก do_* ชุดเดียวกับ Terminal)
และแท็บคืนนี้/ศาลเจ้า/บันทึก ส่วนหน้าตาหนังตะลุงอยู่ใน talung_ui/ (TalungApp สืบทอดจาก SalaApp)
Shared Tkinter game logic; the Nang Talung look lives in talung_ui/.

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

from language import get_text, set_language
from data import (RESOURCES, SKILLS, JOBS, BUILDINGS, GHOSTS, RAID_START_DAY, LOCATIONS, COUNTERS, LIGHTS, VOWS,
                  VOW_DAYS, MERIT_COST, MAX_GRUDGE, TICKET_PIECES, tr)
import sala
import day
import menu
import realm
import storage
import survivors
from gui_theme import (COLORS, FONT_SMALL, FONT_SMALL_BOLD, FONT_BOLD, ask_confirm, ask_text, flat_button, label, meter,
                       open_dialog, picture, section_title, set_button_text, tk_safe, wait_dialog)
from talung_ui.art import sprite, GHOST_SPRITES

ANIM_MS = 60             # ความถี่ของแอนิเมชัน (การ์ดคนถูกผีสิงกะพริบ) มิลลิวินาทีต่อเฟรม
TABS = ["gate", "build", "tonight", "shrine", "ghosts", "log"]
ADVANCED_TABS = {"tonight", "shrine"}   # แท็บของระบบเสริม (ระดับปกติขึ้นไป)

# ชื่องานแบบสั้นสำหรับปุ่มบนการ์ด
JOB_SHORT = {"scavenge": {"th": "หาของ", "en": "Scavenge"}, "guard": {"th": "เฝ้ายาม", "en": "Guard"},
             "heal": {"th": "น้ำมนต์", "en": "Bless"}, "rest": {"th": "พักผ่อน", "en": "Rest"}}


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
    for ghost in GHOSTS:
        line = re.sub(re.escape(ghost["icon"]) + r"(?=x\d)", tr(ghost["name"]) + " ", line)
    for info in RESOURCES.values():
        line = re.sub(re.escape(info["icon"]) + r"(?=[+-]\d)", tr(info["name"]) + " ", line)
    return tk_safe(line)


def line_color(line: str) -> str:
    """สีของบรรทัดในรายงานกลางคืน (ดูจากสัญลักษณ์ก่อนแปลงข้อความ)"""
    if wave_counts(line) or "🐯" in line:
        return COLORS["amber"]
    if any(mark in line for mark in ("ได้ผล!", " works!", "เจ้าที่คุ้มครอง", "spirit keeps watch", "🎫")):
        return COLORS["accent"]
    if any(mark in line for mark in ("✖", "🩸", "😈", "🪦", "💀", "😵", "😱", "🎭", "👤", "⚡")):
        return COLORS["red"]
    if any(mark in line for mark in ("✔", "🌀", "✚", "🎁")):
        return COLORS["accent"]
    return COLORS["text"]


def wave_counts(line: str) -> list:
    """อ่านองค์ประกอบฝูงจากบรรทัดรายงาน เช่น '👻x5 🔥x2' → [(1, 5), (2, 2)]"""
    found = []
    for ghost in GHOSTS:
        match = re.search(re.escape(ghost["icon"]) + r"x(\d+)", line)
        if match:
            found.append((ghost["level"], int(match.group(1))))
    return found


class SalaApp:
    """หน้าต่างหลักของเกม"""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.tab = "gate"
        self.message = (get_text("ยินดีต้อนรับสู่มิติผี มอบงานให้ทุกคน แล้วกดจบวัน",
                                 "Welcome to the ghost realm. Give everyone a job, then end the day."), COLORS["muted"])
        root.configure(bg=COLORS["bg"])
        self.tick = 0            # นับเฟรมแอนิเมชัน
        self.blink_cards = []    # การ์ดคนที่ถูกผีสิง (ขอบกะพริบแดง)
        self.build_layout()
        self.refresh()
        root.after(ANIM_MS, self.animate)

    def refresh(self) -> None:
        """วาดข้อมูลทั้งหมดใหม่ตามสถานะเกมปัจจุบัน"""
        self.draw_header()
        self.draw_scene()
        self.draw_people()
        self.draw_tabs()
        self.draw_footer()

    def animate(self) -> None:
        """เฟรมแอนิเมชัน: การ์ดคนถูกผีสิงกะพริบ"""
        self.tick += 1
        if self.tick % 8 == 0:
            color = COLORS["red"] if self.tick % 16 else COLORS["red_dark"]
            for card in self.blink_cards:
                if card.winfo_exists():
                    card.config(highlightbackground=color)
        self.root.after(ANIM_MS, self.animate)

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

    # ---------- แท็บด้านขวา ----------

    def switch_tab(self, key: str) -> None:
        self.tab = key
        self.draw_tabs()

    def draw_log(self, parent: tk.Widget) -> None:
        """แท็บบันทึก: สถิติ กราฟอาหาร/น้ำรายวัน และผลเกมที่ผ่านมา"""
        bg = COLORS["panel"]
        state = storage.state
        log = state["log"]
        stats = day.shelter_stats()
        section_title(parent, get_text("บันทึกศาลา", "SALA LOG"), bg).pack(anchor="w")
        rows = [
            (get_text("ผีบุก / ต้านได้", "Raids / repelled"), f"{log['raids']} / {log['repelled']}  ({stats['defense_rate']:.0f}%)"),
            (get_text("ถูกผีสิง / ไล่ผีออกได้", "Possessed / freed"), f"{log['possessed']} / {log['cured']}  ({stats['cure_rate']:.0f}%)"),
            (get_text("กลายเป็นผี / เสียชีวิต", "Became ghosts / died"), f"{log['turned']} / {log['deaths']}"),
            (get_text("คนเข้าร่วมใหม่", "Joined"), str(log["joined"])),
            (get_text("หาของได้ทั้งหมด", "Total gathered"), str(stats["gathered"])),
            (get_text("ฝูงใหญ่ที่สุด (พลัง)", "Biggest horde (power)"), str(log["biggest_wave"])),
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

    # ---------- แถบล่าง ----------

    def draw_footer(self) -> None:
        """ข้อความล่าสุด พลังป้องกัน และปุ่มหลัก"""
        self.message_label.config(text=tk_safe(self.message[0]), fg=self.message[1])
        playing = storage.state["status"] == "playing"
        # แถบพลังป้องกัน (เขียว) เทียบกับพลังผีเฉลี่ยที่อาจบุกคืนนี้ (เส้นแดง)
        guard, threat = day.defense(), day.expected_wave_power()
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
        label(parent, get_text(f"พลังป้องกันคืนนี้ {day.defense()}  ·  ผีที่อาจมา ~{day.expected_wave_power()}  ·  "
                               f"โอกาสถูกบุก {realm.raid_chance():.0%}",
                               f"Defense {day.defense()}  ·  ghosts ~{day.expected_wave_power()}  ·  "
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
            picture(card, sprite(GHOST_SPRITES[info["ghost"] - 1], 3)).pack(side="left")
            text_box = tk.Frame(card, bg=COLORS["card"])
            text_box.pack(side="left", fill="x", expand=True, padx=10)
            ghost = tr(GHOSTS[info["ghost"] - 1]["name"])
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
        picture(top, sprite("spirit_house", 4)).pack(side="left")
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
        error = sala.do_build(key)
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
        stranger = storage.state["stranger"]
        name, possessed = stranger["name"], stranger["possessed"]
        error = survivors.do_accept_stranger()
        if error:
            self.say(error, COLORS["red"])
        elif possessed:
            self.say(get_text(f"{name} เข้ามาแล้ว... แต่เงาไม่ขยับตามตัว! ต้องได้น้ำมนต์วันนี้ ไม่งั้นจะกลายเป็นผีคืนนี้!",
                              f"{name} is in... but their shadow doesn't move! Holy water today or they become a ghost tonight!"), COLORS["red"])
        else:
            self.say(get_text(f"{name} เข้ามาอยู่ในศาลาแล้ว!", f"{name} joined the sala!"), COLORS["accent"])
        if not error and stranger.get("ticket"):
            self.say(get_text(f"{name} ยื่นชิ้นส่วนตั๋วบ้านผีสิงให้! ({storage.state['tickets']}/{TICKET_PIECES})",
                              f"{name} hands you a ticket piece! ({storage.state['tickets']}/{TICKET_PIECES})"), COLORS["accent"])
        self.refresh()

    def reject(self) -> None:
        if not self.playing():
            return
        survivors.do_reject_stranger()
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
        stranger = storage.state["stranger"]
        if error:
            self.say(error, COLORS["red"])
        elif stranger["possessed"]:
            self.say(get_text(f"{person['name']} ส่องดูเงาของ {stranger['name']}: เงาไม่ขยับตามตัว! ถูกผีสิง",
                              f"{person['name']} checks {stranger['name']}: their shadow doesn't move! Possessed"), COLORS["red"])
        else:
            self.say(get_text(f"{person['name']} ส่องดูเงาของ {stranger['name']}: เงาปกติ ปลอดภัย",
                              f"{person['name']} checks {stranger['name']}: normal shadow, safe"), COLORS["accent"])
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

    def change_language(self, lang: str) -> None:
        set_language(lang)
        self.message = ("", COLORS["muted"])
        self.refresh()


def main() -> None:
    """เปิดหน้าต่างเกม (โหลดเซฟเดียวกับเวอร์ชัน Terminal)"""
    from talung_ui.main import main as open_game
    open_game()


if __name__ == "__main__":
    main()
