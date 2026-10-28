#!/usr/bin/env python3
"""
GUI - DUNGEON RUSH (Bonus)
หน้าต่างเกมด้วย Tkinter ใช้ข้อมูล กฎ และการต่อสู้ชุดเดียวกับเวอร์ชัน Terminal
Tkinter window for the game, sharing data, rules, and combat with the terminal version.

หน้าจอ:
  บน   = โลโก้ ทอง ชั้น ทีม กระเป๋า และปุ่มภาษา
  ซ้าย = การ์ดฮีโร่ (เปลี่ยนชื่อ ไล่ออก ถอดอุปกรณ์) รับสมัครฮีโร่ และโรงเตี๊ยม
  ขวา  = แท็บ ร้านค้า / กระเป๋า (gui_town.py) และ ดันเจี้ยน / บันทึก (gui_dungeon.py)
  ล่าง = แถบข้อความแจ้งผลการกระทำล่าสุด

รัน: python3 gui.py
"""

import sys

try:
    import tkinter as tk
except ImportError:
    print("Tkinter is not installed. Please run: python3 main.py")
    print("เครื่องนี้ไม่มี Tkinter กรุณาใช้: python3 main.py")
    sys.exit(1)

from language import get_text, get_language, set_language
from data import HERO_CLASSES, ELEMENTS, MONSTERS, MAX_PARTY, BAG_SIZE, tr
import heroes
import items
import storage
from gui_theme import (picture, COLORS, ELEMENT_COLORS, FONT, FONT_SMALL, FONT_SMALL_BOLD, FONT_BOLD,
                       FONT_BIG, FONT_LOGO, ScrollableFrame, add_hover, ask_confirm, ask_text,
                       flat_button, label, meter, open_dialog, section_title, tk_safe, type_font, wait_dialog)
from gui_town import ShopView, BagView
from sprites import sprite
from gui_dungeon import DungeonView, LogView


