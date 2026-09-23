"""Training load and recovery analyzer for coordinating cycling and strength."""

from datetime import datetime, timedelta
from typing import Any, Optional
from .models import Activity, Athlete, Event, WellnessDay


class TrainingAnalyzer:
    """Analyzes training load, fatigue, form, and cross-discipline interference."""

    @staticmethod
    def interpret_form(tsb: float) -> tuple[str, str, str]:
        """Interprets Form (TSB = CTL - ATL).

        Returns: (status, color_tag, coaching_advice)
        """
        if tsb > 25:
            return (
                "Very Fresh / Tapered",
                "yellow",
                "High freshness. Good for racing or testing, but prolonged time here will cause fitness decay.",
            )
        elif 5 <= tsb <= 25:
            return (
                "Fresh / Race Ready",
                "green",
                "Fresh and ready for top performance or high-quality hard interval sessions.",
            )
        elif -10 <= tsb < 5:
            return (
                "Neutral / Maintenance",
                "cyan",
                "Balanced state. Good for steady base training or moderate workouts.",
            )
        elif -30 <= tsb < -10:
            return (
                "Optimal Training Zone",
                "blue",
                "Productive fatigue zone. Stimulating fitness gains without excessive overreaching.",
            )
        else:  # tsb < -30
            return (
                "High Fatigue / Overreaching",
                "bold red",
                "Excessive fatigue. High risk of non-functional overreaching or injury. Prioritize active recovery or rest.",
            )

    @staticmethod
    def summarize_status(
        athlete: Optional[Athlete],
        wellness_history: list[WellnessDay],
        recent_activities: list[Activity],
        upcoming_events: list[Event],
    ) -> dict[str, Any]:
        """Produce a comprehensive health, load, and coordination summary."""
        latest_wellness = wellness_history[-1] if wellness_history else None

        ctl = latest_wellness.ctl if latest_wellness else 0.0
        atl = latest_wellness.atl if latest_wellness else 0.0
        tsb = latest_wellness.tsb if latest_wellness else 0.0
        form_status, form_color, form_advice = TrainingAnalyzer.interpret_form(tsb)

        # Activity Breakdown (last 7 days)
        bike_activities = [a for a in recent_activities if "Ride" in a.type or "VirtualRide" in a.type or "Cycling" in a.type]
        gym_activities = [a for a in recent_activities if "WeightTraining" in a.type or "Workout" in a.type or "Gym" in a.type]
        other_activities = [a for a in recent_activities if a not in bike_activities and a not in gym_activities]

        total_load_7d = sum(a.training_load for a in recent_activities)
        bike_load_7d = sum(a.training_load for a in bike_activities)
        gym_load_7d = sum(a.training_load for a in gym_activities)
        bike_time_7d = sum(a.moving_time_secs for a in bike_activities)
        bike_dist_7d = sum(a.distance_km for a in bike_activities)

        # Interference & Recovery Checks
        recommendations: list[str] = []

        if tsb < -30:
            recommendations.append("Fatigue is very high (TSB < -30). Keep any rides strictly Zone 1/2 recovery; skip heavy leg squats/deadlifts.")
        elif tsb < -15:
            recommendations.append("Moderate-to-high fatigue. If lifting today, prioritize upper body/core or keep lower body volume submaximal (RPE 6-7).")
        else:
            recommendations.append("Readiness is good. Prime window for either high-intensity cycling intervals (VO2max/Threshold) or a hard gym session.")

        # Check recent gym leg fatigue if logged in activity names
        recent_gym_leg = any(
            "leg" in a.name.lower() or "lower" in a.name.lower() or "squat" in a.name.lower()
            for a in gym_activities[-2:]
        )
        if recent_gym_leg:
            recommendations.append("Recent lower-body gym session detected. Avoid maximal anaerobic or high-torque sprint intervals within 24-48h.")

        return {
            "athlete_name": athlete.name if athlete else "Athlete",
            "ftp": athlete.ftp if athlete else None,
            "weight": athlete.weight if athlete else None,
            "resting_hr": latest_wellness.resting_hr if latest_wellness else (athlete.resting_hr if athlete else None),
            "hrv": latest_wellness.hrv if latest_wellness else None,
            "soreness": latest_wellness.soreness if latest_wellness else None,
            "fitness_ctl": round(ctl, 1),
            "fatigue_atl": round(atl, 1),
            "form_tsb": round(tsb, 1),
            "form_status": form_status,
            "form_color": form_color,
            "form_advice": form_advice,
            "total_load_7d": round(total_load_7d, 1),
            "bike_load_7d": round(bike_load_7d, 1),
            "gym_load_7d": round(gym_load_7d, 1),
            "bike_rides_7d": len(bike_activities),
            "bike_time_7d_hours": round(bike_time_7d / 3600.0, 1),
            "bike_distance_7d_km": round(bike_dist_7d, 1),
            "gym_sessions_7d": len(gym_activities),
            "other_sessions_7d": len(other_activities),
            "recommendations": recommendations,
            "upcoming_events_count": len(upcoming_events),
        }
