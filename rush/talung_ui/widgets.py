"""Small native widgets shared by every screen of Miti Phi."""
import tkinter as tk
from tkinter import ttk
import gui_theme as theme

COLORS = theme.COLORS
COLORS.update({
    "bg": "#08141d", "panel": "#10212b", "card": "#142c35", "card_hover": "#203d45",
    "line": "#796448", "text": "#f0e2c8", "muted": "#c4b69f", "accent": "#eab363",
    "accent_dark": "#d09644", "ink": "#171a15", "amber": "#eab363", "red": "#e18b82",
    "red_dark": "#733d39", "blue": "#86b9c6", "purple": "#b6a2c5", "disabled": "#25353c",
    "screen": "#152d36", "screen_edge": "#0b202b", "moon": "#eee1c5",
    "puppet": "#0a1119", "far": "#345563", "green": "#a6bf80", "job": "#354d33",
})


def clean(text):
    return theme.tk_safe(str(text).replace("หลุดมิติผี", "มิติผี"))


def font(text="", size=11):
    return ("Leelawadee UI", size, "bold")


def label(parent, text, bg=None, fg=None, font=None, **options):
    return tk.Label(parent, text=clean(text), bg=bg or COLORS["panel"], fg=fg or COLORS["text"],
                    font=font or ("Leelawadee UI", 10), **options)


def button(parent, text, command, color=None, hover=None, fg=None, size=11, padx=12, pady=7, **options):
    color = color or COLORS["card"]
    hover = hover or COLORS["card_hover"]
    fg = fg or COLORS["text"]
    widget = tk.Button(parent, text=clean(text), command=command, font=font(text, size),
                       bg=color, fg=fg, activebackground=hover, activeforeground=fg,
                       relief="flat", bd=0, padx=padx, pady=pady, cursor="hand2",
                       highlightthickness=1, highlightbackground=COLORS["line"],
                       highlightcolor=COLORS["accent"], **options)
    widget.bind("<Enter>", lambda event: widget.config(bg=hover) if widget.cget("state") != "disabled" else None)
    widget.bind("<Leave>", lambda event: widget.config(bg=color))
    return widget


def set_button_text(widget, text, size=11):
    widget.config(text=clean(text), font=font(text, size))


class ScrollableFrame(tk.Frame):
    def __init__(self, parent, bg):
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
        self.inner = tk.Frame(self.canvas, bg=bg)
        self.window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", self._resize)
        self.canvas.bind("<Configure>", self._resize)
        for sequence in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.bind_all(sequence, self.on_wheel, add="+")

    def _resize(self, event=None):
        self.canvas.itemconfig(self.window, width=max(1, self.canvas.winfo_width()))
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    @staticmethod
    def on_wheel(event):
        widget = event.widget
        while isinstance(widget, tk.Misc) and not isinstance(widget, ScrollableFrame):
            widget = widget.master
        if not isinstance(widget, ScrollableFrame) or widget.inner.winfo_height() <= widget.canvas.winfo_height():
            return
        up = getattr(event, "num", 0) == 4 or getattr(event, "delta", 0) > 0
        widget.canvas.yview_scroll(-2 if up else 2, "units")
        return "break"

    def clear(self):
        for widget in self.inner.winfo_children():
            widget.destroy()


def open_dialog(root, title, color=None):
    dialog = tk.Toplevel(root, bg=COLORS["panel"])
    dialog.title("มิติผี · " + clean(title))
    dialog.transient(root)
    dialog.resizable(False, False)
    header = tk.Frame(dialog, bg=COLORS["bg"], padx=22, pady=14)
    header.pack(fill="x", pady=(0, 12))
    label(header, title, COLORS["bg"], color or COLORS["accent"], font(title, 20)).pack(anchor="w")
    dialog.bind("<Escape>", lambda event: dialog.destroy())
    return dialog


def install(base):
    for name, value in {"flat_button": button, "label": label, "type_font": font,
                        "set_button_text": set_button_text, "open_dialog": open_dialog,
                        "ScrollableFrame": ScrollableFrame}.items():
        setattr(theme, name, value)
        setattr(base, name, value)
    for name, size, weight in (("FONT", 11, "normal"), ("FONT_SMALL", 10, "normal"),
                              ("FONT_SMALL_BOLD", 10, "bold"), ("FONT_BOLD", 11, "bold"),
                              ("FONT_BIG", 15, "bold"), ("FONT_HUGE", 28, "bold")):
        value = ("Leelawadee UI", size, weight)
        setattr(theme, name, value)
        setattr(base, name, value)
