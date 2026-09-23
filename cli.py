#!/usr/bin/env python3
"""Unified CLI for Intervals.icu, Cycling & Gym Training Coordination."""

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from intervals.analyzer import TrainingAnalyzer
from intervals.client import IntervalsAPIError, IntervalsClient
from intervals.hevy import HevyParser
from intervals.models import Event
from intervals.templates import CYCLING_WORKOUTS, GYM_WORKOUTS

console = Console()


def get_client() -> IntervalsClient:
    try:
        return IntervalsClient()
    except ValueError as e:
        console.print(f"[bold red]Configuration Error:[/bold red] {e}")
        console.print("[yellow]Hint:[/yellow] Copy [cyan].env.example[/cyan] to [cyan].env[/cyan] and add your INTERVALS_API_KEY.")
        sys.exit(1)


def cmd_test_connection(args: argparse.Namespace) -> None:
    """Test connection and display athlete info."""
    client = get_client()
    try:
        console.print("[dim]Testing connection to Intervals.icu...[/dim]")
        athlete = client.get_athlete()
        console.print(f"[bold green]✔ Successfully connected![/bold green]")
        
        table = Table(title="Athlete Profile", box=box.ROUNDED)
        table.add_column("Property", style="bold cyan")
        table.add_column("Value", style="bold white")
        
        table.add_row("Athlete ID", str(athlete.id))
        table.add_row("Name", athlete.name or "N/A")
        
        ftp_val = f"{athlete.ftp} W" if athlete.ftp else "Not set"
        if athlete.ftp and athlete.weight:
            w_per_kg = athlete.ftp / athlete.weight
            ftp_val += f" ({w_per_kg:.2f} W/kg)"
        table.add_row("FTP (Cycling)", ftp_val)
        if athlete.eftp:
            table.add_row("eFTP (Est.)", f"{athlete.eftp} W")
        table.add_row("Weight", f"{athlete.weight} kg" if athlete.weight else "Not set")
        table.add_row("Threshold HR (LTHR)", f"{athlete.lthr} bpm" if athlete.lthr else "Not set")
        table.add_row("Max HR", f"{athlete.max_hr} bpm" if athlete.max_hr else "Not set")
        table.add_row("Resting HR", f"{athlete.resting_hr} bpm" if athlete.resting_hr else "Not set")
        
        console.print(table)
    except IntervalsAPIError as e:
        console.print(f"[bold red]API Error:[/bold red] {e}")
        sys.exit(1)


def cmd_status(args: argparse.Namespace) -> None:
    """Display training load dashboard, fatigue, form, and recovery advice."""
    client = get_client()
    today = date.today()
    past_days = args.days or 14
    oldest = (today - timedelta(days=past_days)).isoformat()
    future = (today + timedelta(days=7)).isoformat()
    today_str = today.isoformat()

    with console.status("[bold cyan]Fetching wellness and activity data from Intervals.icu..."):
        athlete = client.get_athlete()
        wellness = client.get_wellness(oldest=oldest, newest=today_str)
        activities = client.get_activities(oldest=(today - timedelta(days=7)).isoformat(), newest=today_str)
        upcoming_events = client.get_events(oldest=today_str, newest=future)

    summary = TrainingAnalyzer.summarize_status(athlete, wellness, activities, upcoming_events)

    # Header / Form Banner
    form_status = summary["form_status"]
    form_color = summary["form_color"]
    form_advice = summary["form_advice"]
    tsb = summary["form_tsb"]
    ctl = summary["fitness_ctl"]
    atl = summary["fatigue_atl"]

    console.print()
    banner_content = (
        f"Athlete: [bold]{summary['athlete_name']}[/bold] (FTP: {summary['ftp'] or 'N/A'}W)\n\n"
        f"Fitness (CTL): [bold cyan]{ctl}[/bold cyan]   |   "
        f"Fatigue (ATL): [bold magenta]{atl}[/bold magenta]   |   "
        f"Form (TSB): [{form_color}]{tsb:+.1f} ({form_status})[/{form_color}]\n\n"
        f"[italic]{form_advice}[/italic]"
    )
    console.print(Panel(banner_content, title="[bold]Intervals.icu Training Status[/bold]", border_style=form_color))

    # Last 7 Days Volume Table
    table_vol = Table(title="Last 7 Days Training Load Breakdown", box=box.SIMPLE_HEAVY)
    table_vol.add_column("Discipline", style="bold")
    table_vol.add_column("Count", justify="center")
    table_vol.add_column("Volume", justify="center")
    table_vol.add_column("Training Load (TSS)", justify="right", style="bold yellow")

    table_vol.add_row(
        "🚴 Cycling (Wahoo)",
        str(summary["bike_rides_7d"]),
        f"{summary['bike_time_7d_hours']}h ({summary['bike_distance_7d_km']} km)",
        f"{summary['bike_load_7d']:.0f}",
    )
    table_vol.add_row(
        "🏋 Gym (Hevy)",
        str(summary["gym_sessions_7d"]),
        f"{summary['gym_sessions_7d']} sessions",
        f"{summary['gym_load_7d']:.0f}",
    )
    table_vol.add_row(
        "[bold]Total[/bold]",
        str(len(activities)),
        "-",
        f"[bold]{summary['total_load_7d']:.0f}[/bold]",
    )
    console.print(table_vol)

    # Coaching Recommendations
    rec_table = Table(title="Coaching & Regeneration Advice", box=box.ROUNDED)
    rec_table.add_column("Guidance", style="green")
    for r in summary["recommendations"]:
        rec_table.add_row(f"• {r}")
    console.print(rec_table)

    # Upcoming Events Preview
    if upcoming_events:
        evt_table = Table(title="Upcoming Workouts (Next 7 Days)", box=box.ROUNDED)
        evt_table.add_column("Date / Time", style="cyan")
        evt_table.add_column("Type", style="magenta")
        evt_table.add_column("Workout Name", style="bold white")
        for evt in upcoming_events[:5]:
            evt_table.add_row(evt.start_date_local.replace("T", " "), evt.type, evt.name)
        console.print(evt_table)
    else:
        console.print("[dim]No upcoming workouts planned in the next 7 days.[/dim]")
    console.print()


