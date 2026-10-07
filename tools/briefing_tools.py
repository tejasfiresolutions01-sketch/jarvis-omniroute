from datetime import datetime, date
from core.schedule_manager import schedule_manager
from tools.system_controller import system_controller
from tools.weather_tools import get_weather

def generate_executive_briefing() -> str:
    """
    Protocol Sunrise: Executive Morning Briefing.
    Combines hardware vitals, atmospheric conditions, and the day's agenda.
    """
    now = datetime.now()
    hour = now.hour
    greeting = "Good morning" if hour < 12 else ("Good afternoon" if hour < 18 else "Good evening")
    time_str = now.strftime("%I:%M %p")
    date_str = now.strftime("%A, %B %d, %Y")

    lines = [
        f"{greeting}, sir. Protocol Sunrise initialized at {time_str} on {date_str}.",
        "",
        "-- SYSTEM TELEMETRY --"
    ]

    vitals = system_controller.get_vitals()
    lines.append(f"Hardware status is nominal: CPU is at {vitals['cpu_usage']}, RAM load is {vitals['ram_usage']}, and disk space remaining is {vitals['disk_free']}.")

    lines.append("")
    lines.append("-- METEOROLOGICAL TELEMETRY --")
    weather_summary = get_weather()
    lines.append(weather_summary)

    lines.append("")
    lines.append("-- AGENDA & ITINERARY --")
    today_str = date.today().strftime("%Y-%m-%d")
    events = schedule_manager.get_events_for_date(today_str)
    if not events:
        lines.append("Your agenda for today is entirely clear, sir. No conflicting appointments require your attention.")
    else:
        lines.append(f"You have {len(events)} engagement{'s' if len(events) > 1 else ''} on your schedule today:")
        for idx, e in enumerate(events, 1):
            t_str = schedule_manager._format_time_display(e["event_time"])
            lines.append(f"  {idx}. {e['title']} {t_str}")

    lines.append("")
    lines.append("All subroutines stand ready for your command, sir.")
    return "\n".join(lines)
