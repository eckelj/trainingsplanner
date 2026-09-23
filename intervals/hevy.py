"""Parser and data structures for Hevy workout CSV exports."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


@dataclass
class HevySet:
    set_index: int
    set_type: str = "normal"
    weight_kg: Optional[float] = None
    reps: Optional[int] = None
    distance_km: Optional[float] = None
    duration_seconds: Optional[int] = None
    rpe: Optional[float] = None
    notes: str = ""


@dataclass
class HevyExercise:
    title: str
    sets: list[HevySet] = field(default_factory=list)
    notes: str = ""

    @property
    def total_volume_kg(self) -> float:
        """Total volume in kilograms (weight * reps)."""
        vol = 0.0
        for s in self.sets:
            if s.weight_kg and s.reps:
                vol += s.weight_kg * s.reps
        return vol

    @property
    def sets_summary(self) -> str:
        """Formatted summary of sets, weights, and RPE."""
        if not self.sets:
            return ""
        
        # Check if duration-based (e.g. Plank)
        durations = [s.duration_seconds for s in self.sets if s.duration_seconds]
        if durations and len(durations) == len(self.sets):
            avg_dur = int(sum(durations) / len(durations))
            return f"{len(self.sets)} sets (~{avg_dur}s)"

        weights = [s.weight_kg for s in self.sets if s.weight_kg is not None]
        reps = [s.reps for s in self.sets if s.reps is not None]
        rpes = [s.rpe for s in self.sets if s.rpe is not None]

        summary_parts = []
        if reps:
            avg_reps = int(sum(reps) / len(reps))
            summary_parts.append(f"{len(self.sets)}x{avg_reps}")
        else:
            summary_parts.append(f"{len(self.sets)} sets")

        if weights:
            unique_weights = []
            for w in weights:
                w_str = f"{w:.1f}kg".replace(".0kg", "kg")
                if w_str not in unique_weights:
                    unique_weights.append(w_str)
            summary_parts.append(f"({', '.join(unique_weights)})")

        if rpes:
            min_rpe = min(rpes)
            max_rpe = max(rpes)
            if min_rpe == max_rpe:
                summary_parts.append(f"@ RPE {min_rpe:.1f}")
            else:
                summary_parts.append(f"@ RPE {min_rpe:.1f}-{max_rpe:.1f}")

        return " ".join(summary_parts)


@dataclass
class HevyWorkout:
    title: str
    start_time: datetime
    end_time: datetime
    description: str = ""
    exercises: list[HevyExercise] = field(default_factory=list)

    @property
    def duration_seconds(self) -> int:
        return max(int((self.end_time - self.start_time).total_seconds()), 0)

    @property
    def duration_minutes(self) -> int:
        return max(int(self.duration_seconds / 60), 1)

    @property
    def total_volume_kg(self) -> float:
        return sum(e.total_volume_kg for e in self.exercises)

    @property
    def average_rpe(self) -> Optional[float]:
        rpes: list[float] = []
        for e in self.exercises:
            for s in e.sets:
                if s.rpe is not None:
                    rpes.append(s.rpe)
        if not rpes:
            return None
        return round(sum(rpes) / len(rpes), 1)

    @property
    def muscle_focus(self) -> list[str]:
        focus: list[str] = []
        titles = [e.title.lower() for e in self.exercises]

        # Quads / Knee flexion
        if any(any(k in t for k in ["squat", "split squat", "leg press", "lunge", "calf"]) for t in titles):
            focus.append("Legs (Quads & Calves)")

        # Posterior chain / Hip hinge
        if any(any(k in t for k in ["deadlift", "romanian", "rdl", "hip thrust", "hamstring"]) for t in titles):
            focus.append("Legs (Posterior Chain & Hinge)")

        # Upper Pull
        if any(any(k in t for k in ["pulldown", "pull-up", "chin-up", "row"]) for t in titles):
            focus.append("Upper (Pull)")

        # Upper Push
        if any(any(k in t for k in ["bench press", "overhead press", "shoulder press", "push-up", "dip"]) for t in titles):
            focus.append("Upper (Push)")

        # Core
        if any(any(k in t for k in ["pallof", "plank", "dead bug", "bird dog", "farmers walk", "ab"]) for t in titles):
            focus.append("Core & Stability")

        return focus

    @property
    def has_leg_fatigue(self) -> bool:
        """True if the session involved significant lower body loading."""
        return any("Legs" in f for f in self.muscle_focus)

    @property
    def training_load(self) -> float:
        """Estimated Training Load (TSS) using Foster's session-RPE method."""
        rpe = self.average_rpe if self.average_rpe else 7.0
        # Scaled load: 45 min @ RPE 8 ~ 36 TSS
        return round(self.duration_minutes * (rpe / 10.0), 1)

    @property
    def formatted_description(self) -> str:
        """Markdown formatted description for Intervals.icu."""
        focus_str = ", ".join(self.muscle_focus) if self.muscle_focus else "General Strength"
        rpe_str = f"{self.average_rpe:.1f}" if self.average_rpe else "N/A"
        
        lines = [
            f"🏋 Hevy Strength Workout: {self.title}",
            f"Duration: {self.duration_minutes}m | Volume: {self.total_volume_kg:,.0f} kg | Avg RPE: {rpe_str} | Load: {self.training_load:.0f} TSS",
            f"Focus: {focus_str}",
            "",
            "Exercises & Sets:",
        ]

        for ex in self.exercises:
            lines.append(f"• {ex.title}: {ex.sets_summary}")

        return "\n".join(lines)


