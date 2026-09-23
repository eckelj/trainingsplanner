"""HTTP Client for Intervals.icu REST API."""

import os
from typing import Any, Optional
import requests
from dotenv import load_dotenv

from .models import Activity, Athlete, Event, WellnessDay

load_dotenv()


class IntervalsAPIError(Exception):
    """Custom exception for Intervals.icu API errors."""
    def __init__(self, status_code: int, message: str):
        super().__init__(f"Intervals.icu API Error [{status_code}]: {message}")
        self.status_code = status_code
        self.message = message


class IntervalsClient:
    """Client for interacting with Intervals.icu API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        athlete_id: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("INTERVALS_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Intervals.icu API Key is required. Set INTERVALS_API_KEY in .env or pass it to constructor."
            )

        self.athlete_id = athlete_id or os.getenv("INTERVALS_ATHLETE_ID", "0")
        self.base_url = (base_url or os.getenv("INTERVALS_API_BASE", "https://intervals.icu/api/v1")).rstrip("/")
        self.session = requests.Session()
        # Intervals.icu uses HTTP Basic Auth: Username "API_KEY", Password = your_api_key
        self.session.auth = ("API_KEY", self.api_key)
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
        })

    def _url(self, path: str) -> str:
        return f"{self.base_url}/athlete/{self.athlete_id}/{path.lstrip('/')}"

    def _handle_response(self, response: requests.Response) -> Any:
        if not response.ok:
            error_text = response.text
            try:
                err_json = response.json()
                if "error" in err_json:
                    error_text = err_json["error"]
                elif "message" in err_json:
                    error_text = err_json["message"]
            except Exception:
                pass
            raise IntervalsAPIError(response.status_code, error_text)

        if response.status_code == 204:
            return None
        return response.json()

    def get_athlete(self) -> Athlete:
        """Fetch athlete profile (FTP, Max HR, Resting HR, weight)."""
        url = f"{self.base_url}/athlete/{self.athlete_id}"
        resp = self.session.get(url)
        data = self._handle_response(resp)
        return Athlete.from_dict(data)

    def get_wellness(self, oldest: str, newest: str) -> list[WellnessDay]:
        """Fetch wellness data (Fitness CTL, Fatigue ATL, Form TSB, HRV, resting HR).

        Dates formatted as YYYY-MM-DD.
        """
        url = self._url("wellness")
        params = {"oldest": oldest, "newest": newest}
        resp = self.session.get(url, params=params)
        data = self._handle_response(resp)
        if isinstance(data, list):
            return [WellnessDay.from_dict(item) for item in data]
        return []

    def get_activities(self, oldest: str, newest: str) -> list[Activity]:
        """Fetch completed activities (rides, gym workouts, runs, etc.).

        Dates formatted as YYYY-MM-DD.
        """
        url = self._url("activities")
        params = {"oldest": oldest, "newest": newest}
        resp = self.session.get(url, params=params)
        data = self._handle_response(resp)
        if isinstance(data, list):
            return [Activity.from_dict(item) for item in data]
        return []

    def get_events(self, oldest: str, newest: str, resolve: bool = True) -> list[Event]:
        """Fetch planned calendar events/workouts.

        Dates formatted as YYYY-MM-DD.
        """
        url = self._url("events")
        params = {"oldest": oldest, "newest": newest, "resolve": str(resolve).lower()}
        resp = self.session.get(url, params=params)
        data = self._handle_response(resp)
        if isinstance(data, list):
            return [Event.from_dict(item) for item in data]
        return []

    def create_event(self, event: Event) -> Event:
        """Create a single planned workout or calendar event."""
        url = self._url("events")
        resp = self.session.post(url, json=event.to_payload())
        data = self._handle_response(resp)
        return Event.from_dict(data)

    def bulk_create_events(self, events: list[Event], upsert: bool = True) -> list[Event]:
        """Bulk create planned events."""
        url = self._url("events/bulk")
        params = {"upsert": str(upsert).lower()}
        payload = [e.to_payload() for e in events]
        resp = self.session.post(url, params=params, json=payload)
        data = self._handle_response(resp)
        if isinstance(data, list):
            return [Event.from_dict(item) for item in data]
        return []

    def delete_event(self, event_id: str | int) -> bool:
        """Delete a planned event by its ID."""
        url = self._url(f"events/{event_id}")
        resp = self.session.delete(url)
        self._handle_response(resp)
        return True

    def create_manual_activity(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a completed manual activity (e.g. gym workout)."""
        url = self._url("activities/manual")
        resp = self.session.post(url, json=payload)
        return self._handle_response(resp)

    def delete_activity(self, activity_id: str | int) -> bool:
        """Delete an activity by ID."""
        url = f"{self.base_url}/activity/{activity_id}"
        resp = self.session.delete(url)
        self._handle_response(resp)
        return True