def cmd_activities(args: argparse.Namespace) -> None:
    """List recent completed activities."""
    client = get_client()
    days = args.days or 10
    today = date.today()
    oldest = (today - timedelta(days=days)).isoformat()
    newest = today.isoformat()

    activities = client.get_activities(oldest=oldest, newest=newest)

    table = Table(title=f"Activities (Last {days} Days)", box=box.ROUNDED)
    table.add_column("Date", style="cyan", no_wrap=True)
    table.add_column("Type", style="magenta")
    table.add_column("Name", style="bold white")
    table.add_column("Duration", justify="center", no_wrap=True)
    table.add_column("Dist (km)", justify="right", no_wrap=True)
    table.add_column("Avg Power", justify="right", no_wrap=True)
    table.add_column("Avg HR", justify="right", no_wrap=True)
    table.add_column("Load", justify="right", style="bold yellow", no_wrap=True)

    for act in sorted(activities, key=lambda a: a.start_date_local, reverse=True):
        table.add_row(
            act.start_date_local.split("T")[0],
            act.type,
            act.name,
            act.duration_formatted,
            str(act.distance_km) if act.distance_km > 0 else "-",
            f"{int(act.avg_power)}W" if act.avg_power else "-",
            f"{int(act.avg_hr)}bpm" if act.avg_hr else "-",
            f"{act.training_load:.0f}",
        )
    console.print(table)


