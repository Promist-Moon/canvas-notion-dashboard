from datetime import date
from ...config.student import MATRIC_YEAR
from ...scripts.date_helpers import buildSemesterRanges

SEMESTER_RANGES = buildSemesterRanges(MATRIC_YEAR)