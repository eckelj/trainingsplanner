# Cycling & Strength Training Integration (Wahoo + Hevy + Intervals.icu)

A local Python toolkit and AI coaching workflow that bridges **Intervals.icu**, **Wahoo ELEMNT BOLT**, and **Hevy** to manage fitness, fatigue, and recovery across cycling and gym sessions.

---

## 🏗️ Architecture

```text
       Wahoo ELEMNT BOLT                Hevy Strength App
      (Rides & Workouts)                (Gym / Weightlifting)
              ▲                                   │
              │ (2-way sync)                      │ (Strava / Health sync)
              ▼                                   ▼
        ┌──────────────────────────────────────────────┐
        │                Intervals.icu                 │
        │  • Fitness (CTL) / Fatigue (ATL) / Form(TSB) │
        │  • Calendar & Structured Workouts            │
        │  • REST API                                  │
        └──────────────────────┬───────────────────────┘
                               ▲
                               │ REST API
                               ▼
        ┌──────────────────────────────────────────────┐
        │          Local Python Toolkit & AI           │
        │  • cli.py (Status, Workouts, Plans)          │
        │  • AI Pair Coach (Antigravity)               │
        └──────────────────────────────────────────────┘
```

1. **Wahoo BOLT** records outdoor/indoor rides and uploads them to Intervals.icu. Planned structured workouts on Intervals.icu automatically sync down to the BOLT.
2. **Hevy** logs gym workouts, which sync to Intervals.icu (via Strava, Apple Health, or Google Fit) to account for muscular stress and overall training load.
3. **Intervals.icu** acts as the single source of truth for your fitness/fatigue model (CTL, ATL, TSB).
4. **This tool + AI** evaluates fatigue, checks for cycling-gym interference (e.g., heavy leg day vs. interval rides), and writes structured workouts directly into your calendar.

---

## ⚡ Quickstart

### 1. Setup API Key

1. Log into [Intervals.icu](https://intervals.icu).
2. Go to **Settings** and scroll down to the **Developer Settings** section.
3. Copy your **API Key**.
4. In this repository, copy the example environment file:
   ```bash
   cp .env.example .env
   ```
5. Edit `.env` and set your key:
   ```env
   INTERVALS_API_KEY=your_copied_api_key
   INTERVALS_ATHLETE_ID=0
   ```

### 2. Verify Connection

Run:
```bash
.venv/bin/python cli.py test-connection
```
You should see your athlete name, FTP, and profile stats printed.

---

## 🛠️ CLI Commands

| Command | Description |
|---|---|
| `python cli.py status` | Shows training load dashboard: CTL, ATL, Form (TSB), last 7d load, recovery guidance. |
| `python cli.py activities [--days 7]` | Lists completed bike rides and gym workouts with TSS, power, HR, and duration. |
| `python cli.py events [--days 14]` | Shows upcoming planned workouts on your calendar. |
| `python cli.py templates` | Lists pre-built structured cycling and gym workout templates. |
| `python cli.py push-template <key> <datetime>` | Schedules a pre-built workout template on your calendar. |
| `python cli.py push-workout --datetime ... --name ... --description ...` | Pushes a custom structured workout. |
| `python cli.py push-plan <plan.json>` | Pushes a multi-day / weekly training schedule from a JSON file. |
| `python cli.py delete-event <id>` | Deletes a planned workout by event ID. |
| `python cli.py import-hevy [file.csv] [--upload]` | Imports workouts from Hevy CSV export (volume, sets, RPE) and optionally syncs them natively to Intervals.icu. |
| `python cli.py export-context` | Outputs JSON context (including recent gym volume and bike load) for AI analysis. |

---

## 🤖 Working with your AI Coach (Antigravity)

Because this tool is directly integrated into your project, you can simply chat with me to manage your training. Here are example workflows:

### 1. Weekly Planning
> *"Check my status on Intervals.icu and build my training plan for next week. I have time for 3 rides and 2 gym sessions."*
- **What happens:** I will inspect your CTL/ATL/TSB and recent volume, generate a balanced polarized or sweet-spot plan with leg and upper-body gym days scheduled to prevent interference, and upload it to your calendar.

### 2. Post-Activity Adaptation & Fatigue Management
> *"Yesterday's leg day was brutal and my quads are very sore. Check my calendar and adjust the next 3 days."*
- **What happens:** I will check upcoming workouts, swap high-intensity bike intervals for active recovery or endurance, and push the adjusted schedule.

### 3. Pre-Ride Workout Check
> *"What workout do I have scheduled on my Wahoo BOLT today? Give me the target wattage and pacing tips based on my current FTP."*
- **What happens:** I will query the day's event, compute your target wattages based on your FTP, and give you execution advice.

---

## 📁 Repository Structure

- [`cli.py`](cli.py): Main command-line interface.
- [`intervals/client.py`](intervals/client.py): REST API client for Intervals.icu.
- [`intervals/models.py`](intervals/models.py): Data classes for Athlete, Wellness, Activity, and Event.
- [`intervals/analyzer.py`](intervals/analyzer.py): Fatigue analysis, Form (TSB) classification, and cross-training advice.
- [`intervals/templates.py`](intervals/templates.py): Cycling workouts (using Intervals.icu syntax for Wahoo) and gym workout templates.
- [`examples/sample_week_plan.json`](examples/sample_week_plan.json): A sample 6-session concurrent training week.
