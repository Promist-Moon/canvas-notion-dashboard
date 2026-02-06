from ...config.student import MATRIC_YEAR
from ...scripts.date_helpers import buildWeekRangesForUniTerm

WEEK_RANGES_BY_SEMESTER = buildWeekRangesForUniTerm(matric_year=MATRIC_YEAR)