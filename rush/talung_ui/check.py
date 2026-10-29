"""Bounded integration checks using isolated game saves and real window renders."""
import hashlib
import random
import sys
import tkinter as tk
from pathlib import Path
from data import LOCATIONS, STORY
from language import get_language, set_language
import day
import storage
import survivors
from talung_ui import main as app


def digest(path):
    path = Path(path)
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def children(widget):
    for child in widget.winfo_children():
        yield child
        yield from children(child)


def capture_window(root, filename):
    from PIL import ImageGrab
    root.lift()
    root.update()
    root.after(250, root.quit)
    root.mainloop()
    image = ImageGrab.grab(window=int(root.frame(), 0))
    assert image.width >= 300 and image.height >= 150 and image.getbbox(), "Invalid capture"
    image.save(app.art.ART_DIR / filename)


def run():
    save, history = storage.SAVE_FILE, storage.HISTORY_FILE
    before = (digest(save), digest(history))
    storage.SAVE_FILE = str(app.art.ART_DIR / "check-save.json")
    storage.HISTORY_FILE = str(app.art.ART_DIR / "check-history.json")
    capture = "--capture" in sys.argv
    root = None
    errors = []
    try:
        storage.new_game("normal")
        storage.state["survivors"][0]["name"] = "เคน"
        storage.state["survivors"][1]["name"] = "แพร"
        storage.state["survivors"][2]["name"] = "ชื่อที่ผู้เล่นตั้ง"
        storage.state["fallen"] = ["บิ๊ก"]
        storage.save_game()
        assert storage.load_game()
        assert [person["name"] for person in storage.state["survivors"]] == ["กล้า", "พิกุล", "ชื่อที่ผู้เล่นตั้ง"]
        assert storage.state["fallen"] == ["สิงห์"]
        storage.new_game("normal")
        set_language("th")
        root = tk.Tk()
        root.report_callback_exception = lambda kind, value, traceback: errors.append(value)
        window = app.TalungApp(root)
        for difficulty, duration in (("easy", 15), ("normal", 20), ("nightmare", 25)):
            storage.new_game(difficulty)
            storage.state["day"] = duration - 1
            for language in ("th", "en"):
                window.change_language(language)
                root.update()
                assert window.day_label.cget("text").endswith(f"/ {duration}")
                window.show_title()
                root.update()
                assert window.resume_button.cget("text").endswith(f"/ {duration}")
                window.close_title()
        storage.new_game("normal")
        window.refresh()

        def modal(operation, filename=None, choose=False):
            def inspect_and_close():
                dialog = None
                try:
                    dialogs = [child for child in root.winfo_children() if isinstance(child, tk.Toplevel)]
                    assert len(dialogs) == 1, "Expected one modal dialog"
                    dialog = dialogs[0]
                    if capture and filename:
                        capture_window(dialog, filename)
                    buttons = [child for child in children(dialog) if isinstance(child, tk.Button)]
                    if choose:
                        buttons[0].invoke()
                    else:
                        dialog.destroy()
                except Exception as error:
                    errors.append(error)
                finally:
                    if dialog is not None and dialog.winfo_exists():
                        dialog.destroy()
            root.after(220, inspect_and_close)
            return operation()

        for name in app.art.PEOPLE + app.art.GHOST_SPRITES + ("food", "water", "incense", "holy_water", "sacred_thread", "vegetable_patch", "spirit_house", "rain_barrel"):
            for shadow in (False, True):
                image = app.art.sprite(name, 4, shadow)
                assert 0 < image.width() <= 64 and 0 < image.height() <= 64, name
        for language in ("th", "en"):
            window.change_language(language)
            for size in ("1180x780", "1440x900", "1600x1000", "1920x1080"):
                root.geometry(size)
                root.update()
                width = window.scene.winfo_width()
                assert window.stage.size == (width, max(210, min(320, round(width / 5.5))))
                assert window.stage.point(.65, .38)[1] >= 0, "Pavilion roof cropped"
                assert window.stage.point(.40, .79)[1] < window.scene.winfo_height(), "Actors outside yard"
                assert len(window.person_cards) == 3
                assert all(canvas.winfo_height() > 40 for canvas in window.portrait_canvases)
                assert window.end_button.winfo_rootx() + window.end_button.winfo_width() <= root.winfo_rootx() + root.winfo_width()
                assert window.people_view.winfo_height() > 250
                for key in app.gui.TABS:
                    window.switch_tab(key)
                    root.update()
        set_language("th")
        root.geometry("1440x900+0+0")
        window.refresh()
        root.update()
        assert "หลุด" not in root.title()
        assert modal(window.choose_difficulty, "gui-difficulty.png", choose=True) == "easy"
        person = storage.state["survivors"][0]
        assert modal(lambda: window.choose_location(person), choose=True) in LOCATIONS
        modal(lambda: window.assign(person, "scavenge"), choose=True)
        assert person["job"] == "scavenge" and person["target"] in LOCATIONS
        modal(lambda: window.person_details(person), "gui-person.png")
        modal(window.show_help, "gui-help.png")

        # New-game menu/intro are real UI flows, using only the isolated save.
        storage.new_game("normal")
        assert [person["name"] for person in storage.state["survivors"]] == ["กล้า", "พิกุล", "สิงห์"]
        window.refresh()
        window.show_title()
        root.update()
        if capture:
            capture_window(root, "gui-menu.png")
        window.resume_button.invoke()
        root.update()
        assert window.story_overlay.winfo_exists()
        if capture:
            capture_window(root, "gui-story.png")
        for _ in range((len(STORY[get_language()]) + 2) // 3):
            window.story_next.invoke()
        assert not window.story_overlay.winfo_exists()
        # A newly started game selects a difficulty before showing the story.
        modal(window.new_game, choose=True)
        assert storage.state["difficulty"] == "easy"
        for _ in range((len(STORY[get_language()]) + 2) // 3):
            window.story_next.invoke()

        storage.new_game("normal")
        storage.state["day"] = 4
        storage.state["resources"].update(food=13, water=7, incense=15, holy_water=1)
        for person, hp, job in zip(storage.state["survivors"], (80, 45, 90), ("scavenge", "heal", "guard")):
            person.update(hp=hp, job=job)
        guest = day.make_stranger(random.Random(7))
        guest["name"] = "ชบา"
        storage.state["stranger"] = guest
        window.tab = "gate"
        window.refresh()
        root.update()
        if capture:
            capture_window(root, "gui-desktop.png")
            root.geometry("1600x1000+0+0")
            root.update()
            capture_window(root, "gui-wide.png")
            root.geometry("1440x900+0+0")
            root.update()
        assert len(window.person_cards) == 3
        # Check job popup dispatch without changing the core game's assignment.
        for person in storage.state["survivors"]:
            assert survivors.job_text(person)
        for name, look in (("บัว", "girl"), ("ลุงเพิ่ม", "elder"), ("เทียน", "man")):
            storage.state["survivors"].append(storage.new_survivor(name, {"scavenge": 2, "guard": 2, "heal": 2}, look))
            window.refresh()
            root.update()
            for card in window.person_cards:
                assert card.winfo_y() + card.winfo_height() <= window.people_view.winfo_height()
        storage.state["survivors"][1]["possessed"] = 1
        storage.state["day"] = storage.goal_day()
        for language in ("en", "th"):
            window.change_language(language)
            root.geometry("1180x780")
            root.update()
            assert len(window.person_cards) == 6 and len(window.blink_cards) == 1
            for card in window.person_cards:
                assert card.winfo_y() >= 0
                assert card.winfo_y() + card.winfo_height() <= window.people_view.winfo_height()
                for control in children(card):
                    if isinstance(control, tk.Button):
                        assert control.winfo_ismapped(), "Card action clipped"
            assert all(canvas.winfo_height() > 40 for canvas in window.portrait_canvases)
        if capture:
            capture_window(root, "gui-small.png")
        window.switch_tab("ghosts")
        root.update()
        if capture:
            capture_window(root, "gui-ghosts.png")

        storage.new_game("easy")
        survivors.do_auto_assign()
        result = day.do_end_day(random.Random(42))
        assert storage.state["day"] == 2
        modal(lambda: window.show_night(1, result), "gui-night.png")
        # Synthetic presentation cases cover all report endings and raid art.
        for status in ("won", "lost"):
            sample = dict(result, status=status, lines=["👻x2 🔥x1 🦴x1 👺x1 🐯x1 = พลัง 24 vs พลังป้องกัน 20"])
            modal(lambda report=sample: window.show_night(storage.goal_day(), report))
        for status in ("won", "lost"):
            storage.state["status"] = status
            window.refresh()
            root.update()
        assert not errors, repr(errors)
        assert before == (digest(save), digest(history)), "Real save changed"
        print("PASS: colored art, 4 sizes x TH/EN, shared scene/actor scale, unclipped roof, all tabs, 3-6 people fit without roster scrolling, old-name migration preserves custom names, difficulty, assignment, dialogs, title/story/new game, possession, night/endings; real saves unchanged")
    finally:
        if root:
            root.destroy()
        storage.SAVE_FILE, storage.HISTORY_FILE = save, history
