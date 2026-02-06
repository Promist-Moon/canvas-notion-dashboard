WEEK_OPTIONS = [
    {"name": "Week 0", "color": "default"},
    {"name": "Week 1", "color": "pink"},
    {"name": "Week 2", "color": "green"},
    {"name": "Week 3", "color": "orange"},
    {"name": "Week 4", "color": "purple"},
    {"name": "Week 5", "color": "yellow"},
    {"name": "Week 6", "color": "blue"},
    {"name": "Recess Week", "color": "brown"},
    {"name": "Week 7", "color": "red"},
    {"name": "Week 8", "color": "orange"},
    {"name": "Week 9", "color": "pink"},
    {"name": "Week 10", "color": "blue"},
    {"name": "Week 11", "color": "yellow"},
    {"name": "Week 12", "color": "purple"},
    {"name": "Week 13", "color": "green"},
    {"name": "Reading Week", "color": "red"},
    {"name": "Exam Week 1", "color": "brown"},
    {"name": "Exam Week 2", "color": "blue"},
    {"name": "Special Term", "color": "gray"},
    {"name": "Winter Term", "color": "blue"},
    {"name": "N/A", "color": "default"},
]

SEMESTER_OPTIONS = [
    {"name": "Y1S1", "color": "yellow"},
    {"name": "Y1 Winter Term", "color": "blue"},
    {"name": "Y1S2", "color": "pink"},
    {"name": "Y1 Special Term", "color": "brown"},
    {"name": "Y2S1", "color": "blue"},
    {"name": "Y2 Winter Term", "color": "blue"},
    {"name": "Y2S2", "color": "green"},
    {"name": "Y2 Special Term", "color": "orange"},
    {"name": "Y3S1", "color": "pink"},
    {"name": "Y3 Winter Term", "color": "blue"},
    {"name": "Y3S2", "color": "yellow"},
    {"name": "Y3 Special Term", "color": "brown"},
    {"name": "Y4S1", "color": "purple"},
    {"name": "Y4 Winter Term", "color": "blue"},
    {"name": "Y4S2", "color": "red"},
    {"name": "Y4 Special Term", "color": "orange"},
    {"name": "N/A", "color": "default"},
]

NOTION_DB_PROPERTIES = {
    "State": {
        "formula": {
            "expression": '(dateBetween(prop("Due Date"), now(), "days") == 0) ? "🟧" : ((dateBetween(prop("Due Date"), now(), "days") < 0) ? "🟥" : "🟩")'
        }
    },
    "Assignment": {"title": {}},
    "Class": {
        "type": "select",
        "select": {"options": []},
    },
    "Due Date": {"date": {}},
    "Status": {
        "type": "select",
        "select": {
            "options": [
                {"name": "Not started", "color": "red"},
                {"name": "In progress", "color": "yellow"},
                {"name": "Done", "color": "green"},
            ]
        },
    },
    "Week": {
        "name": "Week",
        "type": "select",
        "select": {
            "options": WEEK_OPTIONS
        }
    },
    "Semester": {
        "type": "select",
        "select": {
            "options": SEMESTER_OPTIONS
        }
    },
    "URL": {"url": {}},
    "Notes": {"rich_text": {}},
}
