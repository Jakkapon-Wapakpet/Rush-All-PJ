#!/usr/bin/env python3
"""
GUI Town Module - DUNGEON RUSH (Bonus)
แท็บ "ร้านค้า" (กรอง/เรียงสินค้า ซื้อ ของคุ้มที่สุด) และแท็บ "กระเป๋า" (สวมใส่ ขาย)
ทุกการเปลี่ยนข้อมูลเรียกฟังก์ชันกลางใน items.py ตัวเดียวกับเวอร์ชัน Terminal
Shop and bag tabs of the GUI.
"""

import tkinter as tk

from language import get_text
from data import ITEMS, HERO_CLASSES, ELEMENTS, BAG_SIZE, tr
import heroes
import items
import storage
from sprites import item_sprite
from gui_theme import (picture, COLORS, FONT_SMALL, FONT_SMALL_BOLD, FONT_BOLD,
                       FONT_BIG, ScrollableFrame, flat_button, label, meter, section_title, toggle_group)


def item_stat(key: str) -> str:
    """ค่าพลังของไอเทมแบบสั้น"""
    item = ITEMS[key]
    if item["type"] == "weapon":
        return f"ATK +{item['atk']}  ◆ {tr(ELEMENTS[item['element']])}"
    if item["type"] == "armor":
        return f"DEF +{item['def']}"
    return get_text(f"ฟื้น HP {item['heal']} อัตโนมัติเมื่อ HP ต่ำ", f"Heals {item['heal']} HP when low")


def item_users(key: str) -> str:
    """เลเวลขั้นต่ำและอาชีพที่ใช้ได้"""
    item = ITEMS[key]
    users = ", ".join(tr(HERO_CLASSES[c]["name"]) for c in item["classes"])
    return f"Lv.{item['level']}+  ·  {users}"


