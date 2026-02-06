from datetime import date, datetime, timedelta, timezone
from typing import Union
from ..config.semester_map import SEMESTER_RANGES
from ..config.student import UTC_OFFSET
from ..config.week_map import WEEK_RANGES_BY_SEMESTER

TIMEZONE = timezone(timedelta(hours=UTC_OFFSET))

def compute_semester_from_due(due: Union[date, datetime, str]) -> str:
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

    for name, start, end in SEMESTER_RANGES:
        if start <= d <= end:
            return name
    return None

"""
Compute given week range name from due date.
Returns None if not found.
"""
def compute_week_from_due(due: Union[date, datetime, str]) -> str:
    semester = compute_semester_from_due(due)

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