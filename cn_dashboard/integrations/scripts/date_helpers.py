from datetime import date, datetime, timedelta, timezone
from ..config.student import UTC_OFFSET

MONDAY = 0
TIMEZONE = timezone(timedelta(hours=UTC_OFFSET))

"""
Helpers relating to generating date mappings.
"""

"""
Convert Canvas UTC due_at string to Singapore ISO format string.
"""
def date_to_sg_offset_iso(due_at: str) -> str:
    dt_utc = datetime.fromisoformat(due_at.replace("Z", "+00:00"))
    return dt_utc.astimezone(TIMEZONE).isoformat()

def firstWeekdayOfMonth(year: int, month: int, weekday: int) -> date:
    d = date(year, month, 1)
    delta = (weekday - d.weekday()) % 7
    return d + timedelta(days=delta)

def nthWeekdayOfMonth(year: int, month: int, weekday: int, n: int) -> date:
    return firstWeekdayOfMonth(year, month, weekday) + timedelta(weeks=n - 1)

"""
Semester ranges for semester 1 start from Week 0 Monday.
Semester ranges for semester 2 start from Week 1 Monday.
"""
def computeSemesterBoundsForAy(ay_start_year: int):
    # Semester 1
    s1_week0 = firstWeekdayOfMonth(ay_start_year, 8, MONDAY)
    s1_week1 = s1_week0 + timedelta(weeks=1)
    s1_start = s1_week0
    s1_end = s1_week1 + timedelta(weeks=17) - timedelta(days=1)

    # Winter term
    wt_start = s1_end + timedelta(days=1)
    s2_week1 = nthWeekdayOfMonth(ay_start_year + 1, 1, MONDAY, 2)
    wt_end = s2_week1 - timedelta(days=1)

    # Semester 2
    s2_start = s2_week1
    s2_end = s2_week1 + timedelta(weeks=17) - timedelta(days=1)

    # Special Term
    next_s1_week0 = firstWeekdayOfMonth(ay_start_year + 1, 8, MONDAY)
    st_start = s2_end + timedelta(days=1)
    st_end = next_s1_week0 - timedelta(days=1)

    return {
        "S1": (s1_start, s1_end),
        "Winter Term": (wt_start, wt_end),
        "S2": (s2_start, s2_end),
        "Special Term": (st_start, st_end),
    }

def computeSemesterBoundsForUniTerm(matric_year: int):
    return {
        "Y1S1": computeSemesterBoundsForAy(matric_year)["S1"],
        "Y1 Winter Term": computeSemesterBoundsForAy(matric_year)["Winter Term"],
        "Y1S2": computeSemesterBoundsForAy(matric_year)["S2"],
        "Y1 Special Term": computeSemesterBoundsForAy(matric_year)["Special Term"],
        "Y2S1": computeSemesterBoundsForAy(matric_year + 1)["S1"],
        "Y2 Winter Term": computeSemesterBoundsForAy(matric_year + 1)["Winter Term"],
        "Y2S2": computeSemesterBoundsForAy(matric_year + 1)["S2"],
        "Y2 Special Term": computeSemesterBoundsForAy(matric_year + 1)["Special Term"],
        "Y3S1": computeSemesterBoundsForAy(matric_year + 2)["S1"],
        "Y3 Winter Term": computeSemesterBoundsForAy(matric_year + 2)["Winter Term"],
        "Y3S2": computeSemesterBoundsForAy(matric_year + 2)["S2"],
        "Y3 Special Term": computeSemesterBoundsForAy(matric_year + 2)["Special Term"],
        "Y4S1": computeSemesterBoundsForAy(matric_year + 3)["S1"],
        "Y4 Winter Term": computeSemesterBoundsForAy(matric_year + 3)["Winter Term"],
        "Y4S2": computeSemesterBoundsForAy(matric_year + 3)["S2"],
        "Y4 Special Term": computeSemesterBoundsForAy(matric_year + 3)["Special Term"],
    }

def buildSemesterRanges(matric_year: int):
    semester_bounds = computeSemesterBoundsForUniTerm(matric_year)
    semester_ranges = []
    for semester_name, (start_date, end_date) in semester_bounds.items():
        semester_ranges.append((semester_name, start_date, end_date))
    return semester_ranges