class ShopView(tk.Frame):
    """แท็บร้านค้า: รายการสินค้า (กรอง/เรียงได้) และอันดับของคุ้มที่สุด"""

    def __init__(self, parent: tk.Widget, app) -> None:
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app
        self.type_var = tk.StringVar(value="all")
        self.sort_var = tk.StringVar(value="price")
        self.afford_var = tk.BooleanVar(value=False)
        for variable in (self.type_var, self.sort_var, self.afford_var):
            variable.trace_add("write", lambda *args: self.render_list())
        self.list_area = None

    def render(self) -> None:
        """วาดแท็บใหม่ทั้งหมด"""
        for widget in self.winfo_children():
            widget.destroy()

        # ขวา: ของคุ้มที่สุด
        side = tk.Frame(self, bg=COLORS["panel"], width=280, padx=16, pady=14)
        side.pack(side="right", fill="y", padx=(14, 0))
        side.pack_propagate(False)
        section_title(side, get_text("ของคุ้มที่สุด", "BEST VALUE"), COLORS["panel"]).pack(anchor="w")
        label(side, get_text("ค่าพลังต่อ 100 ทอง", "power per 100 gold"), COLORS["panel"], COLORS["muted"],
              FONT_SMALL).pack(anchor="w", pady=(0, 8))
        for rank, (key, value) in enumerate(items.best_value_items(), start=1):
            row = tk.Frame(side, bg=COLORS["panel"])
            row.pack(fill="x", pady=4)
            label(row, f"{rank}.", COLORS["panel"], COLORS["gold"], FONT_BOLD, width=2).pack(side="left")
            label(row, f"{value:.1f}", COLORS["panel"], COLORS["green"], FONT_BOLD).pack(side="right")
            text = tk.Frame(row, bg=COLORS["panel"])
            text.pack(side="left", fill="x", expand=True)
            label(text, tr(ITEMS[key]["name"]), COLORS["panel"], font=FONT_BOLD).pack(anchor="w")
            label(text, item_stat(key), COLORS["panel"], COLORS["muted"], FONT_SMALL).pack(anchor="w")
            label(text, f"◉ {ITEMS[key]['price']} {get_text('ทอง', 'gold')}", COLORS["panel"], COLORS["gold"],
                  FONT_SMALL).pack(anchor="w")

        # ซ้าย: ตัวกรอง + รายการสินค้า
        main = tk.Frame(self, bg=COLORS["bg"])
        main.pack(side="left", fill="both", expand=True)
        filters = tk.Frame(main, bg=COLORS["bg"])
        filters.pack(fill="x", pady=(0, 8))
        label(filters, get_text("ประเภท", "Type"), COLORS["bg"], COLORS["muted"], FONT_SMALL).pack(side="left")
        toggle_group(filters, self.type_var, [
            ("all", get_text("ทั้งหมด", "All")), ("weapon", get_text("อาวุธ", "Weapons")),
            ("armor", get_text("เกราะ", "Armor")), ("potion", get_text("ยา", "Potions")),
        ], COLORS["bg"]).pack(side="left", padx=(6, 18))
        label(filters, get_text("เรียง", "Sort"), COLORS["bg"], COLORS["muted"], FONT_SMALL).pack(side="left")
        toggle_group(filters, self.sort_var, [
            ("price", get_text("ราคา", "Price")), ("power", get_text("พลัง", "Power")),
            ("level", get_text("เลเวล", "Level")),
        ], COLORS["bg"]).pack(side="left", padx=(6, 18))
        tk.Checkbutton(filters, text=get_text("เฉพาะที่ซื้อไหว", "Affordable only"), variable=self.afford_var,
                       font=FONT_SMALL_BOLD, bg=COLORS["bg"], fg=COLORS["text"], selectcolor=COLORS["card"],
                       activebackground=COLORS["bg"], activeforeground=COLORS["gold"], highlightthickness=0,
                       bd=0, cursor="hand2").pack(side="left")

        self.list_area = ScrollableFrame(main, COLORS["bg"])
        self.list_area.pack(fill="both", expand=True)
        self.render_list()

    def render_list(self) -> None:
        """เติมรายการสินค้าตามตัวกรองและการเรียง (ใช้ items.shop_items ตัวเดียวกับ Terminal)"""
        if self.list_area is None or not self.list_area.winfo_exists():
            return
        self.list_area.clear()
        keys = items.shop_items(self.type_var.get(), self.sort_var.get(), self.afford_var.get())
        if not keys:
            label(self.list_area.inner, get_text("ไม่มีสินค้าที่ตรงเงื่อนไข", "No items match."),
                  COLORS["bg"], COLORS["muted"]).pack(pady=30)
        for key in keys:
            self.item_row(key)

    def item_row(self, key: str) -> None:
        """สินค้า 1 แถว: สัญลักษณ์ ชื่อ ค่าพลัง ผู้ใช้ได้ ราคา และปุ่มซื้อ"""
        item = ITEMS[key]
        bg = COLORS["card"]
        row = tk.Frame(self.list_area.inner, bg=bg, padx=12, pady=8)
        row.pack(fill="x", pady=3, padx=(0, 6))
        picture(row, item_sprite(key, item, 3), bg).pack(side="left")

        # ราคาและปุ่มซื้อ pack ก่อน เพื่อไม่ให้ข้อความยาวๆ ดันจนหายไป
        affordable = storage.state["gold"] >= item["price"]
        flat_button(row, get_text("ซื้อ", "BUY"), lambda: self.buy(key), COLORS["gold"] if affordable else COLORS["disabled"],
                    COLORS["gold_dark"], fg=COLORS["ink"] if affordable else COLORS["muted"]).pack(side="right")
        label(row, f"◉ {item['price']}", bg, COLORS["gold"] if affordable else COLORS["red"], FONT_BIG,
              width=6, anchor="e").pack(side="right", padx=12)

        text = tk.Frame(row, bg=bg)
        text.pack(side="left", fill="x", expand=True, padx=12)
        label(text, tr(item["name"]), bg, font=FONT_BOLD).pack(anchor="w")
        label(text, item_stat(key), bg, COLORS["muted"], FONT_SMALL).pack(anchor="w")
        label(text, item_users(key), bg, COLORS["muted"], FONT_SMALL).pack(anchor="w")

    def buy(self, key: str) -> None:
        """ซื้อสินค้า (กฎ: ทองต้องพอ, กระเป๋าต้องไม่เต็ม)"""
        name = tr(ITEMS[key]["name"])
        self.app.run(items.do_buy(key), get_text(f"ซื้อ {name} แล้ว ไปที่แท็บกระเป๋าเพื่อสวมใส่",
                                                 f"Bought {name}. Open the Bag tab to equip it."))


