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
    ):
        self.notionToken = notionToken
        self.database_id = database_id
        self.canvasProfile = CanvasApi(canvasKey, schoolAb)
        self.page_ids = {"Default": notionPageId}
        self.generated_db_id = None
        self.schoolAb = schoolAb
        self.notionProfile = NotionApi(
            notionToken,
            database_id=database_id,
            schoolAb=schoolAb,
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
                database_id=self.createDatabase(),
                schoolAb=self.schoolAb,
            )

        created, create_errors = self.addNewDatabaseItems(courseList, timeframe)
        updated, update_errors = self.updateExistingDatabaseItems(courseList)

        errors = []
        errors.extend(create_errors)
        errors.extend(update_errors)

        return {"created": created, "updated": updated, "errors": errors}

    # Creates a new Canvas Assignments database in the notionPageId page
    def createDatabase(self, page_id_name="Default"):
        return self.notionProfile.createNewDatabase(self.page_ids[page_id_name])

    # This function adds NEW assignments to the database based on whether the assignments URL can be found in the notion database
    def addNewDatabaseItems(self, courseList, timeframe=None):
        self.canvasProfile.set_courses_and_id()
        created = 0
        errors = []
        for course in courseList:
            for assignment in self.canvasProfile.update_assignment_objects(
                self.notionProfile.parseDatabaseForAssignments(),
                course.name,
                timeframe,
            ):
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

        for course in courseList:
            courseName = course.name
            assignmentObjects = self.canvasProfile.get_assignment_objects(courseName)

            for assignment in assignmentObjects:
                if assignment["url"] in notionAssignments:
                    due_date = assignment.get("due_at")
                    dueDate = (
                        date_to_sg_offset_iso(due_date)
                        if due_date is not None
                        else None
                    )

                    try:
                        res = self.notionProfile.updateDatabaseItem(
                            page_id=notionAssignments[assignment["url"]],
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
