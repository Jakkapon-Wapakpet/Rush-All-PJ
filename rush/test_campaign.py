"""Campaign boundary and pacing checks, using temporary saves only."""
import copy
import json
import random
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import data
import day
import menu
import realm
import storage
from language import get_language, set_language


class CampaignTests(unittest.TestCase):
    def setUp(self):
        self.original = copy.deepcopy(storage.state)
        self.language = get_language()
        folder = Path(__file__).parent / "assets" / "talung"
        token = uuid4().hex
        self.files = [folder / f"campaign-check-{token}-{kind}.json" for kind in ("save", "history")]
        self.paths = patch.multiple(storage, SAVE_FILE=str(self.files[0]), HISTORY_FILE=str(self.files[1]))
        self.paths.start()

    def tearDown(self):
        self.paths.stop()
        for file in self.files:
            file.unlink(missing_ok=True)
        storage.state.clear()
        storage.state.update(self.original)
        set_language(self.language)

    def protected_shelter(self, difficulty):
        storage.new_game(difficulty)
        storage.state["resources"] = dict.fromkeys(data.RESOURCES, 10000)
        # Remove survival randomness to exercise actual day/ending transitions.
        for person in storage.state["survivors"]:
            person["skills"]["guard"] = 100

    def test_full_campaign_ends_only_on_its_final_night(self):
        for difficulty, duration in (("easy", 15), ("normal", 20), ("nightmare", 25)):
            with self.subTest(difficulty=difficulty):
                self.protected_shelter(difficulty)
                rng = random.Random(31)
                for number in range(1, duration + 1):
                    self.assertEqual(storage.state["day"], number)
                    for person in storage.state["survivors"]:
                        person["job"] = "guard"
                    storage.state["calm"] = True
                    result = day.do_end_day(rng)
                    if number < duration:
                        self.assertEqual(result["status"], "playing")
                    else:
                        self.assertEqual(result["status"], "won")
                        self.assertEqual(result["event"], "raid")
                        self.assertFalse(result["early"])
                        self.assertTrue(any("🐯x1" in line for line in result["lines"]))
                self.assertEqual(storage.load_history()[-1]["day"], duration)

    def test_ghost_unlocks_and_boss_follow_selected_difficulty(self):
        schedules = {"easy": [3, 5, 7, 10, 15], "normal": [3, 6, 9, 13, 20],
                     "nightmare": [3, 7, 10, 16, 25]}
        for difficulty, schedule in schedules.items():
            storage.new_game(difficulty)
            self.assertEqual([storage.ghost_day(level) for level in range(1, 6)], schedule)
            for number in range(3, storage.goal_day() + 1):
                storage.state["day"] = number
                realm.make_omen(random.Random(number))
                for seed in range(8):
                    wave = day.make_wave(random.Random(seed))
                    self.assertTrue(all(schedule[level - 1] <= number for level in wave))
                    self.assertEqual(5 in wave, number == storage.goal_day())
                if realm.advanced():
                    self.assertEqual(storage.state["omen"]["actual"] == 5, number == storage.goal_day())

    def test_pressure_curve_stretches_without_increasing_peak(self):
        for difficulty, duration in (("easy", 15), ("normal", 20), ("nightmare", 25)):
            storage.new_game(difficulty)
            supplies = []
            for number in range(1, duration + 1):
                storage.state["day"] = number
                supplies.append(day.scarcity())
            self.assertAlmostEqual(supplies[0], 1)
            self.assertAlmostEqual(supplies[-1], .58)
            self.assertEqual(supplies, sorted(supplies, reverse=True))
            self.assertAlmostEqual(storage.pressure_day(), 15)

    def test_forecast_matches_wave_strength(self):
        for difficulty in data.DIFFICULTIES:
            storage.new_game(difficulty)
            storage.state["day"] = storage.goal_day()
            realm.make_omen(random.Random(7))
            powers = [day.wave_power(day.make_wave(random.Random(seed))) for seed in range(400)]
            self.assertAlmostEqual(sum(powers) / len(powers), day.expected_wave_power(), delta=3)

    def test_ticket_escape_still_works_before_new_finale(self):
        for difficulty in ("normal", "nightmare"):
            self.protected_shelter(difficulty)
            storage.state.update(day=16, tickets=data.TICKET_PIECES)
            for person in storage.state["survivors"]:
                person["job"] = "guard"
            result = day.do_end_day(random.Random(4))
            self.assertEqual(result["status"], "won")
            self.assertTrue(result["early"])

    def test_calm_vow_uses_selected_final_night(self):
        for difficulty in data.DIFFICULTIES:
            storage.new_game(difficulty)
            storage.state["day"] = storage.goal_day() - 1
            self.assertEqual(realm.do_vow("calm"), "")
            storage.state.update(day=storage.goal_day(), vow=None, calm=False)
            self.assertTrue(realm.do_vow("calm"))
            self.assertFalse(storage.state["calm"])

    def test_old_saves_keep_progress_and_finished_games_stay_finished(self):
        storage.new_game("normal")
        storage.state.update(day=15, omen={"actual": 5, "shown": 5, "whisper": None})
        storage.save_game()
        self.assertTrue(storage.load_game())
        self.assertEqual(storage.state["day"], 15)
        self.assertEqual(storage.goal_day(), 20)
        self.assertLess(storage.state["omen"]["actual"], 5)
        storage.state["status"] = "won"
        storage.save_game()
        storage.load_game()
        self.assertEqual(storage.state["status"], "won")

    def test_old_key_names_are_upgraded_on_load(self):
        storage.new_game("normal")
        old = json.loads(json.dumps(storage.state))
        old["resources"] = {"food": 3, "water": 4, "scrap": 5, "medicine": 6}
        old["log"]["gathered"] = {"food": 1, "water": 2, "scrap": 3, "medicine": 4}
        old["log"]["infected"] = old["log"].pop("possessed")
        old["log"]["biggest_horde"] = old["log"].pop("biggest_wave")
        old["buildings"] = ["barricade", "garden", "collector", "clinic"]
        old["wanderer"] = day.make_stranger(random.Random(1))
        old["wanderer"]["infected"] = old["wanderer"].pop("possessed")
        del old["stranger"]
        for person in old["survivors"]:
            person["infected"] = person.pop("possessed")
        Path(storage.SAVE_FILE).write_text(json.dumps(old), encoding="utf-8")
        self.assertTrue(storage.load_game())
        state = storage.state
        self.assertEqual(state["resources"], {"food": 3, "water": 4, "incense": 5, "holy_water": 6})
        self.assertEqual(state["log"]["gathered"]["holy_water"], 4)
        self.assertIn("possessed", state["log"])
        self.assertIn("biggest_wave", state["log"])
        self.assertEqual(state["buildings"], ["sacred_thread", "vegetable_patch", "rain_barrel", "spirit_house"])
        self.assertIn("possessed", state["stranger"])
        self.assertNotIn("wanderer", state)
        self.assertTrue(all("possessed" in person for person in state["survivors"]))
        day.do_end_day(random.Random(3))

    def test_help_displays_current_duration_in_both_languages(self):
        for difficulty, duration in (("easy", 15), ("normal", 20), ("nightmare", 25)):
            storage.new_game(difficulty)
            for language in ("th", "en"):
                set_language(language)
                self.assertIn(f"{duration} " + ("วัน" if language == "th" else "days"), menu.how_to_play_text())


if __name__ == "__main__":
    unittest.main()