class HevyParser:
    """Parses Hevy CSV export files."""

    DATE_FORMAT = "%d %b %Y, %H:%M"

    @classmethod
    def parse_file(cls, filepath: str | Path) -> list[HevyWorkout]:
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Hevy CSV file not found: {filepath}")

        with path.open(mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return cls.parse_rows(list(reader))

    @classmethod
    def parse_rows(cls, rows: list[dict[str, Any]]) -> list[HevyWorkout]:
        # Group rows by (title, start_time, end_time)
        workouts_map: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
        for row in rows:
            key = (row.get("title", "Workout"), row.get("start_time", ""), row.get("end_time", ""))
            if key not in workouts_map:
                workouts_map[key] = []
            workouts_map[key].append(row)

        workouts: list[HevyWorkout] = []
        for (title, start_str, end_str), w_rows in workouts_map.items():
            if not start_str or not end_str:
                continue

            try:
                start_dt = datetime.strptime(start_str, cls.DATE_FORMAT)
                end_dt = datetime.strptime(end_str, cls.DATE_FORMAT)
            except ValueError:
                continue

            # Group exercises in order of appearance
            exercises_dict: dict[str, HevyExercise] = {}
            for r in w_rows:
                ex_title = r.get("exercise_title", "Exercise")
                if ex_title not in exercises_dict:
                    exercises_dict[ex_title] = HevyExercise(
                        title=ex_title,
                        notes=r.get("exercise_notes", ""),
                    )

                def _to_float(v: Any) -> Optional[float]:
                    if v is None or v == "":
                        return None
                    try:
                        return float(v)
                    except ValueError:
                        return None

                def _to_int(v: Any) -> Optional[int]:
                    if v is None or v == "":
                        return None
                    try:
                        return int(float(v))
                    except ValueError:
                        return None

                # Weight column could be weight_kg or weight_lbs
                weight = _to_float(r.get("weight_kg"))
                if weight is None and r.get("weight_lbs"):
                    lbs = _to_float(r.get("weight_lbs"))
                    if lbs is not None:
                        weight = round(lbs * 0.45359237, 1)

                set_item = HevySet(
                    set_index=_to_int(r.get("set_index")) or 0,
                    set_type=r.get("set_type", "normal"),
                    weight_kg=weight,
                    reps=_to_int(r.get("reps")),
                    distance_km=_to_float(r.get("distance_km")),
                    duration_seconds=_to_int(r.get("duration_seconds")),
                    rpe=_to_float(r.get("rpe")),
                    notes=r.get("exercise_notes", ""),
                )
                exercises_dict[ex_title].sets.append(set_item)

            workout = HevyWorkout(
                title=title,
                start_time=start_dt,
                end_time=end_dt,
                description=w_rows[0].get("description", ""),
                exercises=list(exercises_dict.values()),
            )
            workouts.append(workout)

        # Sort by start_time descending
        workouts.sort(key=lambda w: w.start_time, reverse=True)
        return workouts
