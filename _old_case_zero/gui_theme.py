#!/usr/bin/env python3
"""
GUI Theme Module - CASE ZERO (Bonus)
สี ฟอนต์ และชิ้นส่วนหน้าจอที่ใช้ร่วมกันทุกแท็บของ GUI
Shared colors, fonts, and widgets for every GUI tab.
"""

import tkinter as tk

from language import get_text
import game

# ชุดสีธีม "นักสืบฟิล์มนัวร์"
COLORS = {
    "bg": "#16181d",          # พื้นหลังหน้าต่าง
    "panel": "#20232b",       # พื้นแผง
    "panel_light": "#2c303b", # พื้นการ์ด / ช่องกรอก / ปุ่มตอนเมาส์ชี้
    "text": "#e8e6e1",        # ตัวอักษรบนพื้นมืด
    "muted": "#8b93a7",       # ตัวอักษรรอง
    "accent": "#d4a24c",      # สีทองอำพัน
    "paper": "#efe6d0",       # กระดาษ
    "paper_edge": "#cdbf9c",  # ขอบกระดาษ
    "ink": "#2b2118",         # หมึกบนกระดาษ
    "ink_soft": "#6e5f4b",    # หมึกจาง
    "danger": "#b3261e",      # แดง
    "danger_dark": "#8c1d17",
    "success": "#3f8f5a",     # เขียว
    "cold": "#6fa8dc",        # ฟ้า
    "disabled": "#3a3e49",
}

# สีวงกลมรูปตัวละครของผู้ต้องสงสัยแต่ละคน
AVATAR_COLORS = ["#8c5a3c", "#3c6e8c", "#6b4c8c", "#3c8c6e", "#8c3c5a"]

FONT = ("TkDefaultFont", 12)
FONT_SMALL = ("TkDefaultFont", 10)
FONT_SMALL_BOLD = ("TkDefaultFont", 10, "bold")
FONT_BOLD = ("TkDefaultFont", 12, "bold")
FONT_NAME = ("TkDefaultFont", 14, "bold")
FONT_QUOTE = ("TkDefaultFont", 12, "italic")
FONT_LOGO = ("Courier", 26, "bold")

# สัญลักษณ์และสีของสถานะคดี (ใช้อักขระใน BMP เท่านั้น ดู tk_safe)
STATUS_STYLE = {
    "open": ("●", COLORS["accent"]),
    "closed": ("✔", COLORS["success"]),
    "cold": ("❄", COLORS["cold"]),
}


def tk_safe(text: str) -> str:
    """
    ตัดอักขระนอก BMP (เช่น อีโมจิส่วนใหญ่) ออก
    เพราะ Tkinter บน Python 3.10 / Tk 8.6 crash เมื่อแสดงอักขระเหล่านี้
    """
    return "".join(char for char in text if ord(char) <= 0xFFFF)


def text_of(item: dict, field: str) -> str:
    """คืนค่าฟิลด์ตามภาษาปัจจุบัน (เหมือน game.local) ที่แสดงใน Tkinter ได้อย่างปลอดภัย"""
    return tk_safe(game.local(item, field))


def type_font(text: str, size: int = 12) -> tuple:
    """
    ฟอนต์พิมพ์ดีดสำหรับหัวข้อ ใช้ได้เฉพาะข้อความภาษาอังกฤษ
    เพราะ Courier ไม่มีตัวอักษรไทย (สระและวรรณยุกต์จะลอยแยก) จึงใช้ฟอนต์ปกติตัวหนาแทน
    """
    if all(ord(char) < 128 for char in text):
        return ("Courier", size, "bold")
    return ("TkDefaultFont", size, "bold")


def split_name(full_name: str) -> tuple:
    """แยก 'มาลี (แม่บ้าน)' เป็น ('มาลี', 'แม่บ้าน')"""
    if "(" in full_name and full_name.endswith(")"):
        index = full_name.index("(")
        return full_name[:index].strip(), full_name[index + 1:-1].strip()
    return full_name, ""


