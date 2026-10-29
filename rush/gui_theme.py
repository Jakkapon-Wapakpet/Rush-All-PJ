#!/usr/bin/env python3
"""
GUI Theme Module - GHOST REALM (มิติผี) (Bonus)
สี ฟอนต์ และชิ้นส่วนหน้าจอโทนหนังตะลุงสีที่ทุกส่วนของ GUI ใช้ร่วมกัน
Shared colors, fonts, and widgets for the GUI.
"""

import tkinter as tk
from tkinter import ttk

from language import get_text

# ชุดสี "หนังตะลุงยามค่ำคืน"
COLORS = {
    "bg": "#08141d",          # พื้นหลังหน้าต่าง
    "panel": "#10212b",       # พื้นแผง
    "card": "#142c35",        # พื้นการ์ด
    "card_hover": "#203d45",
    "line": "#796448",        # เส้นขอบ
    "text": "#f0e2c8",        # ตัวอักษรหลัก
    "muted": "#c4b69f",       # ตัวอักษรรอง
    "accent": "#eab363",      # แสงเทียน (สีหลักของธีม)
    "accent_dark": "#d09644",
    "ink": "#171a15",         # ตัวอักษรบนพื้นสีหลัก
    "amber": "#eab363",
    "red": "#e18b82",
    "red_dark": "#733d39",
    "blue": "#86b9c6",
    "purple": "#b6a2c5",
    "green": "#a6bf80",
    "job": "#354d33",         # ปุ่มเลือกงาน
    "disabled": "#25353c",
    "screen": "#152d36",      # จอผ้าหนังตะลุง (พื้นหลังของภาพตัวหนัง)
    "screen_edge": "#0b202b",
    "moon": "#eee1c5",
    "puppet": "#0a1119",
    "far": "#345563",
}

FONT = ("Leelawadee UI", 11, "normal")
FONT_SMALL = ("Leelawadee UI", 10, "normal")
FONT_SMALL_BOLD = ("Leelawadee UI", 10, "bold")
FONT_BOLD = ("Leelawadee UI", 11, "bold")


def tk_safe(text: str) -> str:
    """
    ตัดอักขระนอก BMP (เช่น อีโมจิส่วนใหญ่) ออก
    เพราะ Tkinter บน Python 3.10 / Tk 8.6 crash เมื่อแสดงอักขระเหล่านี้
    """
    return "".join(char for char in text if ord(char) <= 0xFFFF).replace("️", "").strip()


def clean(text) -> str:
    """ข้อความที่แสดงบนจอ: ตัดอักขระที่ Tk แสดงไม่ได้"""
    return tk_safe(str(text))


def font(text: str = "", size: int = 11) -> tuple:
    """ฟอนต์ตัวหนาสำหรับหัวข้อและปุ่ม (รองรับทั้งไทยและอังกฤษ)"""
    return ("Leelawadee UI", size, "bold")


def label(parent: tk.Widget, text, bg: str = None, fg: str = None, font: tuple = None, **options) -> tk.Label:
    """ป้ายข้อความ (ตัดอักขระที่ Tk แสดงไม่ได้ออกให้อัตโนมัติ)"""
    return tk.Label(parent, text=clean(text), bg=bg or COLORS["panel"], fg=fg or COLORS["text"],
                    font=font or ("Leelawadee UI", 10), **options)


def section_title(parent: tk.Widget, text: str, bg: str, size: int = 13, color: str = None) -> tk.Label:
    """หัวข้อสีหลัก"""
    return tk.Label(parent, text=clean(text), font=font(text, size), bg=bg, fg=color or COLORS["accent"])


def flat_button(parent: tk.Widget, text: str, command, color: str = None, hover: str = None, fg: str = None,
                size: int = 11, padx: int = 12, pady: int = 7, **options) -> tk.Button:
    """ปุ่มแบน มีสีพื้นและเปลี่ยนสีเมื่อเมาส์ชี้"""
    color = color or COLORS["card"]
    hover = hover or COLORS["card_hover"]
    fg = fg or COLORS["text"]
    button = tk.Button(parent, text=clean(text), command=command, font=font(text, size),
                       bg=color, fg=fg, activebackground=hover, activeforeground=fg,
                       relief="flat", bd=0, padx=padx, pady=pady, cursor="hand2",
                       highlightthickness=1, highlightbackground=COLORS["line"],
                       highlightcolor=COLORS["accent"], **options)
    button.bind("<Enter>", lambda event: button.config(bg=hover) if button.cget("state") != "disabled" else None)
    button.bind("<Leave>", lambda event: button.config(bg=color))
    return button