class BagView(tk.Frame):
    """แท็บกระเป๋า: ไอเทมทุกชิ้น ใครใส่อยู่ ปุ่มสวมใส่ให้ฮีโร่แต่ละคน และปุ่มขาย"""

    def __init__(self, parent: tk.Widget, app) -> None:
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app

    def render(self) -> None:
        """วาดแท็บใหม่ทั้งหมด"""
        for widget in self.winfo_children():
            widget.destroy()
        bag = storage.state["bag"]

        top = tk.Frame(self, bg=COLORS["bg"])
        top.pack(fill="x", pady=(0, 8))
        section_title(top, get_text("กระเป๋า", "BAG"), COLORS["bg"], 14).pack(side="left")
        label(top, f"{len(bag)}/{BAG_SIZE}", COLORS["bg"], font=FONT_BIG).pack(side="left", padx=10)
        meter(top, len(bag) / BAG_SIZE, COLORS["red"] if len(bag) >= BAG_SIZE else COLORS["blue"],
              COLORS["bg"], 8).pack(side="left", fill="x", expand=True, padx=(10, 0))

        if not bag:
            empty = tk.Frame(self, bg=COLORS["panel"], pady=40)
            empty.pack(fill="x")
            label(empty, get_text("กระเป๋าว่าง", "Your bag is empty."), COLORS["panel"], font=FONT_BIG).pack()
            flat_button(empty, get_text("ไปร้านค้า", "GO TO SHOP"), lambda: self.app.show_tab("shop"),
                        COLORS["gold"], COLORS["gold_dark"], fg=COLORS["ink"]).pack(pady=(10, 0))
            return

        area = ScrollableFrame(self, COLORS["bg"])
        area.pack(fill="both", expand=True)
        grid = tk.Frame(area.inner, bg=COLORS["bg"])
        grid.pack(fill="x")
        grid.columnconfigure((0, 1), weight=1, uniform="bag")
        for index, bag_item in enumerate(bag):
            self.item_card(grid, index, bag_item)

    def item_card(self, grid: tk.Frame, index: int, bag_item: dict) -> None:
        """การ์ดไอเทม 1 ชิ้น"""
        key = bag_item["key"]
        item = ITEMS[key]
        holder = heroes.holder_of(bag_item["uid"])
        bg = COLORS["card"]
        card = tk.Frame(grid, bg=bg, padx=12, pady=10, highlightthickness=2,
                        highlightbackground=COLORS["gold"] if holder else bg)
        card.grid(row=index // 2, column=index % 2, sticky="nsew", padx=(0, 8), pady=4)

        top = tk.Frame(card, bg=bg)
        top.pack(fill="x")
        picture(top, item_sprite(key, item, 3), bg).pack(side="left")
        text = tk.Frame(top, bg=bg)
        text.pack(side="left", padx=10)
        label(text, tr(item["name"]), bg, font=FONT_BOLD).pack(anchor="w")
        label(text, item_stat(key), bg, COLORS["muted"], FONT_SMALL).pack(anchor="w")
        if holder:
            label(top, get_text(f"ใส่อยู่: {holder['name']}", f"worn by {holder['name']}"), bg,
                  COLORS["gold"], FONT_SMALL_BOLD).pack(side="right", anchor="n")

        actions = tk.Frame(card, bg=bg)
        actions.pack(fill="x", pady=(8, 0))
        if item["type"] in ("weapon", "armor"):
            label(actions, get_text("ใส่ให้", "Equip"), bg, COLORS["muted"], FONT_SMALL).pack(side="left")
            for hero in storage.state["heroes"]:
                can = not items.check_can_equip(hero, key)
                worn = hero is holder
                flat_button(actions, hero["name"], lambda h=hero: self.equip(h, bag_item), size=9, padx=8, pady=2,
                            color=COLORS["gold"] if worn else (COLORS["card_hover"] if can else COLORS["disabled"]),
                            fg=COLORS["ink"] if worn else (COLORS["text"] if can else COLORS["muted"])
                            ).pack(side="left", padx=2)
        else:
            label(actions, get_text("ใช้อัตโนมัติในการต่อสู้", "Used automatically in battle"), bg,
                  COLORS["muted"], FONT_SMALL).pack(side="left")
        flat_button(actions, get_text(f"ขาย +{items.sell_price(key)}", f"SELL +{items.sell_price(key)}"),
                    lambda: self.sell(bag_item), COLORS["card_hover"], COLORS["red_dark"], size=9,
                    padx=8, pady=2).pack(side="right")

    def equip(self, hero: dict, bag_item: dict) -> None:
        """ใส่ไอเทมให้ฮีโร่ (กฎ: อาชีพ เลเวล และไอเทมใส่ได้ทีละคน)"""
        name = tr(ITEMS[bag_item["key"]]["name"])
        error = items.do_equip(hero, bag_item)
        self.app.run(error, get_text(
            f"{hero['name']} ใส่ {name} แล้ว (ATK {heroes.hero_attack(hero)}  DEF {heroes.hero_defense(hero)})",
            f"{hero['name']} equipped {name}. (ATK {heroes.hero_attack(hero)}  DEF {heroes.hero_defense(hero)})"))

    def sell(self, bag_item: dict) -> None:
        """ขายไอเทม (กฎ: ขายของที่มีคนใส่อยู่ไม่ได้)"""
        name = tr(ITEMS[bag_item["key"]]["name"])
        refund = items.sell_price(bag_item["key"])
        self.app.run(items.do_sell(bag_item), get_text(f"ขาย {name} ได้ {refund} ทอง",
                                                       f"Sold {name} for {refund} gold."))
