"""Data models for Intervals.icu responses and requests."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class Athlete:
    id: str
    name: str = ""
    ftp: Optional[int] = None
    indoor_ftp: Optional[int] = None
    eftp: Optional[int] = None
    weight: Optional[float] = None
    resting_hr: Optional[int] = None
    max_hr: Optional[int] = None
    lthr: Optional[int] = None
    power_zones: Optional[list[int]] = None
    power_zone_names: Optional[list[str]] = None
    hr_zones: Optional[list[int]] = None
    hr_zone_names: Optional[list[str]] = None
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Athlete":
        sport_settings = data.get("sportSettings") or []
        ride_settings = next(
            (s for s in sport_settings if any(t in ("Ride", "VirtualRide", "Cycling") for t in s.get("types", []))),
            sport_settings[0] if sport_settings else {}
        )

        ftp = (
            data.get("icu_ftp")
            or data.get("ftp")
            or ride_settings.get("ftp")
        )
        indoor_ftp = ride_settings.get("indoor_ftp") or ftp

        eftp = None
        mmp_model = ride_settings.get("mmp_model")
        if isinstance(mmp_model, dict):
            eftp = mmp_model.get("ftp")

        weight = data.get("weight") or data.get("icu_weight")
        resting_hr = data.get("icu_resting_hr") or data.get("restingHR")
        max_hr = (
            data.get("icu_max_hr")
            or data.get("maxHR")
            or ride_settings.get("max_hr")
        )
        lthr = ride_settings.get("lthr")
        power_zones = ride_settings.get("power_zones")
        power_zone_names = ride_settings.get("power_zone_names")
        hr_zones = ride_settings.get("hr_zones")
        hr_zone_names = ride_settings.get("hr_zone_names")

        return cls(
            id=str(data.get("id", "0")),
            name=data.get("name", "Athlete"),
            ftp=ftp,
            indoor_ftp=indoor_ftp,
            eftp=eftp,
            weight=weight,
            resting_hr=resting_hr,
            max_hr=max_hr,
            lthr=lthr,
            power_zones=power_zones,
            power_zone_names=power_zone_names,
            hr_zones=hr_zones,
            hr_zone_names=hr_zone_names,
            raw=data,
        )


@dataclass
class WellnessDay:
    date: str
    ctl: float = 0.0  # Fitness (Chronic Training Load)
    atl: float = 0.0  # Fatigue (Acute Training Load)
    tsb: float = 0.0  # Form = CTL - ATL
    resting_hr: Optional[int] = None
    hrv: Optional[float] = None
    readiness: Optional[float] = None
    soreness: Optional[int] = None  # 1-5 scale in Intervals.icu
    fatigue: Optional[int] = None   # 1-5 scale in Intervals.icu
    stress: Optional[int] = None    # 1-5 scale
    sleep_secs: Optional[int] = None
    sleep_quality: Optional[int] = None
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WellnessDay":
        ctl = float(data.get("ctl") or 0.0)
        atl = float(data.get("atl") or 0.0)
        # TSB is CTL - ATL if not explicitly provided
        tsb = float(data.get("tsb")) if data.get("tsb") is not None else (ctl - atl)

        return cls(
            date=str(data.get("id") or data.get("date", "")),
            ctl=ctl,
            atl=atl,
            tsb=tsb,
            resting_hr=data.get("restingHR"),
            hrv=data.get("hrv") or data.get("hrvSDNN"),
            readiness=data.get("readiness"),
            soreness=data.get("soreness"),
            fatigue=data.get("fatigue"),
            stress=data.get("stress"),
            sleep_secs=data.get("sleepSecs"),
            sleep_quality=data.get("sleepQuality"),
            raw=data,
        )


@dataclass
class Activity:
    id: str
    start_date_local: str
    type: str
    name: str
    moving_time_secs: int = 0
    distance_meters: float = 0.0
    training_load: float = 0.0  # TSS / icu_training_load
    intensity: Optional[float] = None  # IF
    normalized_power: Optional[float] = None  # icu_weighted_avg_watts
    avg_power: Optional[float] = None
    avg_hr: Optional[float] = None
    max_hr: Optional[float] = None
    calories: Optional[float] = None
    source: Optional[str] = None
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Activity":
        source = data.get("source")
        act_type = data.get("type")
        name = data.get("name")

        if source == "STRAVA":
            if not act_type:
                act_type = "WeightTraining"
            if not name:
                name = "Gym / Hevy (via Strava)"
        else:
            if not act_type:
                act_type = "Workout"
            if not name:
                name = "Untitled Activity"

        return cls(
            id=str(data.get("id", "")),
            start_date_local=data.get("start_date_local", ""),
            type=act_type,
            name=name,
            moving_time_secs=int(data.get("moving_time") or 0),
            distance_meters=float(data.get("distance") or 0.0),
            training_load=float(data.get("icu_training_load") or 0.0),
            intensity=data.get("icu_intensity"),
            normalized_power=data.get("icu_weighted_avg_watts"),
            avg_power=data.get("average_watts"),
            avg_hr=data.get("average_heartrate"),
            max_hr=data.get("max_heartrate"),
            calories=data.get("calories"),
            source=source,
            raw=data,
        )

    @property
    def duration_formatted(self) -> str:
        hours = self.moving_time_secs // 3600
        minutes = (self.moving_time_secs % 3600) // 60
        if hours > 0:
            return f"{hours}h {minutes:02d}m"
        return f"{minutes}m"

    @property
    def distance_km(self) -> float:
        return round(self.distance_meters / 1000.0, 1)


@dataclass
class Event:
    start_date_local: str
    type: str  # Ride, WeightTraining, Run, etc.
    name: str
    description: str
    id: Optional[str] = None
    category: str = "WORKOUT"
    load: Optional[float] = None
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Event":
        return cls(
            id=str(data.get("id")) if data.get("id") is not None else None,
            start_date_local=data.get("start_date_local", ""),
            type=data.get("type", "Ride"),
            name=data.get("name", "Planned Workout"),
            description=data.get("description", ""),
            category=data.get("category", "WORKOUT"),
            load=data.get("load"),
            raw=data,
        )

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "category": self.category,
            "start_date_local": self.start_date_local,
            "type": self.type,
            "name": self.name,
            "description": self.description,
        }
        if self.load is not None:
            payload["load"] = self.load
        return payload
