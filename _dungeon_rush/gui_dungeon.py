#!/usr/bin/env python3
"""
GUI Dungeon Module - DUNGEON RUSH (Bonus)
แท็บ "ดันเจี้ยน" (เลือกชั้น สอดแนม โอกาสชนะ และภาพการต่อสู้) และแท็บ "บันทึก" (สถิติ)
การต่อสู้ใช้ dungeon.fight / dungeon.apply_battle ตัวเดียวกับเวอร์ชัน Terminal
Dungeon and log tabs of the GUI.
"""

import random
import tkinter as tk

from language import get_text
from data import MONSTERS, ELEMENTS, tr
import dungeon
import heroes
import items
import storage
from sprites import sprite, MONSTER_SPRITES
from gui_theme import (picture, COLORS, ELEMENT_COLORS, FONT, FONT_SMALL, FONT_SMALL_BOLD,
                       FONT_BOLD, FONT_BIG, FONT_HUGE, ScrollableFrame, badge, flat_button, label, meter,
                       section_title, set_meter, tk_safe, type_font)

# ความเร็วในการเล่นภาพการต่อสู้ (มิลลิวินาทีต่อบรรทัด)
BATTLE_SPEED = 260

# สีของข้อความในบันทึกการต่อสู้ตามประเภทเหตุการณ์ (ดู dungeon.fight)
EVENT_STYLE = {
    "round": (COLORS["muted"], FONT_SMALL_BOLD),
    "hit": (COLORS["text"], FONT),
    "weak": (COLORS["gold"], FONT_BOLD),
    "immune": (COLORS["muted"], ("TkDefaultFont", 11, "italic")),
    "heal": (COLORS["green"], FONT),
    "potion": (COLORS["blue"], FONT),
    "monster": ("#e8806f", FONT),
    "ko": (COLORS["red"], FONT_BOLD),
    "win": (COLORS["green"], FONT_BIG),
    "lose": (COLORS["red"], FONT_BIG),
}


def chance_color(chance: float) -> str:
    """สีของโอกาสชนะ: เขียว >= 70%, ทอง >= 40%, แดง < 40%"""
    if chance >= 70:
        return COLORS["green"]
    return COLORS["gold"] if chance >= 40 else COLORS["red"]


def element_chip(parent: tk.Widget, prefix: str, element: str, bg: str) -> None:
    """ป้ายธาตุสีๆ เช่น '✦ แพ้ทาง ◆ น้ำแข็ง'"""
    label(parent, f"{prefix} ◆ {tr(ELEMENTS[element])}", bg, ELEMENT_COLORS[element],
          FONT_SMALL_BOLD).pack(anchor="w", pady=1)