def initial_of(name: str) -> str:
    """ตัวอักษรแรกของชื่อสำหรับวงกลมรูปตัวละคร (ข้ามสระหน้าภาษาไทย เช่น เ แ โ ใ ไ)"""
    for char in name:
        if char not in "เแโใไ ":
            return char.upper()
    return "?"


def add_hover(button: tk.Button, normal: str, hover: str) -> None:
    """เปลี่ยนสีพื้นปุ่มเมื่อเมาส์ชี้"""
    button.bind("<Enter>", lambda event: button.config(bg=hover))
    button.bind("<Leave>", lambda event: button.config(bg=normal))


def bind_click(widget: tk.Widget, callback) -> None:
    """ให้คลิกตรงไหนของการ์ดก็ได้ (รวม widget ลูกทุกตัว) แล้วเรียก callback"""
    widget.bind("<Button-1>", lambda event: callback())
    for child in widget.winfo_children():
        bind_click(child, callback)


def section_label(parent: tk.Widget, text: str, bg: str, size: int = 12) -> tk.Label:
    """หัวข้อสีทอง"""
    label = tk.Label(parent, text=text, font=type_font(text, size), bg=bg, fg=COLORS["accent"])
    return label


def flat_button(parent: tk.Widget, text: str, command, color: str, hover: str,
                fg: str = "white", **options) -> tk.Button:
    """ปุ่มแบน มีสีพื้นและเปลี่ยนสีเมื่อเมาส์ชี้"""
    button = tk.Button(parent, text=text, command=command, font=type_font(text, 12),
                       bg=color, fg=fg, activebackground=hover, activeforeground=fg,
                       relief="flat", bd=0, padx=14, pady=6, cursor="hand2", **options)
    add_hover(button, color, hover)
    return button


def toggle_group(parent: tk.Widget, variable: tk.StringVar, options: list, bg: str) -> tk.Frame:
    """
    กลุ่มปุ่มสลับ (เลือกได้ทีละปุ่ม) จาก options = [(ค่า, ข้อความ), ...]
    ใช้ Radiobutton แบบไม่มีวงกลม (indicatoron=0) ให้ดูเป็นปุ่ม
    """
    group = tk.Frame(parent, bg=bg)
    buttons = {}
    for value, label in options:
        button = tk.Radiobutton(
            group, text=label, value=value, variable=variable, indicatoron=0, font=FONT_SMALL_BOLD,
            bg=COLORS["panel_light"], fg=COLORS["text"], selectcolor=COLORS["accent"],
            activebackground=COLORS["disabled"], activeforeground=COLORS["text"],
            relief="flat", bd=0, padx=10, pady=5, cursor="hand2", highlightthickness=0
        )
        button.pack(side="left", padx=(0, 2))
        buttons[value] = button

    def recolor(*args) -> None:
        """ปุ่มที่ถูกเลือก (พื้นสีทอง) ใช้ตัวอักษรสีเข้มให้อ่านง่าย"""
        for value, button in buttons.items():
            if button.winfo_exists():
                button.config(fg=COLORS["ink"] if variable.get() == value else COLORS["text"])

    recolor()
    trace = variable.trace_add("write", recolor)
    group.bind("<Destroy>", lambda event: variable.trace_remove("write", trace)
               if event.widget is group else None)
    return group


def text_entry(parent: tk.Widget, variable: tk.StringVar = None, **options) -> tk.Entry:
    """ช่องกรอกข้อความในธีมมืด"""
    return tk.Entry(parent, textvariable=variable, font=FONT, relief="flat", bd=6, width=10,
                    bg=COLORS["panel_light"], fg=COLORS["text"], insertbackground=COLORS["text"],
                    disabledbackground=COLORS["panel"], disabledforeground=COLORS["muted"],
                    highlightthickness=1, highlightbackground=COLORS["panel_light"],
                    highlightcolor=COLORS["accent"], **options)