def cmd_events(args: argparse.Namespace) -> None:
    """List planned calendar events/workouts."""
    client = get_client()
    days = args.days or 14
    today = date.today()
    oldest = today.isoformat()
    newest = (today + timedelta(days=days)).isoformat()

    events = client.get_events(oldest=oldest, newest=newest)

    table = Table(title=f"Planned Workouts (Next {days} Days)", box=box.ROUNDED)
    table.add_column("ID", style="dim")
    table.add_column("Date & Time", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Name", style="bold white")
    table.add_column("Description Preview", style="dim")

    for evt in sorted(events, key=lambda e: e.start_date_local):
        desc_preview = evt.description.split("\n")[0] if evt.description else ""
        if len(desc_preview) > 50:
            desc_preview = desc_preview[:47] + "..."
        table.add_row(
            str(evt.id or ""),
            evt.start_date_local.replace("T", " "),
            evt.type,
            evt.name,
            desc_preview,
        )
    console.print(table)


def cmd_list_templates(args: argparse.Namespace) -> None:
    """List available pre-built cycling and gym templates."""
    table = Table(title="Available Workout Templates", box=box.ROUNDED)
    table.add_column("Key", style="bold cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Name", style="bold white")

    for k, v in CYCLING_WORKOUTS.items():
        table.add_row(k, "🚴 Cycling", v["name"])
    for k, v in GYM_WORKOUTS.items():
        table.add_row(k, "🏋 Gym", v["name"])

    console.print(table)


def cmd_push_template(args: argparse.Namespace) -> None:
    """Push a template workout to the Intervals.icu calendar."""
    client = get_client()
    key = args.template
    target_dt = args.datetime  # Expected format YYYY-MM-DDTHH:MM:SS or YYYY-MM-DD

    if "T" not in target_dt:
        target_dt = f"{target_dt}T09:00:00"

    template = CYCLING_WORKOUTS.get(key) or GYM_WORKOUTS.get(key)
    if not template:
        console.print(f"[bold red]Template '{key}' not found![/bold red]")
        console.print("Run [cyan]python cli.py templates[/cyan] to see available templates.")
        sys.exit(1)

    event = Event(
        start_date_local=target_dt,
        type=template["type"],
        name=template["name"],
        description=template["description"],
        category=template["category"],
    )

    created = client.create_event(event)
    console.print(f"[bold green]✔ Workout created successfully![/bold green]")
    console.print(f"ID: [cyan]{created.id}[/cyan] | {created.start_date_local} | {created.type}: {created.name}")
    if created.type == "Ride":
        console.print("[dim]This workout will automatically sync to your Wahoo ELEMNT BOLT upon its next sync![/dim]")


def cmd_push_workout(args: argparse.Namespace) -> None:
    """Push a custom workout defined via CLI arguments or JSON."""
    client = get_client()
    target_dt = args.datetime
    if "T" not in target_dt:
        target_dt = f"{target_dt}T09:00:00"

    event = Event(
        start_date_local=target_dt,
        type=args.type,
        name=args.name,
        description=args.description,
        category="WORKOUT",
    )
    created = client.create_event(event)
    console.print(f"[bold green]✔ Workout created![/bold green] ID: {created.id}")


def cmd_push_plan(args: argparse.Namespace) -> None:
    """Push a full training plan from a JSON file."""
    client = get_client()
    with open(args.file, "r") as f:
        plan_data = json.load(f)

    if not isinstance(plan_data, list):
        console.print("[bold red]Invalid plan format: Expected a JSON array of workout objects.[/bold red]")
        sys.exit(1)

    events: list[Event] = []
    for item in plan_data:
        dt = item.get("date") or item.get("start_date_local")
        if "T" not in dt:
            dt = f"{dt}T09:00:00"
        events.append(
            Event(
                start_date_local=dt,
                type=item.get("type", "Ride"),
                name=item.get("name", "Workout"),
                description=item.get("description", ""),
                category=item.get("category", "WORKOUT"),
                load=item.get("load"),
            )
        )

    console.print(f"[cyan]Uploading {len(events)} planned workouts to Intervals.icu...[/cyan]")
    for e in events:
        res = client.create_event(e)
        icon = "🚴" if res.type == "Ride" else "🏋"
        console.print(f"  [green]✔[/green] {icon} {res.start_date_local.replace('T', ' ')} - [bold]{res.name}[/bold] (ID: {res.id})")
    console.print("[bold green]All workouts uploaded successfully![/bold green]")
    console.print("[dim]Cycling workouts will sync to your Wahoo BOLT on next device sync.[/dim]")


def cmd_delete_event(args: argparse.Namespace) -> None:
    """Delete a planned workout by its ID."""
    client = get_client()
    client.delete_event(args.id)
    console.print(f"[bold green]✔ Event {args.id} deleted successfully.[/bold green]")


def cmd_export_context(args: argparse.Namespace) -> None:
    """Export compact JSON context for AI analysis & plan generation."""
    client = get_client()
    today = date.today()
    oldest_wellness = (today - timedelta(days=14)).isoformat()
    today_str = today.isoformat()
    future_str = (today + timedelta(days=7)).isoformat()

    athlete = client.get_athlete()
    wellness = client.get_wellness(oldest=oldest_wellness, newest=today_str)
    activities = client.get_activities(oldest=(today - timedelta(days=7)).isoformat(), newest=today_str)
    upcoming_events = client.get_events(oldest=today_str, newest=future_str)

    summary = TrainingAnalyzer.summarize_status(athlete, wellness, activities, upcoming_events)
    recent_act_list = [
        {
            "date": a.start_date_local,
            "type": a.type,
            "name": a.name,
            "duration_min": round(a.moving_time_secs / 60),
            "distance_km": a.distance_km,
            "tss": round(a.training_load, 1),
            "avg_power": a.avg_power,
            "avg_hr": a.avg_hr,
        }
        for a in activities
    ]
    upcoming_evt_list = [
        {
            "id": e.id,
            "date": e.start_date_local,
            "type": e.type,
            "name": e.name,
        }
        for e in upcoming_events
    ]

    hevy_list = []
    hevy_path = Path("workout_data.csv")
    if hevy_path.exists():
        try:
            hw = HevyParser.parse_file(hevy_path)
            hevy_list = [
                {
                    "date": w.start_time.isoformat(),
                    "title": w.title,
                    "duration_min": w.duration_minutes,
                    "volume_kg": w.total_volume_kg,
                    "avg_rpe": w.average_rpe,
                    "muscle_focus": w.muscle_focus,
                    "has_leg_fatigue": w.has_leg_fatigue,
                    "exercises": [f"{e.title} ({e.sets_summary})" for e in w.exercises],
                }
                for w in hw[:5]
            ]
        except Exception:
            pass

    export_data = {
        "athlete": {
            "name": athlete.name,
            "ftp": athlete.ftp,
            "weight": athlete.weight,
        },
        "status": summary,
        "recent_activities_7d": recent_act_list,
        "upcoming_events_7d": upcoming_evt_list,
        "recent_gym_workouts": hevy_list,
    }

    print(json.dumps(export_data, indent=2))


def cmd_import_hevy(args: argparse.Namespace) -> None:
    """Import and inspect Hevy workouts from CSV, optionally uploading natively to Intervals.icu."""
    filepath = args.file or "workout_data.csv"
    try:
        workouts = HevyParser.parse_file(filepath)
    except FileNotFoundError as e:
        console.print(f"[bold red]File Error:[/bold red] {e}")
        sys.exit(1)

    table = Table(title=f"Hevy Strength Sessions ({len(workouts)} found in {filepath})", box=box.ROUNDED)
    table.add_column("Date / Time", style="cyan", no_wrap=True)
    table.add_column("Workout", style="bold white")
    table.add_column("Duration", justify="center", no_wrap=True)
    table.add_column("Volume", justify="right", style="bold green", no_wrap=True)
    table.add_column("Avg RPE", justify="center", style="yellow")
    table.add_column("Load (TSS)", justify="right", style="bold yellow")
    table.add_column("Muscle Focus", style="dim")
    table.add_column("Status", justify="center")

    client = get_client() if args.upload else None
    existing_activities = []
    if client:
        oldest = (date.today() - timedelta(days=45)).isoformat()
        newest = date.today().isoformat()
        try:
            existing_activities = client.get_activities(oldest=oldest, newest=newest)
        except Exception:
            existing_activities = []

    limit = args.limit if args.limit is not None else 10
    selected_workouts = workouts[:limit] if limit > 0 else workouts
    uploaded_count = 0

    for w in selected_workouts:
        w_date_str = w.start_time.strftime("%Y-%m-%d")
        w_datetime_str = w.start_time.strftime("%Y-%m-%d %H:%M")
        short_tags = []
        if any("Quads" in f for f in w.muscle_focus):
            short_tags.append("Quads")
        if any("Posterior" in f for f in w.muscle_focus):
            short_tags.append("Hinge/Glutes")
        if any("Pull" in f for f in w.muscle_focus):
            short_tags.append("Pull")
        if any("Push" in f for f in w.muscle_focus):
            short_tags.append("Push")
        if any("Core" in f for f in w.muscle_focus):
            short_tags.append("Core")
        focus_str = ", ".join(short_tags) if short_tags else "General"
        rpe_str = f"{w.average_rpe:.1f}" if w.average_rpe else "-"

        is_already_present = any(
            act.start_date_local.startswith(w_date_str) and (
                w.title.lower() in act.name.lower()
                or "hevy" in act.name.lower()
                or act.start_date_local == w.start_time.isoformat()
            )
            for act in existing_activities
        )

        status_str = "[dim]Local CSV[/dim]"
        if args.upload and client:
            if is_already_present:
                status_str = "[yellow]Already on Calendar[/yellow]"
            else:
                try:
                    payload = {
                        "start_date_local": w.start_time.isoformat(),
                        "type": "WeightTraining",
                        "name": f"{w.title} (Hevy)",
                        "moving_time": w.duration_seconds,
                        "icu_training_load": w.training_load,
                        "kg_lifted": w.total_volume_kg,
                        "icu_rpe": int(round(w.average_rpe)) if w.average_rpe else None,
                        "description": w.formatted_description,
                    }
                    client.create_manual_activity(payload)
                    status_str = "[bold green]✔ Uploaded[/bold green]"
                    uploaded_count += 1
                except Exception as e:
                    status_str = f"[bold red]Failed ({e})[/bold red]"

        table.add_row(
            w_datetime_str,
            w.title,
            f"{w.duration_minutes}m",
            f"{w.total_volume_kg:,.0f} kg",
            rpe_str,
            f"{w.training_load:.0f}",
            focus_str,
            status_str,
        )

    console.print(table)

    if args.detail:
        console.print("\n[bold]Detailed Exercise Breakdowns:[/bold]")
        for w in selected_workouts:
            console.print(Panel(w.formatted_description, title=f"[bold cyan]{w.title} - {w.start_time.strftime('%Y-%m-%d %H:%M')}[/bold cyan]", box=box.ROUNDED))

    if args.upload:
        console.print(f"\n[bold green]✔ Sync complete:[/bold green] {uploaded_count} new gym session(s) created natively on Intervals.icu.")
    else:
        console.print("\n[dim]Tip: Run with [bold cyan]--upload[/bold cyan] to push new sessions natively into your Intervals.icu calendar with sets & volume.[/dim]")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Intervals.icu CLI for Cycling & Gym Training Management",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # test-connection
    subparsers.add_parser("test-connection", help="Test connection to Intervals.icu API")

    # status
    p_status = subparsers.add_parser("status", help="Show current fitness, fatigue, form, and load")
    p_status.add_argument("--days", type=int, default=14, help="Days of wellness history to fetch")

    # activities
    p_act = subparsers.add_parser("activities", help="List recent completed activities")
    p_act.add_argument("--days", type=int, default=7, help="Number of past days to query")

    # events
    p_evt = subparsers.add_parser("events", help="List upcoming planned workouts")
    p_evt.add_argument("--days", type=int, default=14, help="Number of future days to query")

    # templates
    subparsers.add_parser("templates", help="List available structured workout templates")

    # push-template
    p_tmpl = subparsers.add_parser("push-template", help="Push a template workout to calendar")
    p_tmpl.add_argument("template", help="Template key (e.g., vo2max_intervals, gym_lower_power)")
    p_tmpl.add_argument("datetime", help="Date & time (e.g., 2026-09-24T09:00:00 or 2026-09-24)")

    # push-workout
    p_w = subparsers.add_parser("push-workout", help="Push a custom structured workout")
    p_w.add_argument("--datetime", required=True, help="ISO Date string (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)")
    p_w.add_argument("--type", default="Ride", choices=["Ride", "WeightTraining", "Run", "Walk"], help="Sport type")
    p_w.add_argument("--name", required=True, help="Workout title")
    p_w.add_argument("--description", required=True, help="Intervals.icu structured workout text")

    # push-plan
    p_plan = subparsers.add_parser("push-plan", help="Push a complete training plan from a JSON file")
    p_plan.add_argument("file", help="Path to plan JSON file")

    # delete-event
    p_del = subparsers.add_parser("delete-event", help="Delete a planned workout by event ID")
    p_del.add_argument("id", help="Event ID to delete")

    # export-context
    subparsers.add_parser("export-context", help="Export training state as JSON for AI analysis")

    # import-hevy
    p_hevy = subparsers.add_parser("import-hevy", help="Import & inspect Hevy workouts from CSV")
    p_hevy.add_argument("file", nargs="?", default="workout_data.csv", help="Path to Hevy CSV file (default: workout_data.csv)")
    p_hevy.add_argument("--upload", action="store_true", help="Upload workouts natively to Intervals.icu")
    p_hevy.add_argument("--limit", type=int, default=10, help="Number of workouts to show (default: 10)")
    p_hevy.add_argument("--detail", action="store_true", help="Show full exercise breakdown for workouts")

    args = parser.parse_args()

    commands = {
        "test-connection": cmd_test_connection,
        "status": cmd_status,
        "activities": cmd_activities,
        "events": cmd_events,
        "templates": cmd_list_templates,
        "push-template": cmd_push_template,
        "push-workout": cmd_push_workout,
        "push-plan": cmd_push_plan,
        "delete-event": cmd_delete_event,
        "export-context": cmd_export_context,
        "import-hevy": cmd_import_hevy,
    }

    fn = commands.get(args.command)
    if fn:
        fn(args)


if __name__ == "__main__":
    main()
