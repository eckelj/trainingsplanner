"""Unit tests for models, analyzer, and template parsing."""

import unittest
from intervals.models import Athlete, WellnessDay, Activity, Event
from intervals.analyzer import TrainingAnalyzer
from intervals.templates import CYCLING_WORKOUTS, GYM_WORKOUTS
from intervals.hevy import HevyParser


class TestIntervalsModels(unittest.TestCase):

    def test_athlete_model(self):
        data = {
            "id": "i12345",
            "name": "Test Cyclist",
            "icu_ftp": 280,
            "weight": 75.5,
            "icu_resting_hr": 48,
            "icu_max_hr": 190,
        }
        athlete = Athlete.from_dict(data)
        self.assertEqual(athlete.id, "i12345")
        self.assertEqual(athlete.name, "Test Cyclist")
        self.assertEqual(athlete.ftp, 280)
        self.assertEqual(athlete.weight, 75.5)

    def test_athlete_model_sport_settings(self):
        data = {
            "id": "i123456",
            "name": "Test Athlete",
            "icu_weight":67.0,
            "sportSettings": [
                {
                    "types": ["Ride", "VirtualRide"],
                    "ftp": 290,
                    "max_hr": 189,
                    "lthr": 175,
                    "mmp_model": {"ftp": 299},
                }
            ],
        }
        athlete = Athlete.from_dict(data)
        self.assertEqual(athlete.ftp, 290)
        self.assertEqual(athlete.weight, 67.0)
        self.assertEqual(athlete.lthr, 175)
        self.assertEqual(athlete.max_hr, 189)
        self.assertEqual(athlete.eftp, 299)

    def test_wellness_model_and_tsb(self):
        data = {
            "id": "2026-09-22",
            "ctl": 65.0,
            "atl": 75.0,
            "restingHR": 49,
            "hrv": 62.0,
            "soreness": 2,
        }
        wellness = WellnessDay.from_dict(data)
        self.assertEqual(wellness.ctl, 65.0)
        self.assertEqual(wellness.atl, 75.0)
        self.assertEqual(wellness.tsb, -10.0)

    def test_activity_formatting(self):
        data = {
            "id": "act-1",
            "start_date_local": "2026-09-21T10:00:00",
            "type": "Ride",
            "name": "Tempo Session",
            "moving_time": 5400,  # 1h 30m
            "distance": 45000,   # 45km
            "icu_training_load": 82.5,
        }
        act = Activity.from_dict(data)
        self.assertEqual(act.duration_formatted, "1h 30m")
        self.assertEqual(act.distance_km, 45.0)
        self.assertEqual(act.training_load, 82.5)

    def test_analyzer_form_interpretation(self):
        status_fresh, color_fresh, _ = TrainingAnalyzer.interpret_form(15.0)
        self.assertEqual(status_fresh, "Fresh / Race Ready")

        status_fatigue, color_fatigue, _ = TrainingAnalyzer.interpret_form(-35.0)
        self.assertEqual(status_fatigue, "High Fatigue / Overreaching")

    def test_templates_exist(self):
        self.assertIn("vo2max_intervals", CYCLING_WORKOUTS)
        self.assertIn("gym_lower_power", GYM_WORKOUTS)
        self.assertEqual(CYCLING_WORKOUTS["vo2max_intervals"]["type"], "Ride")
        self.assertEqual(GYM_WORKOUTS["gym_lower_power"]["type"], "WeightTraining")

    def test_hevy_parser(self):
        sample_rows = [
            {
                "title": "Kraft A",
                "start_time": "20 Sep 2026, 06:16",
                "end_time": "20 Sep 2026, 07:00",
                "description": "",
                "exercise_title": "Squat (Barbell)",
                "superset_id": "",
                "exercise_notes": "",
                "set_index": "0",
                "set_type": "normal",
                "weight_kg": "40",
                "reps": "10",
                "distance_km": "",
                "duration_seconds": "",
                "rpe": "8.0",
            },
            {
                "title": "Kraft A",
                "start_time": "20 Sep 2026, 06:16",
                "end_time": "20 Sep 2026, 07:00",
                "description": "",
                "exercise_title": "Squat (Barbell)",
                "superset_id": "",
                "exercise_notes": "",
                "set_index": "1",
                "set_type": "normal",
                "weight_kg": "40",
                "reps": "10",
                "distance_km": "",
                "duration_seconds": "",
                "rpe": "8.5",
            },
        ]
        workouts = HevyParser.parse_rows(sample_rows)
        self.assertEqual(len(workouts), 1)
        w = workouts[0]
        self.assertEqual(w.title, "Kraft A")
        self.assertEqual(w.duration_minutes, 44)
        self.assertEqual(w.total_volume_kg, 800.0)
        self.assertEqual(w.average_rpe, 8.2)
        self.assertTrue(w.has_leg_fatigue)
        self.assertIn("Legs (Quads & Calves)", w.muscle_focus)


if __name__ == "__main__":
    unittest.main()