class DungeonView(tk.Frame):
    """แท็บดันเจี้ยน: แผนที่ 5 ชั้น ข้อมูลศัตรู การจับคู่ธาตุกับทีม โอกาสชนะ และการต่อสู้"""

    def __init__(self, parent: tk.Widget, app) -> None:
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app
        self.selected = None          # ชั้นที่เลือกดูอยู่

    # ---------- หน้าเตรียมตัว ----------

    def render(self) -> None:
        """วาดแท็บใหม่ (แผนที่ + ข้อมูลศัตรูของชั้นที่เลือก)"""
        if self.app.busy:
            return
        for widget in self.winfo_children():
            widget.destroy()

        deepest = min(storage.state["floor"], len(MONSTERS))
        if self.selected is None or self.selected > deepest:
            self.selected = deepest

        self.render_map(deepest)
        body = tk.Frame(self, bg=COLORS["bg"])
        body.pack(fill="both", expand=True, pady=(12, 0))
        self.render_monster(body)
        self.render_matchup(body)

    def render_map(self, deepest: int) -> None:
        """แผนที่ดันเจี้ยน 5 ชั้น (คลิกชั้นที่ปลดล็อกแล้วเพื่อดู)"""
        row = tk.Frame(self, bg=COLORS["bg"])
        row.pack(fill="x")
        row.columnconfigure(tuple(range(len(MONSTERS))), weight=1, uniform="floor")
        for index, monster in enumerate(MONSTERS):
            floor = index + 1
            unlocked = floor <= deepest
            selected = floor == self.selected
            bg = COLORS["card"] if unlocked else COLORS["panel"]
            tile = tk.Frame(row, bg=bg, padx=8, pady=8, highlightthickness=3,
                            highlightbackground=COLORS["gold"] if selected else bg,
                            cursor="hand2" if unlocked else "")
            tile.grid(row=0, column=index, sticky="nsew", padx=3)

            if unlocked:
                picture(tile, sprite(MONSTER_SPRITES[index], 3), bg).pack()
            else:
                badge(tile, "?", COLORS["disabled"], bg, 48).pack()
            label(tile, get_text(f"ชั้น {floor}", f"FLOOR {floor}"), bg, COLORS["muted"], FONT_SMALL_BOLD).pack()
            label(tile, tr(monster["name"]) if unlocked else "???", bg,
                  font=FONT_BOLD if unlocked else FONT).pack()
            if floor < storage.state["floor"]:
                status, status_color = get_text("✔ ผ่านแล้ว", "✔ cleared"), COLORS["green"]
            elif unlocked:
                status, status_color = get_text("★ ชั้นใหม่", "★ new"), COLORS["gold"]
            else:
                status, status_color = get_text("ยังไม่ปลดล็อก", "locked"), COLORS["muted"]
            label(tile, status, bg, status_color, FONT_SMALL_BOLD).pack()

            if unlocked:
                for widget in [tile] + list(tile.winfo_children()):
                    widget.bind("<Button-1>", lambda event, f=floor: self.select(f))

    def render_monster(self, parent: tk.Widget) -> None:
        """การ์ดข้อมูลศัตรูของชั้นที่เลือก"""
        index = self.selected - 1
        monster = MONSTERS[index]
        bg = COLORS["panel"]
        card = tk.Frame(parent, bg=bg, width=330, padx=20, pady=16)
        card.pack(side="left", fill="y")
        card.pack_propagate(False)

        picture(card, sprite(MONSTER_SPRITES[index], 8), bg).pack(pady=(0, 6))
        label(card, tr(monster["name"]), bg, font=("TkDefaultFont", 18, "bold")).pack()
        attacks = get_text(f"โจมตี {monster['attacks']} ครั้ง/เทิร์น", f"{monster['attacks']} attack(s) per round")
        label(card, attacks, bg, COLORS["muted"], FONT_SMALL).pack(pady=(0, 10))

        stats = tk.Frame(card, bg=bg)
        stats.pack(fill="x")
        for column, (name, value, stat_color) in enumerate((("HP", monster["hp"], COLORS["green"]),
                                                            ("ATK", monster["atk"], COLORS["red"]),
                                                            ("DEF", monster["def"], COLORS["blue"]))):
            stats.columnconfigure(column, weight=1)
            box = tk.Frame(stats, bg=COLORS["card"], pady=6)
            box.grid(row=0, column=column, sticky="nsew", padx=2)
            label(box, name, COLORS["card"], COLORS["muted"], FONT_SMALL_BOLD).pack()
            label(box, str(value), COLORS["card"], stat_color, FONT_BIG).pack()

        traits = tk.Frame(card, bg=bg)
        traits.pack(fill="x", pady=(12, 0))
        if monster["weak"]:
            element_chip(traits, get_text("✦ แพ้ทาง (x2)", "✦ Weak to (x2)"), monster["weak"], bg)
        if monster["immune"]:
            element_chip(traits, get_text("⚠ ตีไม่เข้า", "⚠ Immune to"), monster["immune"], bg)
        if not monster["weak"] and not monster["immune"]:
            label(traits, get_text("ไม่มีจุดอ่อนพิเศษ", "No special weakness"), bg, COLORS["muted"], FONT_SMALL).pack(anchor="w")

        gold = dungeon.reward_gold(self.selected)
        replay = self.selected < storage.state["floor"]
        reward = get_text(f"รางวัล: ◉ {gold} ทอง  ·  {monster['xp']} XP", f"Reward: ◉ {gold} gold  ·  {monster['xp']} XP")
        label(card, reward, bg, COLORS["gold"], FONT_BOLD).pack(anchor="w", pady=(12, 0))
        if replay:
            label(card, get_text("(ชั้นที่ผ่านแล้ว ได้ทองครึ่งเดียว)", "(cleared floor: half gold)"), bg,
                  COLORS["muted"], FONT_SMALL).pack(anchor="w")

    def render_matchup(self, parent: tk.Widget) -> None:
        """ทีมเทียบกับศัตรู: ธาตุของแต่ละคน โอกาสชนะ และปุ่มต่อสู้"""
        monster = MONSTERS[self.selected - 1]
        bg = COLORS["panel"]
        panel = tk.Frame(parent, bg=bg, padx=20, pady=16)
        panel.pack(side="left", fill="both", expand=True, padx=(12, 0))

        section_title(panel, get_text("ทีมของคุณ vs ศัตรู", "YOUR PARTY vs ENEMY"), bg).pack(anchor="w", pady=(0, 6))
        for hero in storage.state["heroes"]:
            row = tk.Frame(panel, bg=COLORS["card"], padx=10, pady=6)
            row.pack(fill="x", pady=2)
            picture(row, sprite(hero["class"], 2), COLORS["card"]).pack(side="left")
            info = tk.Frame(row, bg=COLORS["card"])
            info.pack(side="left", padx=8)
            label(info, hero["name"], COLORS["card"], font=FONT_BOLD).pack(anchor="w")
            label(info, f"HP {hero['hp']}/{hero['max_hp']}   ATK {heroes.hero_attack(hero)}   DEF {heroes.hero_defense(hero)}",
                  COLORS["card"], COLORS["muted"], FONT_SMALL).pack(anchor="w")

            element = heroes.hero_element(hero)
            if element == monster["immune"]:
                note, note_color = get_text("⚠ ตีไม่เข้า!", "⚠ can't hurt it!"), COLORS["red"]
            elif element == monster["weak"]:
                note, note_color = get_text("✦ แพ้ทาง x2!", "✦ weakness x2!"), COLORS["gold"]
            else:
                note, note_color = "", COLORS["muted"]
            label(row, note, COLORS["card"], note_color, FONT_SMALL_BOLD, width=14, anchor="e").pack(side="right")
            label(row, f"◆ {tr(ELEMENTS[element])}", COLORS["card"], ELEMENT_COLORS[element],
                  FONT_SMALL_BOLD).pack(side="right", padx=8)

        label(panel, get_text(f"ยาในกระเป๋า: {items.count_potions()} (ดื่มอัตโนมัติเมื่อ HP ต่ำกว่า 40%)",
                              f"Potions in bag: {items.count_potions()} (drunk automatically below 40% HP)"),
              bg, COLORS["muted"], FONT_SMALL).pack(anchor="w", pady=(6, 0))

        # โอกาสชนะจากการจำลอง (Monte Carlo)
        chance = dungeon.win_chance(monster)
        box = tk.Frame(panel, bg=bg)
        box.pack(fill="x", pady=(14, 0))
        label(box, get_text("โอกาสชนะโดยประมาณ", "ESTIMATED WIN CHANCE"), bg, COLORS["muted"], FONT_SMALL_BOLD).pack(anchor="w")
        label(box, f"{chance:.0f}%", bg, chance_color(chance), FONT_HUGE).pack(anchor="w")
        meter(box, chance / 100, chance_color(chance), bg, 12).pack(fill="x")
        label(box, get_text(f"(จำลองการต่อสู้ {dungeon.SIMULATIONS} ครั้ง)", f"(from {dungeon.SIMULATIONS} simulated battles)"),
              bg, COLORS["muted"], FONT_SMALL).pack(anchor="w", pady=(2, 0))
        if chance < 50:
            label(box, get_text("คำแนะนำ: ใช้อาวุธธาตุที่ศัตรูแพ้ทาง ซื้อเกราะ/ยา พักที่โรงเตี๊ยม หรือฝึกที่ชั้นก่อนๆ",
                                "Tip: use its weak element, buy armor/potions, rest, or train on earlier floors."),
                  bg, COLORS["gold"], FONT_SMALL, wraplength=520, justify="left").pack(anchor="w", pady=(6, 0))

        text = get_text("⚔  เข้าต่อสู้!", "⚔  FIGHT!")
        flat_button(panel, text, self.start_battle, COLORS["red"], COLORS["red_dark"], size=16,
                    pady=10).pack(fill="x", side="bottom")

    def select(self, floor: int) -> None:
        """คลิกเลือกชั้นบนแผนที่"""
        self.selected = floor
        self.render()

    # ---------- การต่อสู้ ----------

    def start_battle(self) -> None:
        """จำลองการต่อสู้ นำผลไปใช้กับข้อมูลจริงทันที แล้วเล่นภาพทีละเหตุการณ์"""
        floor = self.selected
        monster = MONSTERS[floor - 1]
        party = [dict(hero) for hero in storage.state["heroes"]]   # ค่าก่อนสู้ ไว้วาดแถบ HP

        result = dungeon.fight(monster, random.Random(), show=False, record=True)
        messages = dungeon.apply_battle(floor, result)

        self.app.busy = True
        for widget in self.winfo_children():
            widget.destroy()

        # แถบ HP ของมอนสเตอร์
        bg = COLORS["panel"]
        top = tk.Frame(self, bg=bg, padx=20, pady=14)
        top.pack(fill="x")
        picture(top, sprite(MONSTER_SPRITES[floor - 1], 5), bg).pack(side="left")
        info = tk.Frame(top, bg=bg)
        info.pack(side="left", fill="x", expand=True, padx=14)
        label(info, tr(monster["name"]), bg, font=FONT_BIG).pack(anchor="w")
        monster_meter = meter(info, 1.0, COLORS["red"], bg, 14)
        monster_meter.pack(fill="x", pady=(4, 0))
        monster_text = label(info, f"HP {monster['hp']}/{monster['hp']}", bg, COLORS["muted"], FONT_SMALL_BOLD)
        monster_text.pack(anchor="e")

        # แถบ HP ของฮีโร่
        heroes_row = tk.Frame(self, bg=COLORS["bg"])
        heroes_row.pack(fill="x", pady=8)
        heroes_row.columnconfigure(tuple(range(len(party))), weight=1, uniform="hero")
        hero_meters = []
        for column, hero in enumerate(party):
            box = tk.Frame(heroes_row, bg=COLORS["card"], padx=10, pady=6)
            box.grid(row=0, column=column, sticky="nsew", padx=3)
            label(box, hero["name"], COLORS["card"], font=FONT_BOLD).pack(anchor="w")
            bar = meter(box, hero["hp"] / hero["max_hp"], COLORS["green"], COLORS["card"], 10)
            bar.pack(fill="x", pady=2)
            text = label(box, f"{hero['hp']}/{hero['max_hp']}", COLORS["card"], COLORS["muted"], FONT_SMALL_BOLD)
            text.pack(anchor="e")
            hero_meters.append((bar, text, hero["max_hp"]))

        # แถบล่าง (ปุ่มข้าม / ผลลัพธ์) pack ก่อนบันทึก เพื่อไม่ให้บันทึกที่ยาวดันจนหลุดจอ
        bottom = tk.Frame(self, bg=COLORS["bg"])
        bottom.pack(side="bottom", fill="x", pady=(8, 0))

        # บันทึกการต่อสู้
        log_frame = tk.Frame(self, bg=COLORS["panel"])
        log_frame.pack(fill="both", expand=True)
        log = tk.Text(log_frame, bg=COLORS["panel"], fg=COLORS["text"], font=FONT, bd=0, padx=16, pady=10,
                      highlightthickness=0, wrap="word", cursor="arrow", spacing1=2)
        log.pack(fill="both", expand=True)
        for kind, (fg, font) in EVENT_STYLE.items():
            log.tag_config(kind, foreground=fg, font=font)
        log.tag_config("round", spacing1=10)

        battle = {"index": 0, "done": False}

        def show_event(event: dict) -> None:
            """แสดงเหตุการณ์ 1 บรรทัด และอัปเดตแถบ HP ตาม HP ณ ตอนนั้น"""
            log.config(state="normal")
            log.insert("end", tk_safe(event["text"]).strip() + "\n", event["kind"])
            log.config(state="disabled")
            log.see("end")
            set_meter(monster_meter, event["monster_hp"] / monster["hp"])
            monster_text.config(text=f"HP {event['monster_hp']}/{monster['hp']}")
            for (bar, text, max_hp), hp in zip(hero_meters, event["hp"]):
                ratio = hp / max_hp
                set_meter(bar, ratio, COLORS["green"] if ratio > 0.5 else (COLORS["gold"] if ratio > 0.25 else COLORS["red"]))
                text.config(text=f"{hp}/{max_hp}")

        def finish() -> None:
            """จบการต่อสู้: แสดงผลลัพธ์และปุ่มกลับ"""
            if battle["done"] or not self.winfo_exists():
                return
            battle["done"] = True
            while battle["index"] < len(result["events"]):
                show_event(result["events"][battle["index"]])
                battle["index"] += 1
            for widget in bottom.winfo_children():
                widget.destroy()

            title = get_text("ชนะ!", "VICTORY!") if result["won"] else get_text("พ่ายแพ้...", "DEFEAT...")
            color = COLORS["green"] if result["won"] else COLORS["red"]
            banner = tk.Frame(bottom, bg=COLORS["panel"], padx=16, pady=10, highlightthickness=2,
                              highlightbackground=color)
            banner.pack(fill="x")
            label(banner, title, COLORS["panel"], color, type_font(title, 20)).pack(side="left")
            notes = tk.Frame(banner, bg=COLORS["panel"])
            notes.pack(side="left", padx=20)
            for message in messages:
                label(notes, message.strip(), COLORS["panel"], font=FONT_BOLD).pack(anchor="w")
            flat_button(banner, get_text("กลับเมือง", "BACK TO TOWN"), self.end_battle, COLORS["gold"],
                        COLORS["gold_dark"], fg=COLORS["ink"]).pack(side="right")
            self.app.notify(messages[0] if messages else title, ok=result["won"])

        def play() -> None:
            """เล่นเหตุการณ์ถัดไปทุก BATTLE_SPEED มิลลิวินาที"""
            if battle["done"] or not self.winfo_exists():
                return
            if battle["index"] >= len(result["events"]):
                finish()
                return
            show_event(result["events"][battle["index"]])
            battle["index"] += 1
            self.after(BATTLE_SPEED, play)

        flat_button(bottom, get_text("ข้าม ▶▶", "SKIP ▶▶"), finish).pack(side="right")
        self.after(300, play)

    def end_battle(self) -> None:
        """กลับจากหน้าการต่อสู้"""
        self.app.busy = False
        self.selected = None
        self.app.refresh()


