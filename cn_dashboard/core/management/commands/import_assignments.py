from django.core.management.base import BaseCommand
from integrations.canvas import CanvasApi
from core.models import Assignment
from dateutil.parser import isoparse
from django.utils import timezone


class Command(BaseCommand):
    help = "Import assignments from Canvas into local Assignment model"

    def add_arguments(self, parser):
        parser.add_argument("--canvas-key", dest="canvas_key", required=True)
        parser.add_argument("--school-ab", dest="school_ab", required=True)
        parser.add_argument("--timeframe", dest="timeframe", required=False, default=None)

    def handle(self, *args, **options):
        canvas_key = options.get("canvas_key")
        school_ab = options.get("school_ab")
        timeframe = options.get("timeframe")

        api = CanvasApi(canvas_key, schoolAb=school_ab)
        courses = api.get_all_courses()
        api.set_courses_and_id()

        created = 0
        updated = 0

        for course in courses:
            course_name = course.name
            assignments = api.get_assignment_objects(course_name, timeframe)

            for a in assignments:
                url = a.get("url")
                if not url:
                    continue

                due_at = a.get("due_at")
                due_dt = None
                if due_at:
                    try:
                        due_dt = isoparse(due_at)
                    except Exception:
                        due_dt = None

                defaults = {
                    "external_id": str(a.get("id")) if a.get("id") is not None else None,
                    "title": a.get("name") or "",
                    "class_name": course_name,
                    "due_date": due_dt,
                    "has_submitted": bool(a.get("has_submitted_submissions", False)),
                    "raw_json": a,
                }

                obj, created_flag = Assignment.objects.update_or_create(
                    url=url, defaults=defaults
                )

                if created_flag:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(self.style.SUCCESS(f"Import complete: {created} created, {updated} updated"))
