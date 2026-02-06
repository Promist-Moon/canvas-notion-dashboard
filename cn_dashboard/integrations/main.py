from .user import User
import os
from dotenv import load_dotenv

load_dotenv()

canvasKey = os.getenv("LMS_API_KEY")
notionToken = os.getenv("NOTION_TOKEN")
notionPageId = os.getenv("NOTION_PAGE_ID")
schoolAb = os.getenv("SCHOOL_AB_KR")
databaseId = os.getenv("DATABASE_ID")

# if you want to use an existing database, uncomment below
user = User(canvasKey, notionToken, notionPageId, schoolAb, database_id=databaseId)

# if you want to create a new database, uncomment below
# user = User(canvasKey, notionToken, notionPageId, schoolAb)

# create database
# user.createDatabase()

"""
Stop here to create a status object in database first, with the default settings.
Else, you will get an error message that status property does not exist.
"""
courses = user.getAllCourses()
user.enterAssignmentsToNotionDb(courses)