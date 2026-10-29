"""Miti Phi: colored Nang Talung management GUI, sharing original rules/saves."""
import sys
import tkinter as tk
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gui
from data import JOBS, MAX_PEOPLE, MAX_HP, RAID_START_DAY, RESOURCES, tr, GHOSTS
import sala
import realm
import storage
import survivors
import gui_theme as theme
from language import get_text, get_language
from talung_ui import art
from talung_ui.screens import NarrativeScreens

COLORS = theme.COLORS


class TalungApp(NarrativeScreens, gui.SalaApp):
    def __init__(self, root):
        self.stage = art.Stage()
        self.title_overlay = None
        self.portrait_canvases = []
        self.person_cards = []
        super().__init__(root)
        root.geometry("1440x900")
        root.minsize(1180, 780)
        root.title("มิติผี · GHOST REALM")
        root.bind("<F1>", lambda event: self.show_help())

    def build_layout(self):
        header = tk.Frame(self.root, bg=COLORS["bg"], padx=18, pady=10)
        header.pack(fill="x")
        self.logo = theme.flat_button(header, "มิติผี", self.show_title, COLORS["bg"], size=22, padx=7, pady=0)
        self.logo.pack(side="left", padx=(0, 10))
        self.day_label = theme.label(header, "", COLORS["bg"], COLORS["text"], theme.font(size=13))
        self.day_label.pack(side="left", padx=(0, 15))
        settings = tk.Frame(header, bg=COLORS["bg"])
        settings.pack(side="right")
        theme.flat_button(settings, get_text("เมนู", "Menu"), self.show_title, size=10, padx=8, pady=5).pack(side="left", padx=4)
        self.lang_buttons = {}
        for code, title in (("th", "TH"), ("en", "EN")):
            button = theme.flat_button(settings, title, lambda lang=code: self.change_language(lang), COLORS["bg"], size=9, padx=5, pady=5)
            button.pack(side="left", padx=1)
            self.lang_buttons[code] = button
        self.resource_bar = tk.Frame(header, bg=COLORS["bg"])
        self.resource_bar.pack(side="left", fill="x", expand=True)
        tk.Frame(self.root, bg=COLORS["line"], height=1).pack(fill="x", padx=18)
        footer = tk.Frame(self.root, bg=COLORS["bg"], padx=18, pady=10)
        footer.pack(side="bottom", fill="x")
        actions = tk.Frame(footer, bg=COLORS["bg"])
        actions.pack(side="right")
        self.end_button = theme.flat_button(actions, "", self.end_day, COLORS["accent"], COLORS["accent_dark"], fg=COLORS["ink"], size=13, padx=22, pady=9)
        self.end_button.pack(side="right")
        self.auto_button = theme.flat_button(actions, "", self.auto_assign, padx=16, pady=9)
        self.auto_button.pack(side="right", padx=10)
        self.message_label = theme.label(footer, "", COLORS["bg"], font=theme.FONT_SMALL, anchor="w", justify="left", wraplength=600)
        self.message_label.pack(fill="x", anchor="w", pady=(0, 4))
        threat = tk.Frame(footer, bg=COLORS["bg"])
        threat.pack(fill="x")
        self.defense_label = theme.label(threat, "", COLORS["bg"], COLORS["muted"], theme.FONT_SMALL)
        self.defense_label.pack(side="left")
        self.threat_bar = tk.Canvas(threat, width=260, height=5, bg=COLORS["disabled"], highlightthickness=0)
        self.threat_bar.pack(side="left", padx=10)
        body = tk.Frame(self.root, bg=COLORS["bg"], padx=18, pady=10)
        body.pack(fill="both", expand=True)
        right = tk.Frame(body, bg=COLORS["panel"], width=350, highlightthickness=1, highlightbackground=COLORS["line"])
        right.pack(side="right", fill="y", padx=(14, 0))
        right.pack_propagate(False)
        self.tab_bar = tk.Frame(right, bg=COLORS["bg"])
        self.tab_bar.pack(fill="x")
        self.tab_view = theme.ScrollableFrame(right, COLORS["panel"])
        self.tab_view.pack(fill="both", expand=True, padx=12, pady=12)
        left = tk.Frame(body, bg=COLORS["bg"])
        left.pack(side="left", fill="both", expand=True)
        self.scene = tk.Canvas(left, height=210, bg=COLORS["screen"], highlightthickness=0)
        self.scene.pack(fill="x", pady=(0, 9))
        self.scene.bind("<Configure>", lambda event: self.draw_scene())
        self.left_title = tk.Frame(left, bg=COLORS["bg"])
        self.left_title.pack(fill="x", pady=(0, 7))
        self.people_view = tk.Frame(left, bg=COLORS["bg"])
        self.people_view.pack(fill="both", expand=True)
        self.people_view.pack_propagate(False)

    def draw_header(self):
        state = storage.state
        self.logo.config(text=get_text("มิติผี", "GHOST REALM"), font=theme.font(size=20 if get_language() == "th" else 15))
        self.day_label.config(text=get_text(f"วันที่ {state['day']} / {storage.goal_day()}", f"Day {state['day']} / {storage.goal_day()}"))
        for child in self.resource_bar.winfo_children():
            child.destroy()
        for column, (key, info) in enumerate(RESOURCES.items()):
            self.resource_bar.columnconfigure(column, weight=1, uniform="stock")
            group = tk.Frame(self.resource_bar, bg=COLORS["bg"])
            group.grid(row=0, column=column, sticky="ew", padx=5)
            tk.Label(group, image=art.sprite(key, 3), bg=COLORS["bg"]).pack(side="left", padx=(0, 6))
            words = tk.Frame(group, bg=COLORS["bg"])
            words.pack(side="left")
            theme.label(words, tr(info["name"]), COLORS["bg"], COLORS["muted"], theme.FONT_SMALL).pack(anchor="w")
            color = COLORS["red"] if key in ("food", "water") and sala.days_left(key) <= 1 else COLORS["text"]
            theme.label(words, state["resources"][key], COLORS["bg"], color, theme.font(size=17)).pack(anchor="w")
        for code, button in self.lang_buttons.items():
            button.config(fg=COLORS["accent"] if code == get_language() else COLORS["muted"])

    def draw_scene(self):
        canvas = self.scene
        canvas.delete("all")
        width = canvas.winfo_width()
        if width < 50:
            return
        height = max(210, min(320, round(width / 5.5)))
        if int(canvas.cget("height")) != height:
            canvas.configure(height=height)
        canvas.create_image(0, 0, image=self.stage.fit(width, height), anchor="nw")
        state = storage.state
        base = self.stage.point(0, .79)[1]
        actor_scale = max(1, round(175 * self.stage.scale / 16))
        people = state["survivors"]
        spacing = min(.10, .44 / max(1, len(people) - 1))
        for index, person in enumerate(state["survivors"]):
            x = self.stage.point(.40 + (index - (len(people) - 1) / 2) * spacing, .79)[0]
            canvas.create_image(x, base, image=art.sprite(survivors.look_of(person), actor_scale), anchor="s", tags="survivor")
            if person["possessed"]:
                head = base - actor_scale * 16 - 6
                canvas.create_oval(x - 2, head, x + 2, head + 4, fill=COLORS["red"], outline="")
        for index, building in enumerate(state["buildings"]):
            canvas.create_image(40 + index * 45, base, image=art.sprite(building, 3), anchor="s")
        if state["status"] == "playing" and state["day"] >= RAID_START_DAY:
            kinds = [ghost for ghost in GHOSTS if storage.ghost_day(ghost["level"]) <= state["day"]]
            for index, ghost in enumerate(kinds[-2:]):
                canvas.create_image(width * (0.10, 0.92)[index], base,
                                    image=art.sprite(art.GHOST_SPRITES[ghost["level"] - 1], actor_scale), anchor="s")
        if state.get("stranger") and state["status"] == "playing":
            canvas.create_image(self.stage.point(.82, .79)[0], base, image=art.sprite("stranger", actor_scale), anchor="s")
        note = realm.omen_text() if realm.advanced() else ""
        if note:
            canvas.create_rectangle(0, 0, width, 29, fill=COLORS["bg"], outline="")
            canvas.create_text(10, 6, anchor="nw", width=width - 20, text=theme.clean(note), fill=COLORS["text"], font=("Leelawadee UI", 9))

    def draw_people(self):
        for child in self.left_title.winfo_children():
            child.destroy()
        people = storage.state["survivors"]
        theme.label(self.left_title, get_text(f"คนในศาลา  {len(people)} / {MAX_PEOPLE}", f"Survivors  {len(people)} / {MAX_PEOPLE}"),
                 COLORS["bg"], font=theme.font(size=11)).pack(side="left")
        idle = sum(person["job"] is None for person in people)
        theme.label(self.left_title, get_text(f"ยังว่าง {idle} คน", f"{idle} unassigned"), COLORS["bg"], COLORS["muted"], theme.FONT_SMALL).pack(side="right")
        for child in self.people_view.winfo_children():
            child.destroy()
        self.blink_cards, self.person_cards, self.portrait_canvases = [], [], []
        grid = self.people_view
        for column in range(3):
            grid.columnconfigure(column, weight=1, uniform="people")
        rows = (len(people) + 2) // 3
        ended = storage.state["status"] != "playing"
        for row in range(3):
            grid.rowconfigure(row, weight=0, minsize=0, uniform="")
        for row in range(rows):
            grid.rowconfigure(row + int(ended), weight=1, uniform="people")
        if storage.state["status"] != "playing":
            self.draw_ending_banner(grid)
        for index, person in enumerate(people):
            card = self.person_card(grid, person)
            card.grid(row=index // 3 + int(ended), column=index % 3, sticky="nsew", padx=(0, 8), pady=(0, 9))
            card.grid_propagate(False)
            card.pack_propagate(False)
            self.person_cards.append(card)

    def person_card(self, parent, person):
        bg = COLORS["card"]
        compact = len(storage.state["survivors"]) > 3
        card = tk.Frame(parent, bg=bg, highlightthickness=1, highlightbackground=COLORS["red"] if person["possessed"] else COLORS["line"])
        if person["possessed"]:
            self.blink_cards.append(card)
        portrait = tk.Canvas(card, height=1, width=1, bg=bg, highlightthickness=0)
        content = tk.Frame(card, bg=bg, width=1)
        if compact:
            card.columnconfigure(0, weight=2, uniform="parts")
            card.columnconfigure(1, weight=3, uniform="parts")
            card.rowconfigure(0, weight=1)
            portrait.grid(row=0, column=0, sticky="nsew")
            content.grid(row=0, column=1, sticky="nsew")
            content.pack_propagate(False)
        else:
            portrait.pack(fill="both", expand=True)
            content.pack(fill="x")
        look = survivors.look_of(person)

        def fit(event=None):
            portrait.image = art.portrait(look, max(1, portrait.winfo_width()), max(15, portrait.winfo_height()))
            portrait.delete("all")
            portrait.create_image(0, 0, image=portrait.image, anchor="nw")

        portrait.bind("<Configure>", fit)
        self.portrait_canvases.append(portrait)
        theme.flat_button(content if compact else portrait, "⋯", lambda: self.person_details(person), size=10 if compact else 12, padx=3 if compact else 5, pady=0).place(relx=1, x=-3 if compact else -8, y=3 if compact else 7, anchor="ne")
        theme.label(content, person["name"], bg, font=theme.font(size=12 if compact else 16)).pack(pady=(27 if compact else 5, 1))
        health = tk.Frame(content, bg=bg, padx=6 if compact else 12)
        health.pack(fill="x")
        theme.label(health, f"HP {person['hp']}/{MAX_HP}", bg, COLORS["text"], theme.FONT_SMALL).pack(side="top" if compact else "left", padx=(0, 0 if compact else 8))
        color = COLORS["green"] if person["hp"] >= 70 else COLORS["amber"] if person["hp"] >= 40 else COLORS["red"]
        theme.meter(health, person["hp"] / MAX_HP, color, height=7).pack(side="top" if compact else "left", fill="x", expand=True)
        job_text = tr(gui.JOB_SHORT[person["job"]]) if compact and person["job"] in gui.JOB_SHORT else survivors.job_text(person)
        job_button = theme.flat_button(content, job_text + "  ▾", lambda: None,
                               COLORS["job"], COLORS["card_hover"], size=10 if compact else 11, pady=3 if compact else 7)
        job_button.pack(fill="x", padx=4 if compact else 10, pady=(5, 3) if compact else (9, 6))
        job_button.config(command=lambda: self.job_menu(person, job_button))
        if storage.state["status"] != "playing" or person["job"] == "inspect":
            job_button.config(state="disabled", disabledforeground=COLORS["muted"])
        if person["possessed"]:
            theme.label(content, get_text("ถูกผีสิง", "Possessed"), bg, COLORS["red"], ("Leelawadee UI", 9)).pack(padx=4, pady=(0, 2))
        return card

    def job_menu(self, person, anchor):
        menu = tk.Menu(self.root, tearoff=False, bg=COLORS["panel"], fg=COLORS["text"], activebackground=COLORS["job"],
                        activeforeground=COLORS["text"], font=("Leelawadee UI", 11))
        for job in survivors.assignable_jobs():
            menu.add_command(label=theme.clean(tr(JOBS[job]["name"])), command=lambda key=job: self.assign(person, key),
                             state="disabled" if survivors.check_job(person, job) else "normal")
        try:
            menu.tk_popup(anchor.winfo_rootx(), anchor.winfo_rooty() + anchor.winfo_height())
        finally:
            menu.grab_release()

    def draw_tabs(self):
        for child in self.tab_bar.winfo_children():
            child.destroy()
        names = {"gate": get_text("ประตู", "Gate"), "build": get_text("สร้าง", "Build"), "tonight": get_text("คืนนี้", "Tonight"),
                 "shrine": get_text("ศาลเจ้า", "Shrine"), "ghosts": get_text("ผี", "Ghosts"), "log": get_text("บันทึก", "Log")}
        tabs = [key for key in gui.TABS if realm.advanced() or key not in gui.ADVANCED_TABS]
        if self.tab not in tabs:
            self.tab = "gate"
        for column in range(3):
            self.tab_bar.columnconfigure(column, weight=1, uniform="tabs")
        for index, key in enumerate(tabs):
            active = key == self.tab
            title = names[key] + (" !" if key == "gate" and storage.state["stranger"] else "")
            theme.flat_button(self.tab_bar, title, lambda tab=key: self.switch_tab(tab), COLORS["card_hover"] if active else COLORS["bg"],
                      fg=COLORS["accent"] if active else COLORS["muted"], size=10, padx=4, pady=9).grid(row=index // 3, column=index % 3, sticky="ew")
        self.tab_view.clear()
        self.tab_view.canvas.yview_moveto(0)
        {"gate": self.draw_gate, "build": self.draw_build, "tonight": self.draw_tonight, "shrine": self.draw_shrine,
         "ghosts": self.draw_ghosts, "log": self.draw_log}[self.tab](self.tab_view.inner)

    def draw_gate(self, parent):
        state, bg = storage.state, COLORS["panel"]
        guest = state["stranger"] if state["status"] == "playing" else None
        theme.label(parent, get_text("มีคนมาที่ประตู", "Someone at the gate") if guest else get_text("ประตูศาลา", "Shelter gate"), bg,
                 font=theme.font(size=18)).pack(pady=(0, 10))
        tk.Label(parent, image=art.portrait("stranger", 286, 210, shadow=not guest), bg=bg).pack(fill="x")
        if not guest:
            theme.label(parent, get_text("วันนี้ยังไม่มีผู้มาเยือน", "No visitors today"), bg, COLORS["muted"], theme.FONT_BOLD).pack(pady=15)
            theme.label(parent, get_text("ดูแลคนในศาลา เตรียมพร้อมสำหรับคืนนี้", "Care for your people. Prepare for tonight."),
                     bg, COLORS["muted"], theme.FONT_SMALL, wraplength=285, justify="center").pack()
            return
        theme.label(parent, guest["name"], bg, font=theme.font(size=19)).pack(pady=(8, 2))
        if guest["checked"]:
            note = get_text("เงาผิดปกติ — ถูกผีสิง", "Abnormal shadow — possessed") if guest["possessed"] else get_text("เงาปกติ — ปลอดภัย", "Normal shadow — safe")
        else:
            note = get_text("ยังไม่ได้ส่องดูเงา", "Shadow not inspected")
        theme.label(parent, note, bg, COLORS["red"] if guest["checked"] and guest["possessed"] else COLORS["muted"], theme.FONT_SMALL).pack(pady=(0, 12))
        if not guest["checked"]:
            theme.flat_button(parent, get_text("ส่องดูเงา", "Check shadow"), self.inspect, COLORS["accent"], COLORS["accent_dark"], fg=COLORS["ink"], size=12).pack(fill="x", pady=3)
        theme.flat_button(parent, get_text("รับเข้าศาลา", "Let in"), self.accept, COLORS["job"], size=12).pack(fill="x", pady=3)
        theme.flat_button(parent, get_text("ไม่รับ", "Turn away"), self.reject, size=11).pack(fill="x", pady=3)
        theme.label(parent, get_text("เพิ่มอาหารและน้ำอย่างละ 1 ต่อวัน", "+1 food and +1 water per day"), bg, COLORS["muted"], theme.FONT_SMALL).pack(pady=7)
        details = tk.Frame(parent, bg=bg)

        def reveal():
            details.pack_forget() if details.winfo_ismapped() else details.pack(fill="x", pady=8)

        theme.flat_button(parent, get_text("ข้อมูลผู้มาเยือน", "Visitor details"), reveal, bg, size=10).pack(fill="x")
        theme.label(details, f"HP {guest['hp']}/{MAX_HP}", bg, font=theme.FONT_SMALL).pack(anchor="w")
        gui.skills_grid(details, guest["skills"], bg).pack(fill="x", pady=7)
        for line in realm.story_lines(guest):
            theme.label(details, line, bg, COLORS["muted"], theme.FONT_SMALL, wraplength=280, justify="left").pack(anchor="w")

    def draw_chart(self, parent, days):
        width, height, pad = 290, 135, 22
        canvas = tk.Canvas(parent, width=width, height=height, bg=COLORS["card"], highlightthickness=0)
        canvas.pack(fill="x")
        if len(days) < 2:
            canvas.create_text(width // 2, height // 2, width=250, fill=COLORS["muted"], text=get_text("กราฟจะแสดงหลังผ่านไป 2 วัน", "Chart available after two days"), font=theme.FONT_SMALL)
            return
        top = max(max(day["food"], day["water"]) for day in days) or 1
        for key, color, offset in (("food", COLORS["green"], 0), ("water", COLORS["blue"], 100)):
            points = []
            for index, entry in enumerate(days):
                points.extend((pad + index * (width - pad * 2) / (storage.goal_day() - 1), height - pad - entry[key] / top * (height - pad * 2)))
            canvas.create_line(*points, fill=color, width=2)
            canvas.create_text(pad + offset, 10, anchor="w", fill=color, text=tr(RESOURCES[key]["name"]), font=theme.FONT_SMALL)


def main():
    if "--check" in sys.argv:
        from talung_ui.check import run
        run()
        return
    storage.load_game()
    root = tk.Tk()
    app = TalungApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (storage.save_game(), root.destroy()))
    root.after(100, app.show_title)
    root.mainloop()


if __name__ == "__main__":
    main()