class DungeonRushApp:
    """หน้าต่างหลักของเกม"""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.busy = False             # True ระหว่างเล่นภาพการต่อสู้ (ห้ามเปลี่ยนแท็บ)
        self.current_tab = "dungeon"

        root.title("DUNGEON RUSH")
        root.geometry("1360x840")
        root.minsize(1220, 720)
        root.configure(bg=COLORS["bg"])
        self.build_layout()
        self.refresh()

    # ---------- โครงหน้าต่าง ----------

    def build_layout(self) -> None:
        """สร้างส่วนที่อยู่คงที่ของหน้าต่าง"""
        header = tk.Frame(self.root, bg=COLORS["bg"], padx=20, pady=10)
        header.pack(fill="x")
        tk.Label(header, text="⚔ DUNGEON RUSH", font=FONT_LOGO, bg=COLORS["bg"],
                 fg=COLORS["gold"]).pack(side="left")

        self.lang_buttons = {}
        for lang, text in (("en", "EN"), ("th", "ไทย")):
            button = tk.Button(header, text=text, font=FONT_BOLD, width=4, relief="flat", bd=0,
                               cursor="hand2", command=lambda l=lang: self.change_language(l))
            button.pack(side="right", padx=2)
            self.lang_buttons[lang] = button

        self.reset_button = tk.Button(header, font=FONT_BOLD, relief="flat", bd=0, padx=12, cursor="hand2",
                                      bg=COLORS["panel"], fg=COLORS["muted"], activebackground=COLORS["red_dark"],
                                      activeforeground="white", highlightthickness=0, command=self.new_game)
        self.reset_button.pack(side="right", padx=(0, 14))
        add_hover(self.reset_button, COLORS["panel"], COLORS["red_dark"])

        # แถบสถานะ pack หลังปุ่มด้านขวา เพื่อไม่ให้กินพื้นที่จนปุ่มถูกตัด
        self.chips = tk.Frame(header, bg=COLORS["bg"])
        self.chips.pack(side="left", padx=14)

        tk.Frame(self.root, bg=COLORS["gold"], height=2).pack(fill="x", padx=20)

        # แถบข้อความด้านล่าง (pack ก่อน body เพื่อให้อยู่ล่างสุดเสมอ)
        self.message = tk.Label(self.root, font=FONT_BOLD, anchor="w", padx=20, pady=8,
                                bg=COLORS["panel"], fg=COLORS["muted"])
        self.message.pack(side="bottom", fill="x")

        body = tk.Frame(self.root, bg=COLORS["bg"], padx=20, pady=12)
        body.pack(fill="both", expand=True)

        # ซ้าย: ทีมฮีโร่
        self.party_area = ScrollableFrame(body, COLORS["panel"])
        self.party_area.config(width=370)
        self.party_area.pack(side="left", fill="y")
        self.party_area.pack_propagate(False)

        # ขวา: แท็บ + เนื้อหา
        right = tk.Frame(body, bg=COLORS["bg"])
        right.pack(side="left", fill="both", expand=True, padx=(16, 0))
        self.tab_bar = tk.Frame(right, bg=COLORS["bg"])
        self.tab_bar.pack(fill="x", pady=(0, 10))
        self.tab_buttons = {}
        for tab in ("dungeon", "shop", "bag", "log"):
            button = tk.Button(self.tab_bar, relief="flat", bd=0, padx=18, pady=7, cursor="hand2",
                               highlightthickness=0, command=lambda t=tab: self.show_tab(t))
            button.pack(side="left", padx=(0, 4))
            self.tab_buttons[tab] = button

        content = tk.Frame(right, bg=COLORS["bg"])
        content.pack(fill="both", expand=True)
        self.views = {
            "dungeon": DungeonView(content, self),
            "shop": ShopView(content, self),
            "bag": BagView(content, self),
            "log": LogView(content, self),
        }

    # ---------- วาดหน้าจอ ----------

    def refresh(self) -> None:
        """วาดทุกส่วนใหม่จาก storage.state (เรียกหลังทุกการกระทำที่เปลี่ยนข้อมูล)"""
        self.render_header()
        self.render_tabs()
        self.render_party()
        for tab, view in self.views.items():
            if tab == self.current_tab:
                view.pack(fill="both", expand=True)
                view.render()
            else:
                view.pack_forget()

    def render_header(self) -> None:
        """แถบสถานะด้านบน: ทอง ชั้น ทีม กระเป๋า"""
        for widget in self.chips.winfo_children():
            widget.destroy()
        state = storage.state
        cleared = min(state["floor"] - 1, len(MONSTERS))
        chips = (
            ("◉", str(state["gold"]), get_text("ทอง", "gold"), COLORS["gold"]),
            ("▼", "■" * cleared + "□" * (len(MONSTERS) - cleared), get_text("ชั้นที่ผ่าน", "floors"), COLORS["purple"]),
            ("♟", f"{len(state['heroes'])}/{MAX_PARTY}", get_text("ทีม", "party"), COLORS["green"]),
            ("▣", f"{len(state['bag'])}/{BAG_SIZE}", get_text("กระเป๋า", "bag"), COLORS["blue"]),
        )
        for symbol, value, name, color in chips:
            chip = tk.Frame(self.chips, bg=COLORS["panel"], padx=8, pady=5)
            chip.pack(side="left", padx=2)
            tk.Label(chip, text=symbol, font=FONT_BOLD, bg=COLORS["panel"], fg=color).pack(side="left")
            tk.Label(chip, text=value, font=FONT_BIG, bg=COLORS["panel"], fg=COLORS["text"]).pack(side="left", padx=4)
            tk.Label(chip, text=name, font=FONT_SMALL, bg=COLORS["panel"], fg=COLORS["muted"]).pack(side="left")

        self.reset_button.config(text=get_text("↺ เริ่มใหม่", "↺ NEW GAME"))
        for lang, button in self.lang_buttons.items():
            active = lang == get_language()
            normal = COLORS["gold"] if active else COLORS["panel"]
            button.config(bg=normal, fg=COLORS["ink"] if active else COLORS["text"],
                          activebackground=COLORS["card_hover"], activeforeground=COLORS["gold"])
            add_hover(button, normal, COLORS["card_hover"])

    def render_tabs(self) -> None:
        """ปุ่มแท็บ (แท็บที่เปิดอยู่เป็นสีทอง)"""
        names = {
            "dungeon": get_text("▼ ดันเจี้ยน", "▼ DUNGEON"),
            "shop": get_text("◉ ร้านค้า", "◉ SHOP"),
            "bag": get_text("▣ กระเป๋า", "▣ BAG"),
            "log": get_text("✎ บันทึก", "✎ LOG"),
        }
        for tab, button in self.tab_buttons.items():
            active = tab == self.current_tab
            normal = COLORS["gold"] if active else COLORS["panel"]
            button.config(text=names[tab], font=type_font(names[tab], 12), bg=normal,
                          fg=COLORS["ink"] if active else COLORS["muted"],
                          activebackground=COLORS["card_hover"], activeforeground=COLORS["gold"])
            add_hover(button, normal, COLORS["card_hover"])

    def render_party(self) -> None:
        """แผงซ้าย: การ์ดฮีโร่ทุกคน ช่องรับสมัคร และโรงเตี๊ยม"""
        self.party_area.clear()
        panel = tk.Frame(self.party_area.inner, bg=COLORS["panel"], padx=14, pady=12)
        panel.pack(fill="both", expand=True)

        title = get_text("ทีมฮีโร่", "YOUR PARTY")
        row = tk.Frame(panel, bg=COLORS["panel"])
        row.pack(fill="x", pady=(0, 6))
        section_title(row, title, COLORS["panel"], 14).pack(side="left")
        power = heroes.party_power()
        label(row, f"ATK {power['atk']} · DEF {power['def']}", COLORS["panel"], COLORS["muted"],
              FONT_SMALL_BOLD).pack(side="right")

        for hero in storage.state["heroes"]:
            self.hero_card(panel, hero)

        if len(storage.state["heroes"]) < MAX_PARTY:
            empty = tk.Frame(panel, bg=COLORS["panel"], highlightthickness=2,
                             highlightbackground=COLORS["line"], pady=14, cursor="hand2")
            empty.pack(fill="x", pady=6)
            text = get_text("+ รับสมัครฮีโร่", "+ RECRUIT A HERO")
            hint = tk.Label(empty, text=text, font=type_font(text, 12), bg=COLORS["panel"], fg=COLORS["gold"])
            hint.pack()
            for widget in (empty, hint):
                widget.bind("<Button-1>", lambda event: self.open_recruit())

        self.inn_box(panel)

    def hero_card(self, parent: tk.Widget, hero: dict) -> None:
        """การ์ดฮีโร่ 1 คน: รูปอาชีพ ชื่อ HP XP ค่าพลัง และอุปกรณ์"""
        bg = COLORS["card"]
        card = tk.Frame(parent, bg=bg, padx=12, pady=10)
        card.pack(fill="x", pady=6)

        top = tk.Frame(card, bg=bg)
        top.pack(fill="x")
        picture(top, sprite(hero["class"], 3), bg).pack(side="left")
        info = tk.Frame(top, bg=bg)
        info.pack(side="left", padx=10)
        label(info, hero["name"], bg, font=FONT_BIG).pack(anchor="w")
        label(info, f"{heroes.class_name(hero['class'])}  Lv.{hero['level']}", bg, COLORS["muted"],
              FONT_SMALL).pack(anchor="w")
        actions = tk.Frame(top, bg=bg)
        actions.pack(side="right", anchor="n")
        flat_button(actions, "✎", lambda: self.rename(hero), size=10, padx=6, pady=1).pack(side="left", padx=1)
        flat_button(actions, "✕", lambda: self.dismiss(hero), COLORS["card"], COLORS["red_dark"],
                    size=10, padx=6, pady=1).pack(side="left", padx=1)

        # HP และ XP
        ratio = hero["hp"] / hero["max_hp"]
        hp_color = COLORS["green"] if ratio > 0.5 else (COLORS["gold"] if ratio > 0.25 else COLORS["red"])
        row = tk.Frame(card, bg=bg)
        row.pack(fill="x", pady=(8, 0))
        label(row, "HP", bg, COLORS["muted"], FONT_SMALL_BOLD, width=3, anchor="w").pack(side="left")
        meter(row, ratio, hp_color, bg, 10).pack(side="left", fill="x", expand=True, padx=4)
        label(row, f"{hero['hp']}/{hero['max_hp']}", bg, font=FONT_SMALL_BOLD, width=7, anchor="e").pack(side="left")
        row = tk.Frame(card, bg=bg)
        row.pack(fill="x", pady=(3, 0))
        need = heroes.xp_needed(hero["level"])
        label(row, "XP", bg, COLORS["muted"], FONT_SMALL_BOLD, width=3, anchor="w").pack(side="left")
        meter(row, hero["xp"] / need, COLORS["purple"], bg, 5).pack(side="left", fill="x", expand=True, padx=4)
        label(row, f"{hero['xp']}/{need}", bg, COLORS["muted"], FONT_SMALL, width=7, anchor="e").pack(side="left")

        # ค่าพลังและธาตุ
        element = heroes.hero_element(hero)
        row = tk.Frame(card, bg=bg)
        row.pack(fill="x", pady=(6, 2))
        label(row, f"ATK {heroes.hero_attack(hero)}", bg, font=FONT_BOLD).pack(side="left")
        label(row, f"   DEF {heroes.hero_defense(hero)}", bg, font=FONT_BOLD).pack(side="left")
        label(row, f"◆ {tr(ELEMENTS[element])}", bg, ELEMENT_COLORS[element], FONT_SMALL_BOLD).pack(side="right")

        # อุปกรณ์ที่ใส่ (กด ✕ เพื่อถอด)
        for slot, slot_name in (("weapon", get_text("อาวุธ", "Weapon")), ("armor", get_text("เกราะ", "Armor"))):
            item = heroes.equipped_item(hero, slot)
            row = tk.Frame(card, bg=bg)
            row.pack(fill="x", pady=1)
            label(row, slot_name, bg, COLORS["muted"], FONT_SMALL, width=6, anchor="w").pack(side="left")
            if item:
                label(row, tr(item["name"]), bg, font=FONT_SMALL_BOLD).pack(side="left")
                flat_button(row, "✕", lambda s=slot: self.unequip(hero, s), size=8, padx=4, pady=0,
                            fg=COLORS["muted"]).pack(side="right")
            else:
                label(row, "—", bg, COLORS["muted"], FONT_SMALL).pack(side="left")

    def inn_box(self, parent: tk.Widget) -> None:
        """กล่องโรงเตี๊ยมใต้การ์ดฮีโร่"""
        box = tk.Frame(parent, bg=COLORS["bg"], padx=12, pady=10)
        box.pack(fill="x", pady=(10, 0))
        title = get_text("โรงเตี๊ยม", "THE INN")
        section_title(box, title, COLORS["bg"], 12).pack(anchor="w")
        tired = len(heroes.tired_heroes())
        if tired:
            text = get_text(f"พักฟื้น HP ทุกคน: {heroes.inn_cost()} ทอง ({heroes.INN_PRICE} ทอง x {tired} คน)",
                            f"Restore everyone: {heroes.inn_cost()} gold ({heroes.INN_PRICE} x {tired})")
        else:
            text = get_text("ทุกคน HP เต็มแล้ว", "Everyone is at full HP.")
        label(box, text, COLORS["bg"], COLORS["muted"], FONT_SMALL).pack(anchor="w", pady=(2, 6))
        if tired:
            flat_button(box, get_text("พักผ่อน", "REST"), self.rest, COLORS["green"], "#3a8a54").pack(anchor="w")

    # ---------- การกระทำ ----------

    def notify(self, text: str, ok: bool = True) -> None:
        """แสดงผลการกระทำล่าสุดที่แถบล่าง (สีเขียว = สำเร็จ, สีแดง = ผิดกฎ)"""
        mark = "✔ " if ok else "✖ "
        self.message.config(text=mark + tk_safe(text.strip()), fg=COLORS["green"] if ok else COLORS["red"])

    def run(self, error: str, success: str) -> bool:
        """แสดงผลของฟังก์ชันกลาง (error = "" แปลว่าสำเร็จ) แล้ววาดหน้าจอใหม่ คืนค่า True หากสำเร็จ"""
        if error:
            self.notify(error, ok=False)
            return False
        self.notify(success)
        self.refresh()
        return True

    def show_tab(self, tab: str) -> None:
        """สลับแท็บ (ยกเว้นระหว่างการต่อสู้)"""
        if self.busy:
            return
        self.current_tab = tab
        self.refresh()

    def change_language(self, lang: str) -> None:
        """เปลี่ยนภาษาแล้ววาดหน้าจอใหม่"""
        if self.busy:
            return
        set_language(lang)
        self.message.config(text="")
        self.refresh()

    def new_game(self) -> None:
        """เริ่มเกมใหม่ (ถามยืนยันก่อน เพราะเซฟเดิมจะหายไป) ใช้ storage.new_game ตัวเดียวกับ Terminal"""
        if self.busy:
            return
        if not ask_confirm(self.root, get_text("เริ่มเกมใหม่?", "START OVER?"),
                           get_text("ความคืบหน้าทั้งหมด (ทอง ฮีโร่ ไอเทม ชั้นที่ผ่าน และสถิติ) จะหายไป",
                                    "All progress (gold, heroes, items, floors, and stats) will be lost.")):
            return
        storage.new_game()
        self.views["dungeon"].selected = None
        self.current_tab = "dungeon"
        self.notify(get_text("เริ่มเกมใหม่แล้ว ขอให้โชคดี นักผจญภัย!", "New game started. Good luck, adventurer!"))
        self.refresh()

    def rename(self, hero: dict) -> None:
        """เปลี่ยนชื่อฮีโร่"""
        name = ask_text(self.root, get_text("เปลี่ยนชื่อ", "RENAME"), get_text("ชื่อใหม่", "New name"),
                        hero["name"], heroes.validate_hero_name)
        if name is not None:
            old_name = hero["name"]
            self.run(heroes.do_rename(hero, name),
                     get_text(f"เปลี่ยนชื่อ {old_name} เป็น {name} แล้ว", f"{old_name} is now called {name}."))

    def dismiss(self, hero: dict) -> None:
        """ไล่ฮีโร่ออก (ถามยืนยันก่อน)"""
        error = heroes.check_can_dismiss()
        if error:
            self.notify(error, ok=False)
            return
        if ask_confirm(self.root, get_text("ไล่ออก?", "DISMISS?"),
                       get_text(f"ไล่ {hero['name']} ออกจากทีม? ไม่ได้รับทองคืน และอุปกรณ์จะกลับเข้ากระเป๋า",
                                f"Dismiss {hero['name']}? No refund. Their gear goes back to the bag.")):
            self.run(heroes.do_dismiss(hero), get_text(f"{hero['name']} ออกจากทีมแล้ว", f"{hero['name']} left the party."))

    def unequip(self, hero: dict, slot: str) -> None:
        """ถอดอุปกรณ์"""
        self.run(items.do_unequip(hero, slot),
                 get_text("ถอดแล้ว ไอเทมกลับเข้ากระเป๋า", "Unequipped. The item is back in your bag."))

    def rest(self) -> None:
        """พักที่โรงเตี๊ยม"""
        self.run(heroes.do_rest(), get_text("ทุกคนพักผ่อนจน HP เต็มแล้ว", "Your party is fully rested."))

    def open_recruit(self) -> None:
        """หน้าต่างรับสมัครฮีโร่: เลือกอาชีพ ตั้งชื่อ แล้วยืนยัน"""
        error = heroes.check_party_space()
        if error:
            self.notify(error, ok=False)
            return

        dialog = open_dialog(self.root, get_text("รับสมัครฮีโร่", "RECRUIT A HERO"), COLORS["gold"])
        label(dialog, get_text(f"ทองที่มี: {storage.state['gold']}", f"Your gold: {storage.state['gold']}"),
              COLORS["panel"], COLORS["muted"]).pack()
        chosen = tk.StringVar(value="")
        cards = {}

        grid = tk.Frame(dialog, bg=COLORS["panel"], padx=20, pady=10)
        grid.pack()
        for column, (key, info) in enumerate(HERO_CLASSES.items()):
            card = tk.Frame(grid, bg=COLORS["card"], padx=12, pady=10, highlightthickness=3,
                            highlightbackground=COLORS["card"], cursor="hand2")
            card.grid(row=0, column=column, padx=5, sticky="nsew")
            picture(card, sprite(key, 5), COLORS["card"]).pack()
            label(card, tr(info["name"]), COLORS["card"], font=FONT_BIG).pack(pady=(6, 0))
            price_color = COLORS["gold"] if storage.state["gold"] >= info["cost"] else COLORS["red"]
            label(card, f"{info['cost']} {get_text('ทอง', 'gold')}", COLORS["card"], price_color, FONT_BOLD).pack()
            label(card, f"HP {info['hp']}  ATK {info['atk']}  DEF {info['def']}", COLORS["card"],
                  COLORS["muted"], FONT_SMALL).pack(pady=(4, 0))
            label(card, tr(info["about"]), COLORS["card"], font=FONT_SMALL, wraplength=130,
                  justify="center").pack(pady=(4, 0))
            cards[key] = card

            def pick(event=None, k=key) -> None:
                chosen.set(k)
                for other, frame in cards.items():
                    frame.config(highlightbackground=COLORS["gold"] if other == k else COLORS["card"])
            for widget in [card] + list(card.winfo_children()):
                widget.bind("<Button-1>", pick)

        label(dialog, get_text("ชื่อฮีโร่", "Hero name"), COLORS["panel"], COLORS["muted"], FONT_SMALL).pack(anchor="w", padx=28)
        name_var = tk.StringVar()
        entry = tk.Entry(dialog, textvariable=name_var, font=FONT, relief="flat", bd=6,
                         bg=COLORS["card"], fg=COLORS["text"], insertbackground=COLORS["text"],
                         highlightthickness=1, highlightbackground=COLORS["card"], highlightcolor=COLORS["gold"])
        entry.pack(fill="x", padx=28, pady=(4, 4))
        error_label = tk.Label(dialog, text="", font=FONT_SMALL_BOLD, bg=COLORS["panel"], fg=COLORS["red"])
        error_label.pack(anchor="w", padx=28)

        def confirm(event=None) -> None:
            if not chosen.get():
                error_label.config(text=get_text("กรุณาเลือกอาชีพ", "Please choose a class."))
                return
            name = name_var.get().strip()
            error = heroes.do_recruit(chosen.get(), name)
            if error:
                error_label.config(text=error)
                return
            dialog.destroy()
            self.notify(get_text(f"{name} เข้าร่วมทีมแล้ว!", f"{name} joined your party!"))
            self.refresh()

        row = tk.Frame(dialog, bg=COLORS["panel"])
        row.pack(pady=(10, 18))
        flat_button(row, get_text("ยกเลิก", "Cancel"), dialog.destroy).pack(side="left", padx=6)
        flat_button(row, get_text("รับเข้าทีม", "RECRUIT"), confirm, COLORS["gold"], COLORS["gold_dark"],
                    fg=COLORS["ink"]).pack(side="left", padx=6)
        dialog.bind("<Return>", confirm)
        wait_dialog(self.root, dialog, entry)


def main() -> None:
    """เริ่มเกมเวอร์ชัน GUI"""
    storage.load_game()
    try:
        root = tk.Tk()
    except tk.TclError:
        # เช่น รันผ่าน SSH ที่ไม่มีหน้าจอ
        print("Cannot open a window here. Please run: python3 main.py")
        print("เปิดหน้าต่างไม่ได้ กรุณาใช้: python3 main.py")
        sys.exit(1)

    DungeonRushApp(root)
    root.mainloop()
    storage.save_game()


if __name__ == "__main__":
    main()