class ScrollableFrame(tk.Frame):
    """กรอบที่เลื่อนขึ้นลงได้ (Canvas + Scrollbar) สำหรับเนื้อหาที่ยาวเกินหน้าจอ"""

    def __init__(self, parent: tk.Widget, bg: str) -> None:
        super().__init__(parent, bg=bg)
        self.canvas = tk.Canvas(self, bg=bg, bd=0, highlightthickness=0)
        scrollbar = tk.Scrollbar(self, command=self.canvas.yview, width=12, bd=0,
                                 bg=COLORS["panel_light"], troughcolor=bg,
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
        """ลบเนื้อหาทั้งหมดและเลื่อนกลับไปบนสุด"""
        for widget in self.inner.winfo_children():
            widget.destroy()
        self.canvas.yview_moveto(0)


def _open_dialog(root: tk.Tk, title: str, message: str, color: str) -> tk.Toplevel:
    """สร้างกล่องข้อความในธีม (ส่วนหัว + ข้อความ) ให้ show_dialog และ ask_confirm ใช้ร่วมกัน"""
    dialog = tk.Toplevel(root, bg=COLORS["panel"])
    dialog.title("CASE ZERO")
    dialog.transient(root)
    dialog.resizable(False, False)
    tk.Frame(dialog, bg=color, height=6).pack(fill="x")
    tk.Label(dialog, text=title, font=type_font(title, 20), bg=COLORS["panel"], fg=color,
             padx=30).pack(pady=(18, 8))
    tk.Label(dialog, text=message, font=FONT, wraplength=440, justify="left",
             bg=COLORS["panel"], fg=COLORS["text"], padx=30).pack(pady=(0, 16))
    dialog.bind("<Escape>", lambda event: dialog.destroy())
    return dialog


def _wait_dialog(root: tk.Tk, dialog: tk.Toplevel, focus: tk.Widget) -> None:
    """วางกล่องไว้กลางหน้าต่างหลัก แล้วรอจนกว่าจะปิด"""
    dialog.update_idletasks()
    x = root.winfo_rootx() + (root.winfo_width() - dialog.winfo_width()) // 2
    y = root.winfo_rooty() + (root.winfo_height() - dialog.winfo_height()) // 3
    dialog.geometry(f"+{max(x, 0)}+{max(y, 0)}")
    focus.focus_set()
    dialog.wait_visibility()
    dialog.grab_set()
    root.wait_window(dialog)


def show_dialog(root: tk.Tk, title: str, message: str, color: str) -> None:
    """กล่องข้อความแจ้งผล มีปุ่ม OK ปุ่มเดียว"""
    dialog = _open_dialog(root, title, message, color)
    ok = flat_button(dialog, "OK", dialog.destroy, color, COLORS["panel_light"], width=10)
    ok.pack(pady=(0, 20))
    dialog.bind("<Return>", lambda event: dialog.destroy())
    _wait_dialog(root, dialog, ok)


def ask_confirm(root: tk.Tk, title: str, message: str) -> bool:
    """กล่องยืนยัน คืนค่า True เมื่อผู้ใช้กดยืนยัน"""
    answer = {"value": False}

    def confirm() -> None:
        answer["value"] = True
        dialog.destroy()

    dialog = _open_dialog(root, title, message, COLORS["danger"])
    row = tk.Frame(dialog, bg=COLORS["panel"])
    row.pack(pady=(0, 20))
    cancel = flat_button(row, get_text("ยกเลิก", "Cancel"), dialog.destroy,
                         COLORS["panel_light"], COLORS["disabled"])
    cancel.pack(side="left", padx=6)
    flat_button(row, get_text("ยืนยัน", "Confirm"), confirm,
                COLORS["danger"], COLORS["danger_dark"]).pack(side="left", padx=6)
    _wait_dialog(root, dialog, cancel)
    return answer["value"]
