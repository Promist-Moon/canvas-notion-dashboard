from datetime import date, datetime, timedelta, timezone
from typing import Union
from ..config.semester_map import SEMESTER_RANGES
from ..config.student import UTC_OFFSET
from ..config.week_map import WEEK_RANGES_BY_SEMESTER

TIMEZONE = timezone(timedelta(hours=UTC_OFFSET))

def compute_semester_from_due(
    due: Union[date, datetime, str],
    custom_range: tuple | None = None,
    custom_label: str | None = None,
    custom_phases: list | None = None,
) -> str:
    if due is None or due == "":
        return "N/A"

    # parse
    if isinstance(due, str):
        s = due.strip()

        if "T" not in s:
            d = date.fromisoformat(s)
        else:
            dt = datetime.fromisoformat(
                s.replace("Z", "+00:00")
            )
            d = dt.astimezone(TIMEZONE).date()
    elif isinstance(due, datetime):
        if due.tzinfo is None:
            due = due.replace(tzinfo=timezone.utc)
        d = due.astimezone(TIMEZONE).date()
    else:
        d = due

    if custom_phases:
        for phase in custom_phases:
            name = phase.get("name") if isinstance(phase, dict) else None
            start = phase.get("start") if isinstance(phase, dict) else None
            end = phase.get("end") if isinstance(phase, dict) else None
            try:
                if isinstance(start, str):
                    start = date.fromisoformat(start)
                if isinstance(end, str):
                    end = date.fromisoformat(end)
            except Exception:
                start = None
                end = None
            if name and start and end and start <= d <= end:
                return name

    if custom_range and len(custom_range) == 2:
        custom_start, custom_end = custom_range
        if custom_start and custom_end and custom_start <= d <= custom_end:
            return custom_label or "Custom Semester"

    for name, start, end in SEMESTER_RANGES:
        if start <= d <= end:
            return name
    return None

"""
Compute given week range name from due date.
Returns None if not found.
"""
def compute_week_from_due(
    due: Union[date, datetime, str],
    custom_range: tuple | None = None,
    custom_label: str | None = None,
    custom_phases: list | None = None,
) -> str:
    semester = compute_semester_from_due(
        due,
        custom_range=custom_range,
        custom_label=custom_label,
        custom_phases=custom_phases,
    )

    if semester is None or semester == "N/A":
        return "N/A"
    elif "Special Term" in semester:
        return "Special Term"
    elif "Winter Term" in semester:
        return "Winter Term"

    WEEK_RANGES = WEEK_RANGES_BY_SEMESTER.get(semester, [])

    # parse
    if isinstance(due, str):
        s = due.strip()

        if "T" not in s:
            d = date.fromisoformat(s)
        else:
            dt = datetime.fromisoformat(
                s.replace("Z", "+00:00")
            )
            d = dt.astimezone(TIMEZONE).date()
    elif isinstance(due, datetime):
        if due.tzinfo is None:
            due = due.replace(tzinfo=timezone.utc)
        d = due.astimezone(TIMEZONE).date()
    else:
        d = due

    for name, start, end in WEEK_RANGES:
        if start <= d <= end:
            return name
    return None