def set_button_text(button: tk.Button, text: str, size: int = 11) -> None:
    """เปลี่ยนข้อความของปุ่ม พร้อมฟอนต์ใหม่"""
    button.config(text=clean(text), font=font(text, size))


def meter(parent: tk.Widget, ratio: float, color: str, height: int = 8) -> tk.Canvas:
    """แถบค่า (เช่น HP) วาดใหม่อัตโนมัติเมื่อขนาดเปลี่ยน"""
    canvas = tk.Canvas(parent, height=height, bg=COLORS["disabled"], bd=0, highlightthickness=0)
    ratio = max(0.0, min(1.0, ratio))

    def draw(event=None) -> None:
        canvas.delete("all")
        width = canvas.winfo_width() * ratio
        if width > 0:
            canvas.create_rectangle(0, 0, width, height, fill=color, width=0)

    canvas.bind("<Configure>", draw)
    return canvas


def picture(parent: tk.Widget, image: tk.PhotoImage) -> tk.Label:
    """แสดงภาพตัวหนังบนจอผ้าเล็กๆ"""
    return tk.Label(parent, image=image, bg=COLORS["screen"], bd=0, padx=4, pady=4)


class ScrollableFrame(tk.Frame):
    """กรอบที่เลื่อนขึ้นลงได้ (Canvas + Scrollbar) สำหรับเนื้อหาที่ยาวเกินหน้าจอ"""

    def __init__(self, parent: tk.Widget, bg: str) -> None:
        super().__init__(parent, bg=bg)
        style = ttk.Style(self)
        if style.theme_use() != "clam":
            style.theme_use("clam")
        style.configure("Miti.Vertical.TScrollbar", background=COLORS["card_hover"],
                        troughcolor=bg, bordercolor=bg, arrowcolor=COLORS["muted"],
                        lightcolor=COLORS["card_hover"], darkcolor=bg, width=10)
        self.canvas = tk.Canvas(self, bg=bg, bd=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview,
                                       style="Miti.Vertical.TScrollbar")
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.config(yscrollcommand=self.scrollbar.set)

        # inner คือกรอบที่ใส่เนื้อหาจริง วางอยู่ใน canvas
        self.inner = tk.Frame(self.canvas, bg=bg)
        self.window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", self.on_resize)
        self.canvas.bind("<Configure>", self.on_resize)

        # ลูกกลิ้งเมาส์ (Windows/macOS ใช้ MouseWheel, Linux ใช้ Button-4/5)
        for sequence in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.bind_all(sequence, self.on_wheel, add="+")

    def on_resize(self, event=None) -> None:
        """ขนาดเปลี่ยน: ให้เนื้อหากว้างเท่า canvas และอัปเดตพื้นที่เลื่อน"""
        self.canvas.itemconfig(self.window, width=max(1, self.canvas.winfo_width()))
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    @staticmethod
    def on_wheel(event):
        """หา ScrollableFrame ที่อยู่ใต้เมาส์ แล้วเลื่อนเฉพาะกรอบนั้น"""
        widget = event.widget
        while isinstance(widget, tk.Misc) and not isinstance(widget, ScrollableFrame):
            widget = widget.master
        if not isinstance(widget, ScrollableFrame) or widget.inner.winfo_height() <= widget.canvas.winfo_height():
            return
        up = getattr(event, "num", 0) == 4 or getattr(event, "delta", 0) > 0
        widget.canvas.yview_scroll(-2 if up else 2, "units")
        return "break"

    def clear(self) -> None:
        """ลบเนื้อหาทั้งหมด"""
        for widget in self.inner.winfo_children():
            widget.destroy()


