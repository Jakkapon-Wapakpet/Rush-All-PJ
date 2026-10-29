"""Title, story, dialogs and catalogs in the same colored puppet world."""
import tkinter as tk
from PIL import Image, ImageOps, ImageTk
import gui
from data import BUILDINGS, DIFFICULTIES, MAX_HP, RESOURCES, SKILLS, STORY, tr, GHOSTS
import sala
import day
import menu
import storage
import survivors
import gui_theme as theme
from language import get_text, get_language
from talung_ui import art

C = theme.COLORS


class NarrativeScreens:
    def close_title(self):
        if self.title_overlay is not None and self.title_overlay.winfo_exists():
            self.title_overlay.destroy()
        self.title_overlay = None
        self.root.focus_set()

    def show_title(self):
        self.close_title()
        overlay = tk.Frame(self.root, bg=C["bg"])
        overlay.place(x=0, y=0, relwidth=1, relheight=1)
        self.title_overlay = overlay
        self.title_stage = art.Stage("stage-color.png")
        backdrop = tk.Canvas(overlay, bg=C["bg"], highlightthickness=0)
        backdrop.place(x=0, y=0, relwidth=1, relheight=1)

        def draw(event=None):
            width, height = backdrop.winfo_width(), backdrop.winfo_height()
            if width < 2 or height < 2:
                return
            image = ImageOps.fit(self.title_stage.source, (width, height), art.LANCZOS, centering=(0.60, 0.5)).convert("RGBA")
            shade = Image.new("RGBA", image.size)
            # Runtime lighting mask keeps text readable over the authored plate.
            from PIL import ImageDraw
            pen = ImageDraw.Draw(shade)
            for x in range(width):
                alpha = round(245 * max(0.0, 1 - x / (width * 0.72)))
                pen.line((x, 0, x, height), fill=(5, 15, 23, alpha))
            image.alpha_composite(shade)
            backdrop.image = ImageTk.PhotoImage(image)
            backdrop.delete("all")
            backdrop.create_image(0, 0, image=backdrop.image, anchor="nw")
            for look, x in (("man", 0.58), ("woman", 0.73), ("big", 0.88)):
                backdrop.create_image(width * x, height * 0.89, image=art.sprite(look, 12), anchor="s")

        backdrop.bind("<Configure>", draw)
        menu = tk.Frame(overlay, bg=C["bg"], padx=24, pady=22)
        menu.place(relx=0.045, rely=0.10, width=425)
        tk.Label(menu, image=art.logo(365, 210), bg=C["bg"]).pack(pady=(0, 12))
        theme.label(menu, get_text("ดูแลคนในศาลา แล้วพาทุกคนกลับบ้าน", "Care for your people. Bring them home."),
                 C["bg"], C["text"], ("Leelawadee UI", 12), wraplength=365, justify="center").pack(pady=(0, 25))
        state = storage.state
        started = state["day"] > 1 or any(person["job"] for person in state["survivors"])

        def resume():
            self.close_title()
            if not started:
                self.show_intro()

        text = get_text(f"เล่นต่อ · วันที่ {state['day']} / {storage.goal_day()}", f"Continue · Day {state['day']} / {storage.goal_day()}") if started else get_text("เริ่มเล่น", "Start playing")
        self.resume_button = theme.flat_button(menu, text, resume, C["accent"], C["accent_dark"], fg=C["ink"], size=17, pady=12)
        self.resume_button.pack(fill="x", pady=6)
        if state["status"] != "playing":
            self.resume_button.config(text=get_text("เล่นอีกครั้ง", "Play again"), command=self.new_game)
        theme.flat_button(menu, get_text("เริ่มเกมใหม่", "New game"), self.new_game, size=15, pady=10).pack(fill="x", pady=6)
        theme.flat_button(menu, get_text("วิธีเล่น", "How to play"), self.show_help, size=13).pack(fill="x", pady=6)

        def exit_game():
            storage.save_game()
            self.root.destroy()

        theme.flat_button(menu, get_text("ออกจากเกม", "Exit game"), exit_game, C["bg"], size=11).pack(pady=(17, 0))
        languages = tk.Frame(overlay, bg=C["bg"])
        languages.place(relx=0.065, rely=0.91)
        for code, text in (("th", "TH"), ("en", "EN")):
            theme.flat_button(languages, text, lambda language=code: self.change_title_language(language),
                      C["bg"], fg=C["accent"] if code == get_language() else C["muted"], size=11).pack(side="left", padx=3)
        overlay.bind("<Return>", lambda event: self.resume_button.invoke())
        overlay.bind("<Escape>", lambda event: self.close_title())
        overlay.focus_set()

    def change_title_language(self, code):
        self.change_language(code)
        self.show_title()

    def show_intro(self):
        self.close_title()
        previous = getattr(self, "story_overlay", None)
        if previous is not None and previous.winfo_exists():
            previous.destroy()
        overlay = tk.Frame(self.root, bg=C["bg"])
        overlay.place(x=0, y=0, relwidth=1, relheight=1)
        self.story_overlay = overlay
        content = tk.Frame(overlay, bg=C["panel"], padx=25, pady=25,
                            highlightthickness=1, highlightbackground=C["line"])
        content.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.87, relheight=0.78)
        content.columnconfigure(0, weight=1, uniform="story")
        content.columnconfigure(1, weight=1, uniform="story")
        content.rowconfigure(1, weight=1)
        canvas = tk.Canvas(content, bg=C["screen"], highlightthickness=0)
        canvas.grid(row=0, column=0, rowspan=3, sticky="nsew", padx=(0, 28))
        self.story_stage = art.Stage("stage-color.png")

        def draw(event=None):
            width, height = canvas.winfo_width(), canvas.winfo_height()
            if width < 2 or height < 2:
                return
            canvas.delete("all")
            canvas.create_image(0, 0, image=self.story_stage.fit(width, height), anchor="nw")
            for look, x in (("man", 0.25), ("woman", 0.5), ("big", 0.76)):
                canvas.create_image(width * x, height * 0.91, image=art.sprite(look, 8), anchor="s")

        canvas.bind("<Configure>", draw)
        tk.Label(content, image=art.logo(240, 135), bg=C["panel"]).grid(row=0, column=1, sticky="w", pady=(0, 15))
        words = theme.label(content, "", C["panel"], C["text"], ("Leelawadee UI", 15),
                         justify="left", anchor="nw", wraplength=380)
        words.grid(row=1, column=1, sticky="nsew")
        row = tk.Frame(content, bg=C["panel"])
        row.grid(row=2, column=1, sticky="ew", pady=(20, 0))
        progress = theme.label(row, "", C["panel"], C["muted"], theme.FONT_SMALL)
        progress.pack(side="left")
        lines = STORY[get_language()]
        pages = ["\n\n".join(lines[index:index + 3]) for index in range(0, len(lines), 3)]
        page = {"index": 0}

        def close(event=None):
            overlay.destroy()
            self.root.focus_set()

        def next_page(event=None):
            if page["index"] == len(pages) - 1:
                close()
            else:
                page["index"] += 1
                update()

        self.story_next = theme.flat_button(row, "", next_page, C["accent"], C["accent_dark"], fg=C["ink"])
        self.story_next.pack(side="right")
        theme.flat_button(row, get_text("ข้าม", "Skip"), close, C["panel"], size=10).pack(side="right", padx=8)

        def update():
            words.config(text=theme.clean(pages[page["index"]]))
            progress.config(text=f"{page['index'] + 1} / {len(pages)}")
            theme.set_button_text(self.story_next, get_text("เข้าเล่น", "Enter") if page["index"] == len(pages) - 1 else get_text("ต่อไป", "Next"))

        update()
        overlay.bind("<Return>", next_page)
        overlay.bind("<Escape>", close)
        overlay.focus_set()

    def person_details(self, person):
        dialog = theme.open_dialog(self.root, person["name"], C["accent"])
        body = tk.Frame(dialog, bg=C["panel"], padx=24)
        body.pack(fill="both")
        tk.Label(body, image=art.portrait(survivors.look_of(person), 190, 245), bg=C["panel"]).pack(side="left", padx=(0, 24))
        info = tk.Frame(body, bg=C["panel"])
        info.pack(side="left", fill="both", expand=True)
        theme.label(info, f"HP {person['hp']} / {MAX_HP}", font=theme.font(size=18)).pack(anchor="w", pady=10)
        for skill, value in person["skills"].items():
            theme.label(info, f"{tr(SKILLS[skill])}   {survivors.stars(value)}", font=theme.FONT).pack(anchor="w", pady=5)
        theme.label(info, survivors.job_text(person), fg=C["green"], wraplength=260, justify="left").pack(anchor="w", pady=10)
        if person["possessed"]:
            theme.label(info, survivors.possession_text(person), fg=C["red"], wraplength=260).pack(anchor="w")

        def rename():
            dialog.destroy()
            self.rename(person)

        def exile():
            dialog.destroy()
            self.exile(person)

        theme.flat_button(info, get_text("เปลี่ยนชื่อ", "Rename"), rename, size=10).pack(fill="x", pady=(10, 3))
        if storage.state["status"] == "playing":
            theme.flat_button(info, get_text("ไล่ออกจากศาลา", "Exile"), exile, C["red_dark"], size=10).pack(fill="x", pady=3)
        close = theme.flat_button(dialog, get_text("กลับ", "Back"), dialog.destroy, size=11, padx=25)
        close.pack(pady=20)
        theme.wait_dialog(self.root, dialog, close)

    def choose_difficulty(self):
        chosen = {"key": None}
        dialog = theme.open_dialog(self.root, get_text("เริ่มการเดินทาง", "Start a new journey"))
        body = tk.Frame(dialog, bg=C["panel"], padx=20)
        body.pack(fill="x")

        def pick(key):
            chosen["key"] = key
            dialog.destroy()

        for index, (key, info) in enumerate(DIFFICULTIES.items()):
            card = tk.Frame(body, bg=C["card"], padx=16, pady=14, highlightthickness=1, highlightbackground=C["line"])
            card.grid(row=0, column=index, sticky="nsew", padx=5)
            theme.label(card, tr(info["name"]), C["card"], C["red"] if key == "nightmare" else C["accent"], theme.font(size=18)).pack(anchor="w")
            theme.label(card, get_text(f"{info['days']} วัน", f"{info['days']} days"), C["card"], C["text"], theme.font(size=14)).pack(anchor="w", pady=(5, 0))
            theme.label(card, tr(info["about"]), C["card"], C["muted"], wraplength=210, justify="left", height=5, anchor="nw").pack(pady=12)
            theme.flat_button(card, get_text("เลือกระดับนี้", "Choose"), lambda level=key: pick(level), C["job"], size=11).pack(fill="x")
        cancel = theme.flat_button(dialog, get_text("ยกเลิก", "Cancel"), dialog.destroy)
        cancel.pack(pady=18)
        theme.wait_dialog(self.root, dialog, cancel)
        return chosen["key"]

    def show_help(self):
        dialog = theme.open_dialog(self.root, get_text("วิธีดูแลศาลา", "How to manage the shelter"))
        dialog.geometry("810x650")
        area = theme.ScrollableFrame(dialog, C["panel"])
        close = theme.flat_button(dialog, get_text("เข้าใจแล้ว", "Got it"), dialog.destroy, C["accent"], C["accent_dark"], fg=C["ink"])
        close.pack(side="bottom", pady=14)
        area.pack(fill="both", expand=True, padx=24)
        for paragraph in menu.how_to_play_text().split("\n\n"):
            theme.label(area.inner, paragraph, C["panel"], C["text"], theme.FONT,
                     wraplength=720, justify="left", anchor="w").pack(fill="x", pady=(0, 14))
        theme.wait_dialog(self.root, dialog, close)

    def show_night(self, night, result):
        dialog = theme.open_dialog(self.root, get_text(f"บันทึกคืนที่ {night}", f"Night {night} report"))
        dialog.geometry("860x690")
        dialog.resizable(True, True)
        dialog.minsize(650, 500)
        summary = tk.Frame(dialog, bg=C["card"], padx=20, pady=10)
        summary.pack(fill="x", padx=22, pady=(0, 10))
        status = result["status"]
        if status == "won":
            saved = len(day.rescued())
            stars, title = day.ending_grade(saved, result.get("early", False))
            text = get_text(f"กลับบ้านได้ {saved} คน · ", f"{saved} returned home · ") + "★" * stars + "  " + title
        elif status == "lost":
            text = get_text("ไม่มีใครกลับจากมิติผี", "Nobody escaped the ghost realm")
        else:
            text = get_text(f"เช้าวันที่ {storage.state['day']} · เหลือ {len(storage.state['survivors'])} คน",
                            f"Morning {storage.state['day']} · {len(storage.state['survivors'])} survivors")
        theme.label(summary, text, C["card"], C["red"] if status == "lost" else C["accent"], theme.font(size=15), wraplength=760).pack(anchor="w")
        wave = []
        for line in result["lines"]:
            wave = gui.wave_counts(line) or wave
        if wave:
            stage = tk.Frame(dialog, bg=C["screen"])
            stage.pack(fill="x", padx=22, pady=(0, 10))
            for level, count in wave:
                figure = tk.Frame(stage, bg=C["screen"])
                figure.pack(side="left", padx=14, pady=8)
                tk.Label(figure, image=art.sprite(art.GHOST_SPRITES[level - 1], 6), bg=C["screen"]).pack()
                theme.label(figure, f"× {count}", C["screen"], C["text"], theme.FONT_SMALL).pack()
        close = theme.flat_button(dialog, get_text("กลับสู่ศาลา", "Return to shelter"), dialog.destroy,
                           C["accent"], C["accent_dark"], fg=C["ink"], padx=25)
        close.pack(side="bottom", pady=14)
        log = theme.ScrollableFrame(dialog, C["panel"])
        log.pack(fill="both", expand=True, padx=24)
        for line in result["lines"]:
            theme.label(log.inner, gui.pretty(line), C["panel"], gui.line_color(line), theme.FONT,
                     wraplength=750, justify="left", anchor="w").pack(fill="x", pady=5)
        dialog.bind("<Return>", lambda event: dialog.destroy())
        theme.wait_dialog(self.root, dialog, close)

    def draw_ending_banner(self, parent):
        won = storage.state["status"] == "won"
        frame = tk.Frame(parent, bg=C["panel"], padx=16, pady=15, highlightthickness=1, highlightbackground=C["line"])
        frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=(0, 8), pady=(0, 10))
        if won:
            saved = len(day.rescued())
            stars, title = day.ending_grade(saved, storage.state.get("escaped", False))
            text = "★" * stars + "  " + get_text(f"กลับบ้านได้ {saved} คน", f"{saved} returned home")
        else:
            text = get_text("ศาลาเงียบงัน… ไม่มีใครได้กลับบ้าน", "The shelter falls silent… Nobody returned home")
        theme.flat_button(frame, get_text("เล่นอีกครั้ง", "Play again"), self.new_game, C["accent"], C["accent_dark"], fg=C["ink"]).pack(side="right")
        theme.label(frame, text, C["panel"], C["accent"] if won else C["red"], theme.font(size=15), wraplength=500).pack(side="left")

    def draw_ghosts(self, parent):
        theme.label(parent, get_text("ผีในมิติ", "Ghosts of the realm"), font=theme.font(size=18)).pack(anchor="w", pady=(0, 10))
        for ghost in GHOSTS:
            seen = storage.ghost_day(ghost["level"]) <= storage.state["day"]
            row = tk.Frame(parent, bg=C["card"], padx=10, pady=12)
            row.pack(fill="x", pady=(0, 10))
            tk.Label(row, image=art.sprite(art.GHOST_SPRITES[ghost["level"] - 1], 7, shadow=not seen), bg=C["screen"]).pack(side="left", padx=(0, 10))
            info = tk.Frame(row, bg=C["card"])
            info.pack(side="left", fill="x", expand=True)
            theme.label(info, tr(ghost["name"]) if seen else "???", C["card"], C["text"], theme.font(size=13)).pack(anchor="w")
            theme.label(info, get_text(f"ระดับ {ghost['level']} · พลัง {ghost['power']}", f"Level {ghost['level']} · Power {ghost['power']}"), C["card"], C["muted"], theme.FONT_SMALL).pack(anchor="w")
            arrival = storage.ghost_day(ghost["level"])
            theme.label(info, get_text(f"เริ่มวันที่ {arrival}", f"Appears from day {arrival}"), C["card"], C["muted"], theme.FONT_SMALL).pack(anchor="w")
            theme.label(info, tr(ghost["about"]), C["card"], C["muted"], theme.FONT_SMALL, wraplength=170, justify="left").pack(anchor="w", pady=5)

    def draw_build(self, parent):
        theme.label(parent, get_text("ดูแลและต่อเติมศาลา", "Improve the shelter"), font=theme.font(size=17)).pack(anchor="w", pady=(0, 10))
        for key, info in BUILDINGS.items():
            built = key in storage.state["buildings"]
            card = tk.Frame(parent, bg=C["card"], padx=12, pady=12)
            card.pack(fill="x", pady=(0, 10))
            top = tk.Frame(card, bg=C["card"])
            top.pack(fill="x")
            tk.Label(top, image=art.sprite(key, 4), bg=C["card"]).pack(side="left", padx=(0, 10))
            theme.label(top, tr(info["name"]), C["card"], C["text"], theme.font(size=13), wraplength=205).pack(side="left")
            theme.label(card, tr(info["about"]), C["card"], C["muted"], theme.FONT_SMALL, wraplength=280, justify="left").pack(anchor="w", pady=6)
            cost = sala.build_cost(key)
            cost_text = " · ".join(f"{tr(RESOURCES[resource]['name'])} {amount}" for resource, amount in cost.items())
            theme.label(card, cost_text, C["card"], C["muted"], theme.FONT_SMALL).pack(anchor="w", pady=(0, 8))
            if built:
                theme.label(card, get_text("สร้างแล้ว", "Built"), C["card"], C["green"], theme.FONT_SMALL_BOLD).pack(anchor="e")
            else:
                button = theme.flat_button(card, get_text("สร้าง", "Build"), lambda building=key: self.build(building), C["job"], size=10)
                button.pack(fill="x")
                if storage.check_resources(cost):
                    button.config(state="disabled", disabledforeground=C["muted"])
