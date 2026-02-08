import json, requests
from .canvas import CanvasApi
from .notion import NotionApi
from .scripts.date_helpers import date_to_sg_offset_iso

class User:
    def __init__(
        self,
        canvasKey,
        notionToken,
        notionPageId,
        schoolAb,
        database_id=None,
        db_properties=None,
        semester_start_date=None,
        semester_end_date=None,
        semester_label=None,
        semester_phases=None,
    ):
        self.notionToken = notionToken
        self.database_id = database_id
        self.db_properties = db_properties or []
        self.semester_start_date = semester_start_date
        self.semester_end_date = semester_end_date
        self.semester_label = semester_label
        self.semester_phases = semester_phases or []
        self.canvasProfile = CanvasApi(canvasKey, schoolAb)
        self.page_ids = {"Default": notionPageId}
        self.generated_db_id = None
        self.schoolAb = schoolAb
        self.notionProfile = NotionApi(
            notionToken,
            database_id=database_id,
            schoolAb=schoolAb,
            semester_start_date=semester_start_date,
            semester_end_date=semester_end_date,
            semester_label=semester_label,
            semester_phases=semester_phases,
        )

    # Shorthand fucntion for getting list of courses that started within the past 6 months from Canvas
    def getCoursesLastSixMonths(self):
        return self.canvasProfile.get_courses_within_six_months()

    # Shorthand fucntion for getting list of all courses from Canvas
    def getAllCourses(self):
        return self.canvasProfile.get_all_courses()

    # Enters assignments into given database given (by id), or creates a new database, and fills the page with assignments not already found in the database
    def enterAssignmentsToNotionDb(self, courseList, timeframe=None):
        if not self.notionProfile.test_if_database_id_exists():
            self.notionProfile = NotionApi(
                self.notionToken,
                database_id=self.createDatabase(properties=self.db_properties),
                schoolAb=self.schoolAb,
                semester_start_date=self.semester_start_date,
                semester_end_date=self.semester_end_date,
                semester_label=self.semester_label,
                semester_phases=self.semester_phases,
            )
        # Cache DB properties once to ensure we only send supported fields.
        self.notionProfile.refresh_database_properties()

        created, create_errors = self.addNewDatabaseItems(courseList, timeframe)
        updated, update_errors = self.updateExistingDatabaseItems(courseList)

        errors = []
        errors.extend(create_errors)
        errors.extend(update_errors)

        return {"created": created, "updated": updated, "errors": errors}

    # Creates a new Canvas Assignments database in the notionPageId page
    def createDatabase(self, page_id_name="Default", properties=None):
        return self.notionProfile.createNewDatabase(self.page_ids[page_id_name], properties=properties)

    # This function adds NEW assignments to the database based on whether the assignments URL can be found in the notion database
    def addNewDatabaseItems(self, courseList, timeframe=None):
        self.canvasProfile.set_courses_and_id()
        created = 0
        errors = []
        existing_by_url = self.notionProfile.parseDatabaseForAssignments()
        existing_by_key = self.notionProfile.parseDatabaseForAssignmentsByKey()

        for course in courseList:
            assignmentObjects = self.canvasProfile.get_assignment_objects(
                course.name, timeframe
            )
            for assignment in assignmentObjects:
                assignment_url = assignment.get("url")
                assignment_key = f"{course.name}||{assignment.get('name')}"

                if assignment_url in existing_by_url or assignment_key in existing_by_key:
                    continue

                due_date = assignment.get("due_at")
                dueDate = (
                    date_to_sg_offset_iso(due_date)
                    if due_date is not None
                    else None
                )
                try:
                    res = self.notionProfile.createNewDatabaseItem(
                        id=assignment["id"],
                        className=course.name,
                        dueDate=dueDate,
                        url=assignment["url"],
                        assignmentName=assignment["name"],
                        has_submitted=assignment["has_submitted_submissions"],
                    )
                    status = getattr(res, 'status_code', None)
                    if status and 200 <= status < 300:
                        created += 1
                    else:
                        errors.append({"action": "create", "course": course.name, "url": assignment.get("url"), "response": getattr(res, 'text', str(res))})
                except Exception as e:
                    errors.append({"action": "create", "course": course.name, "url": assignment.get("url"), "error": str(e)})

        return created, errors
    
    # This function updates EXISTING assignments in the database based on whether the assignments URL can be found in the notion database
    def updateExistingDatabaseItems(self, courseList):
        self.canvasProfile.set_courses_and_id()
        updated = 0
        errors = []
        notionAssignments = self.notionProfile.parseDatabaseForAssignments()
        notionAssignmentsByKey = self.notionProfile.parseDatabaseForAssignmentsByKey()

        for course in courseList:
            courseName = course.name
            assignmentObjects = self.canvasProfile.get_assignment_objects(courseName)

            for assignment in assignmentObjects:
                assignment_url = assignment.get("url")
                assignment_key = f"{courseName}||{assignment.get('name')}"
                page_id = None
                if assignment_url in notionAssignments:
                    page_id = notionAssignments.get(assignment_url)
                elif assignment_key in notionAssignmentsByKey:
                    page_id = notionAssignmentsByKey.get(assignment_key)

                if page_id:
                    due_date = assignment.get("due_at")
                    dueDate = (
                        date_to_sg_offset_iso(due_date)
                        if due_date is not None
                        else None
                    )

                    try:
                        res = self.notionProfile.updateDatabaseItem(
                            page_id=page_id,
                            className=courseName,
                            dueDate=dueDate,
                            assignmentName=assignment["name"],
                            has_submitted=assignment["has_submitted_submissions"],
                        )
                        status = getattr(res, 'status_code', None)
                        if status and 200 <= status < 300:
                            updated += 1
                        else:
                            errors.append({"action": "update", "course": courseName, "url": assignment.get("url"), "response": getattr(res, 'text', str(res))})
                    except Exception as e:
                        errors.append({"action": "update", "course": courseName, "url": assignment.get("url"), "error": str(e)})

        return updated, errors

    # This function adds all found assignments to the notion database
    def rawFillDatabase(self, courseList):
        self.canvasProfile.set_courses_and_id()
        for course in courseList:
            for assignment in self.canvasProfile.get_assignment_objects(
                course.name, "upcoming"
            ):
                self.notionProfile.createNewDatabaseItem(
                    id=assignment["id"],
                    className=course.name,
                    dueDate=date_to_sg_offset_iso(assignment["due_at"]),
                    url=assignment["url"],
                    assignmentName=assignment["name"],
                    has_submitted=assignment["has_submitted_submissions"],
                )