def open_dialog(root: tk.Tk, title: str, color: str = None) -> tk.Toplevel:
    """สร้างหน้าต่างย่อยในธีม (แถบหัวข้อด้านบน)"""
    dialog = tk.Toplevel(root, bg=COLORS["panel"])
    dialog.title("มิติผี · " + clean(title))
    dialog.transient(root)
    dialog.resizable(False, False)
    header = tk.Frame(dialog, bg=COLORS["bg"], padx=22, pady=14)
    header.pack(fill="x", pady=(0, 12))
    label(header, title, COLORS["bg"], color or COLORS["accent"], font(title, 20)).pack(anchor="w")
    dialog.bind("<Escape>", lambda event: dialog.destroy())
    return dialog


def wait_dialog(root: tk.Tk, dialog: tk.Toplevel, focus: tk.Widget) -> None:
    """วางหน้าต่างย่อยไว้กลางหน้าต่างหลัก แล้วรอจนกว่าจะปิด"""
    dialog.update_idletasks()
    x = root.winfo_rootx() + (root.winfo_width() - dialog.winfo_width()) // 2
    y = root.winfo_rooty() + (root.winfo_height() - dialog.winfo_height()) // 3
    dialog.geometry(f"+{max(x, 0)}+{max(y, 0)}")
    focus.focus_set()
    dialog.wait_visibility()
    dialog.grab_set()
    root.wait_window(dialog)


def ask_confirm(root: tk.Tk, title: str, message: str) -> bool:
    """กล่องยืนยัน คืนค่า True เมื่อผู้ใช้กดยืนยัน"""
    answer = {"value": False}

    def confirm() -> None:
        answer["value"] = True
        dialog.destroy()

    dialog = open_dialog(root, title, COLORS["red"])
    tk.Label(dialog, text=tk_safe(message), font=FONT, wraplength=420, justify="left",
             bg=COLORS["panel"], fg=COLORS["text"], padx=28).pack(pady=(0, 16))
    row = tk.Frame(dialog, bg=COLORS["panel"])
    row.pack(pady=(0, 18))
    cancel = flat_button(row, get_text("ยกเลิก", "Cancel"), dialog.destroy)
    cancel.pack(side="left", padx=6)
    flat_button(row, get_text("ยืนยัน", "Confirm"), confirm, COLORS["red"], COLORS["red_dark"]).pack(side="left", padx=6)
    wait_dialog(root, dialog, cancel)
    return answer["value"]


def ask_text(root: tk.Tk, title: str, prompt: str, initial: str, validate) -> str:
    """
    กล่องให้พิมพ์ข้อความ 1 บรรทัด
    validate(text) คืนข้อความผิดพลาด หรือ "" หากใช้ได้ (ผิดพลาดจะแสดงในกล่องและให้แก้ใหม่)
    คืนค่าข้อความที่ผ่านการตรวจ หรือ None หากยกเลิก
    """
    answer = {"value": None}
    dialog = open_dialog(root, title, COLORS["accent"])
    tk.Label(dialog, text=prompt, font=FONT_SMALL, bg=COLORS["panel"], fg=COLORS["muted"]).pack(anchor="w", padx=28)
    variable = tk.StringVar(value=tk_safe(initial))
    entry = tk.Entry(dialog, textvariable=variable, font=FONT, width=28, relief="flat", bd=6,
                     bg=COLORS["card"], fg=COLORS["text"], insertbackground=COLORS["text"],
                     highlightthickness=1, highlightbackground=COLORS["card"], highlightcolor=COLORS["accent"])
    entry.pack(padx=28, pady=(4, 6), fill="x")
    error_label = tk.Label(dialog, text="", font=FONT_SMALL_BOLD, bg=COLORS["panel"], fg=COLORS["red"])
    error_label.pack(anchor="w", padx=28)

    def confirm(event=None) -> None:
        error = validate(variable.get().strip())
        if error:
            error_label.config(text=tk_safe(error))
            return
        answer["value"] = variable.get().strip()
        dialog.destroy()

    row = tk.Frame(dialog, bg=COLORS["panel"])
    row.pack(pady=(10, 18))
    flat_button(row, get_text("ยกเลิก", "Cancel"), dialog.destroy).pack(side="left", padx=6)
    flat_button(row, "OK", confirm, COLORS["accent"], COLORS["accent_dark"], fg=COLORS["ink"]).pack(side="left", padx=6)
    dialog.bind("<Return>", confirm)
    entry.select_range(0, "end")
    wait_dialog(root, dialog, entry)
    return answer["value"]
