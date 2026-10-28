#!/usr/bin/env python3
"""
GUI Theme Module - LAST SHELTER (Bonus)
สี ฟอนต์ และชิ้นส่วนหน้าจอที่ทุกส่วนของ GUI ใช้ร่วมกัน
Shared colors, fonts, and widgets for the GUI.
"""

import tkinter as tk

from language import get_text

# ชุดสี "เมืองร้างยามค่ำคืน"
COLORS = {
    "bg": "#101311",          # พื้นหลังหน้าต่าง
    "panel": "#181d1a",       # พื้นแผง
    "card": "#222925",        # พื้นการ์ด
    "card_hover": "#2c3530",
    "line": "#36413a",        # เส้นขอบ
    "text": "#e6e8df",        # ตัวอักษรหลัก
    "muted": "#87928a",       # ตัวอักษรรอง
    "accent": "#a3d65a",      # เขียวสารพิษ (สีหลักของธีม)
    "accent_dark": "#7aa83a",
    "ink": "#141812",         # ตัวอักษรบนพื้นสีหลัก
    "amber": "#e8a83a",
    "red": "#d2463b",
    "red_dark": "#9c3029",
    "blue": "#5aa9e6",
    "purple": "#9b7be0",
    "disabled": "#2f3632",
}

FONT = ("TkDefaultFont", 11)
FONT_SMALL = ("TkDefaultFont", 9)
FONT_SMALL_BOLD = ("TkDefaultFont", 9, "bold")
FONT_BOLD = ("TkDefaultFont", 11, "bold")
FONT_BIG = ("TkDefaultFont", 14, "bold")
FONT_HUGE = ("TkDefaultFont", 28, "bold")
FONT_LOGO = ("Courier", 24, "bold")


def tk_safe(text: str) -> str:
    """
    ตัดอักขระนอก BMP (เช่น อีโมจิส่วนใหญ่) ออก
    เพราะ Tkinter บน Python 3.10 / Tk 8.6 crash เมื่อแสดงอักขระเหล่านี้
    """
    return "".join(char for char in text if ord(char) <= 0xFFFF).replace("️", "").strip()


def type_font(text: str, size: int = 12) -> tuple:
    """
    ฟอนต์พิมพ์ดีดสำหรับหัวข้อ ใช้ได้เฉพาะข้อความภาษาอังกฤษ
    เพราะ Courier ไม่มีตัวอักษรไทย (สระและวรรณยุกต์จะลอยแยก) จึงใช้ฟอนต์ปกติตัวหนาแทน
    """
    if all(ord(char) < 128 for char in text):
        return ("Courier", size, "bold")
    return ("TkDefaultFont", size, "bold")


def add_hover(widget: tk.Widget, normal: str, hover: str) -> None:
    """เปลี่ยนสีพื้นเมื่อเมาส์ชี้"""
    widget.bind("<Enter>", lambda event: widget.config(bg=hover))
    widget.bind("<Leave>", lambda event: widget.config(bg=normal))


def label(parent: tk.Widget, text: str, bg: str, fg: str = None, font: tuple = FONT, **options) -> tk.Label:
    """ป้ายข้อความ (ตัดอักขระที่ Tk แสดงไม่ได้ออกให้อัตโนมัติ)"""
    return tk.Label(parent, text=tk_safe(text), bg=bg, fg=fg or COLORS["text"], font=font, **options)


def section_title(parent: tk.Widget, text: str, bg: str, size: int = 13, color: str = None) -> tk.Label:
    """หัวข้อสีหลัก"""
    return tk.Label(parent, text=tk_safe(text), font=type_font(text, size), bg=bg, fg=color or COLORS["accent"])


def flat_button(parent: tk.Widget, text: str, command, color: str = None, hover: str = None,
                fg: str = "white", size: int = 11, padx: int = 12, pady: int = 5, **options) -> tk.Button:
    """ปุ่มแบน มีสีพื้นและเปลี่ยนสีเมื่อเมาส์ชี้"""
    color = color or COLORS["card"]
    hover = hover or COLORS["card_hover"]
    button = tk.Button(parent, text=tk_safe(text), command=command, font=type_font(text, size),
                       bg=color, fg=fg, activebackground=hover, activeforeground=fg,
                       relief="flat", bd=0, padx=padx, pady=pady, cursor="hand2",
                       highlightthickness=0, **options)
    add_hover(button, color, hover)
    return button