class LogView(tk.Frame):
    """แท็บบันทึก: สถิติการผจญภัย (ใช้ dungeon.adventure_stats ตัวเดียวกับ Terminal)"""

    def __init__(self, parent: tk.Widget, app) -> None:
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app

    def render(self) -> None:
        """วาดแท็บใหม่ทั้งหมด"""
        for widget in self.winfo_children():
            widget.destroy()
        log = storage.state["log"]
        stats = dungeon.adventure_stats()

        area = ScrollableFrame(self, COLORS["bg"])
        area.pack(fill="both", expand=True)
        page = area.inner

        section_title(page, get_text("บันทึกการผจญภัย", "ADVENTURE LOG"), COLORS["bg"], 14).pack(anchor="w")

        # ความคืบหน้า 5 ชั้น
        progress = tk.Frame(page, bg=COLORS["panel"], padx=18, pady=14)
        progress.pack(fill="x", pady=(8, 0))
        label(progress, get_text(f"ผ่านแล้ว {stats['cleared']}/{len(MONSTERS)} ชั้น",
                                 f"{stats['cleared']}/{len(MONSTERS)} floors cleared"), COLORS["panel"],
              font=FONT_BOLD).pack(anchor="w")
        row = tk.Frame(progress, bg=COLORS["panel"])
        row.pack(fill="x", pady=(8, 0))
        for index, monster in enumerate(MONSTERS):
            cleared = index < stats["cleared"]
            if cleared:
                picture(row, sprite(MONSTER_SPRITES[index], 3), COLORS["panel"]).pack(side="left", padx=4)
            else:
                badge(row, "?", COLORS["disabled"], COLORS["panel"], 48).pack(side="left", padx=4)
            if index < len(MONSTERS) - 1:
                tk.Frame(row, bg=COLORS["green"] if index + 1 < stats["cleared"] else COLORS["disabled"],
                         height=4, width=40).pack(side="left")

        # การ์ดตัวเลข
        tiles = tk.Frame(page, bg=COLORS["bg"])
        tiles.pack(fill="x", pady=10)
        data = (
            (get_text("ต่อสู้", "Battles"), log["battles"], COLORS["text"]),
            (get_text("ชนะ", "Wins"), log["wins"], COLORS["green"]),
            (get_text("แพ้", "Losses"), log["losses"], COLORS["red"]),
            (get_text("อัตราชนะ", "Win rate"), f"{stats['rate']:.0f}%", COLORS["gold"]),
            (get_text("ทองที่หาได้", "Gold earned"), log["gold_earned"], COLORS["gold"]),
            (get_text("ทองที่ใช้ไป", "Gold spent"), log["gold_spent"], COLORS["muted"]),
        )
        for column, (name, value, color) in enumerate(data):
            tiles.columnconfigure(column, weight=1, uniform="tile")
            tile = tk.Frame(tiles, bg=COLORS["panel"], padx=14, pady=10)
            tile.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 6, 0))
            label(tile, name, COLORS["panel"], COLORS["muted"], FONT_SMALL).pack(anchor="w")
            label(tile, str(value), COLORS["panel"], color, ("TkDefaultFont", 22, "bold")).pack(anchor="w")

        # สถิติฮีโร่
        records = tk.Frame(page, bg=COLORS["panel"], padx=18, pady=14)
        records.pack(fill="x")
        section_title(records, get_text("ฮีโร่เด่น", "HALL OF HEROES"), COLORS["panel"], 12).pack(anchor="w", pady=(0, 6))
        strongest, toughest, highest = stats["strongest"], stats["toughest"], stats["highest"]
        for title, hero, value in (
            (get_text("โจมตีแรงที่สุด", "Strongest"), strongest, f"ATK {heroes.hero_attack(strongest)}"),
            (get_text("อึดที่สุด", "Toughest"), toughest, f"HP {toughest['max_hp']}"),
            (get_text("เลเวลสูงสุด", "Most experienced"), highest, f"Lv.{highest['level']}"),
        ):
            row = tk.Frame(records, bg=COLORS["panel"])
            row.pack(fill="x", pady=3)
            picture(row, sprite(hero["class"], 2), COLORS["panel"]).pack(side="left")
            label(row, title, COLORS["panel"], COLORS["muted"], FONT, width=14, anchor="w").pack(side="left", padx=8)
            label(row, hero["name"], COLORS["panel"], font=FONT_BOLD).pack(side="left")
            label(row, value, COLORS["panel"], COLORS["gold"], FONT_BOLD).pack(side="right")

        power = stats["power"]
        label(page, get_text(f"พลังรวมของทีม:  ATK {power['atk']}   DEF {power['def']}   HP {power['hp']}/{power['max_hp']}",
                             f"Party total:  ATK {power['atk']}   DEF {power['def']}   HP {power['hp']}/{power['max_hp']}"),
              COLORS["bg"], COLORS["muted"], FONT_BOLD).pack(anchor="w", pady=(10, 0))