def computeWeekRangesForSemester1(matric_year: int, current_level: int):
    ay_start_year = matric_year + current_level - 1
    week_ranges = [
        ("Week 0", firstWeekdayOfMonth(ay_start_year, 8, MONDAY), firstWeekdayOfMonth(ay_start_year, 8, MONDAY) + timedelta(days=6)),
    ]
    for i in range(1, 7):
        start_date = week_ranges[i - 1][2] + timedelta(days=1)
        end_date = start_date + timedelta(days=6)
        week_ranges.append((f"Week {i}", start_date, end_date))

    # Recess Week
    recess_start = week_ranges[6][2] + timedelta(days=1)
    recess_end = recess_start + timedelta(days=6)
    week_ranges.append(("Recess Week", recess_start, recess_end))

    for i in range(7, 14):
        start_date = week_ranges[i][2] + timedelta(days=1)
        end_date = start_date + timedelta(days=6)
        week_ranges.append((f"Week {i}", start_date, end_date))
    
    # Reading Week
    reading_start = week_ranges[14][2] + timedelta(days=1)
    reading_end = reading_start + timedelta(days=6)
    week_ranges.append(("Reading Week", reading_start, reading_end))

    # Exam Weeks
    exam1_start = week_ranges[15][2] + timedelta(days=1)
    exam1_end = exam1_start + timedelta(days=6)
    week_ranges.append(("Exam Week 1", exam1_start, exam1_end))
    exam2_start = exam1_end + timedelta(days=1)
    exam2_end = exam2_start + timedelta(days=6)
    week_ranges.append(("Exam Week 2", exam2_start, exam2_end))

    return week_ranges

def computeWeekRangesForSemester2(matric_year: int, current_level: int):
    ay_start_year = matric_year + current_level - 1
    week_ranges = []
    # Semester 2 starts from Week 1 Monday
    week1_start = nthWeekdayOfMonth(ay_start_year + 1, 1, MONDAY, 2)
    week_ranges.append(("Week 1", week1_start, week1_start + timedelta(days=6)))
    
    for i in range(2, 7):
        start_date = week_ranges[i - 2][2] + timedelta(days=1)
        end_date = start_date + timedelta(days=6)
        week_ranges.append((f"Week {i}", start_date, end_date))

    # Recess Week
    recess_start = week_ranges[5][2] + timedelta(days=1)
    recess_end = recess_start + timedelta(days=6)
    week_ranges.append(("Recess Week", recess_start, recess_end))

    for i in range(7, 14):
        start_date = week_ranges[i - 2][2] + timedelta(days=1)
        end_date = start_date + timedelta(days=6)
        week_ranges.append((f"Week {i}", start_date, end_date))
    
    # Reading Week
    reading_start = week_ranges[12][2] + timedelta(days=1)
    reading_end = reading_start + timedelta(days=6)
    week_ranges.append(("Reading Week", reading_start, reading_end))

    # Exam Weeks
    exam1_start = week_ranges[13][2] + timedelta(days=1)
    exam1_end = exam1_start + timedelta(days=6)
    week_ranges.append(("Exam Week 1", exam1_start, exam1_end))
    exam2_start = exam1_end + timedelta(days=1)
    exam2_end = exam2_start + timedelta(days=6)
    week_ranges.append(("Exam Week 2", exam2_start, exam2_end))

    return week_ranges

def buildWeekRanges(matric_year: int, current_level: int, current_sem: int):
    if current_sem == 1:
        return computeWeekRangesForSemester1(matric_year, current_level)
    else:
        return computeWeekRangesForSemester2(matric_year, current_level)

def buildWeekRangesForUniTerm(matric_year: int):
    week_ranges = {
        "Y1S1": computeWeekRangesForSemester1(matric_year, 1),
        "Y1S2": computeWeekRangesForSemester2(matric_year, 1),
        "Y2S1": computeWeekRangesForSemester1(matric_year, 2),
        "Y2S2": computeWeekRangesForSemester2(matric_year, 2),
        "Y3S1": computeWeekRangesForSemester1(matric_year, 3),
        "Y3S2": computeWeekRangesForSemester2(matric_year, 3),
        "Y4S1": computeWeekRangesForSemester1(matric_year, 4),
        "Y4S2": computeWeekRangesForSemester2(matric_year, 4),
    }
    return week_ranges