def meter(parent: tk.Widget, ratio: float, color: str, height: int = 8) -> tk.Canvas:
    """แถบค่า (เช่น HP / XP) วาดใหม่อัตโนมัติเมื่อขนาดเปลี่ยน"""
    canvas = tk.Canvas(parent, height=height, bg=COLORS["disabled"], bd=0, highlightthickness=0)
    ratio = max(0.0, min(1.0, ratio))

    def draw(event=None) -> None:
        canvas.delete("all")
        width = canvas.winfo_width() * ratio
        if width > 0:
            canvas.create_rectangle(0, 0, width, height, fill=color, width=0)

    canvas.bind("<Configure>", draw)
    return canvas


def picture(parent: tk.Widget, image: tk.PhotoImage, bg: str) -> tk.Label:
    """แสดงภาพพิกเซลอาร์ต (จาก sprites.py) บนพื้นสีที่กำหนด"""
    return tk.Label(parent, image=image, bg=bg, bd=0)


class ScrollableFrame(tk.Frame):
    """กรอบที่เลื่อนขึ้นลงได้ (Canvas + Scrollbar) สำหรับเนื้อหาที่ยาวเกินหน้าจอ"""

    def __init__(self, parent: tk.Widget, bg: str) -> None:
        super().__init__(parent, bg=bg)
        self.canvas = tk.Canvas(self, bg=bg, bd=0, highlightthickness=0)
        scrollbar = tk.Scrollbar(self, command=self.canvas.yview, width=10, bd=0,
                                 bg=COLORS["card"], troughcolor=bg,
                                 activebackground=COLORS["accent"], highlightthickness=0)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        # inner คือกรอบที่ใส่เนื้อหาจริง วางอยู่ใน canvas
        self.inner = tk.Frame(self.canvas, bg=bg)
        self.window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", self.on_inner_resize)
        self.canvas.bind("<Configure>",
                         lambda event: self.canvas.itemconfig(self.window, width=event.width))

        # ลูกกลิ้งเมาส์ (Windows/macOS ใช้ MouseWheel, Linux ใช้ Button-4/5)
        for sequence in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.bind_all(sequence, ScrollableFrame.on_wheel)

    def on_inner_resize(self, event) -> None:
        """เนื้อหาเปลี่ยนขนาด: อัปเดตพื้นที่เลื่อน และบังคับให้กว้างเท่า canvas"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        width = self.canvas.winfo_width()
        if width > 1:
            self.canvas.itemconfig(self.window, width=width)

    @staticmethod
    def on_wheel(event) -> None:
        """หา ScrollableFrame ที่อยู่ใต้เมาส์ แล้วเลื่อนเฉพาะกรอบนั้น"""
        widget = event.widget
        while isinstance(widget, tk.Misc) and not isinstance(widget, ScrollableFrame):
            widget = widget.master
        if not isinstance(widget, ScrollableFrame):
            return
        if widget.inner.winfo_height() <= widget.canvas.winfo_height():
            return
        if event.num == 4 or getattr(event, "delta", 0) > 0:
            widget.canvas.yview_scroll(-2, "units")
        else:
            widget.canvas.yview_scroll(2, "units")

    def clear(self) -> None:
        """ลบเนื้อหาทั้งหมด"""
        for widget in self.inner.winfo_children():
            widget.destroy()


def open_dialog(root: tk.Tk, title: str, color: str) -> tk.Toplevel:
    """สร้างหน้าต่างย่อยในธีม (แถบสีด้านบน + หัวข้อ)"""
    dialog = tk.Toplevel(root, bg=COLORS["panel"])
    dialog.title("LAST SHELTER")
    dialog.transient(root)
    dialog.resizable(False, False)
    tk.Frame(dialog, bg=color, height=5).pack(fill="x")
    tk.Label(dialog, text=tk_safe(title), font=type_font(title, 18), bg=COLORS["panel"], fg=color,
             padx=28).pack(pady=(16, 8))
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
