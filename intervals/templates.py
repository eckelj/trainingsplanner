"""Structured workout templates for cycling (Intervals.icu / Wahoo) and gym (Hevy)."""

from typing import Dict, Any


CYCLING_WORKOUTS: Dict[str, Dict[str, Any]] = {
    "z2_endurance": {
        "name": "Zone 2 Aerobic Base (75m)",
        "type": "Ride",
        "category": "WORKOUT",
        "description": """Warmup
- 10m 50-60% 85-90rpm

Main Set
- 60m 65-72% 88-94rpm Keep cadence steady and breathing conversational

Cooldown
- 5m 50% 85rpm
""",
    },
    "vo2max_intervals": {
        "name": "VO2 Max 5x3min Intervals",
        "type": "Ride",
        "category": "WORKOUT",
        "description": """Warmup
- 12m 55-65% 90rpm
- 3x 30s 115% / 30s 55%
- 3m 55%

Main Set 5x
- 3m 112-118% 100rpm Max sustainable aerobic power
- 3m 50% 85rpm Easy spin recovery

Cooldown
- 10m 50% 85rpm
""",
    },
    "sweet_spot_3x10": {
        "name": "Sweet Spot 3x10min (88-92%)",
        "type": "Ride",
        "category": "WORKOUT",
        "description": """Warmup
- 15m 55-65%
- 3x 1m 95% / 1m 55%
- 2m 55%

Main Set 3x
- 10m 88-92% 90rpm
- 4m 55% 85rpm

Cooldown
- 10m 50%
""",
    },
    "over_unders": {
        "name": "Threshold Over-Unders 3x9min",
        "type": "Ride",
        "category": "WORKOUT",
        "description": """Warmup
- 15m 55-70%
- 2m 90%
- 3m 55%

Main Set 3x
- 3x
  - 2m 95% 90rpm Under
  - 1m 105% 95rpm Over
- 5m 50% Recovery

Cooldown
- 10m 50%
""",
    },
    "recovery_spin": {
        "name": "Active Recovery Spin (45m)",
        "type": "Ride",
        "category": "WORKOUT",
        "description": """Recovery Spin
- 45m 45-55% 90-95rpm Very light pressure on pedals. Stay in Zone 1.
""",
    },
}

GYM_WORKOUTS: Dict[str, Dict[str, Any]] = {
    "gym_lower_power": {
        "name": "Gym - Lower Body Power & Posterior Chain",
        "type": "WeightTraining",
        "category": "WORKOUT",
        "description": """Focus: Strength & pedal stroke power without excessive hypertrophy fatigue.

Warmup & Mobility:
- 5m foam roll (quads, glutes, lats) + hip 90/90 mobility
- 2x 10 bodyweight squats + glute bridges

Main Lifts:
- Trap Bar Deadlift / Back Squat: 4 sets x 5 reps @ RPE 7.5 (rest 2.5-3m)
- Romanian Deadlift (RDL): 3 sets x 8 reps @ RPE 7 (posterior chain focus)
- Bulgarian Split Squat: 3 sets x 8 reps each side
- Standing Calf Raises: 3 sets x 12 reps (controlled eccentric)

Core & Anti-Extension:
- Ab Wheel Rollout / Dead Bug: 3 sets x 10 reps
- Side Planks: 3 sets x 45s each side
""",
    },
    "gym_upper_core": {
        "name": "Gym - Upper Body Posture & Core Stability",
        "type": "WeightTraining",
        "category": "WORKOUT",
        "description": """Focus: Thoracic spine extension, shoulder stability, anti-fatigue on the bike.

Warmup:
- Band pull-aparts: 2x15
- Arm circles & cat-cow: 2m

Main Lifts:
- Standing Overhead Barbell/DB Press: 4 sets x 6-8 reps @ RPE 7.5
- Chest-Supported DB Row: 4 sets x 8-10 reps @ RPE 8
- Incline DB Bench Press: 3 sets x 8-10 reps
- Face Pulls (rear delt & rotator cuff): 3 sets x 15 reps

Core & Anti-Rotation:
- Pallof Press: 3 sets x 12 reps / side
- Hanging Knee Raises: 3 sets x 12 reps
- Plank: 3 sets x 60s
""",
    },
    "gym_full_body_express": {
        "name": "Gym - Full Body Express (40m)",
        "type": "WeightTraining",
        "category": "WORKOUT",
        "description": """Focus: Time-efficient maintenance during heavy cycling blocks.

Compound Circuit (3-4 rounds, 90s rest):
- Goblet Squat: 8 reps
- Dumbbell Single-Arm Row: 8 reps / side
- Push-ups or DB Bench: 10 reps
- Romanian Deadlift (DB): 10 reps
- Farmer's Walk: 40 meters
- RKC Plank: 30 seconds max tension
""",
    },
}
