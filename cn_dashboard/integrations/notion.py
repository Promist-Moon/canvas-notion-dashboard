import requests, json
from .config.schema import NOTION_DB_PROPERTIES
from .scripts.select_helpers import compute_week_from_due, compute_semester_from_due

class NotionApi:
    def __init__(
        self,
        notionToken=None,
        database_id=None,
        schoolAb=None,
        version="2021-08-16",
    ):
        self.database_id = database_id
        self.notionToken = notionToken
        self.schoolAb = schoolAb
        self.notionHeaders = {
            "Authorization": "Bearer " + notionToken,
            "Content-Type": "application/json",
            "Notion-Version": "2021-08-16",
        }

    def queryDatabase(self):
        readUrl = f"https://api.notion.com/v1/databases/{self.database_id}/query"

        res = requests.request("POST", readUrl, headers=self.notionHeaders)
        data = res.json()

        with open("./db.json", "w", encoding="utf8") as f:
            json.dump(data, f, ensure_ascii=False)

        return data

    def test_if_database_id_exists(self):
        res = requests.request(
            "GET",
            f"https://api.notion.com/v1/databases/{self.database_id}/",
            headers=self.notionHeaders,
        )

        return json.loads(res.text)["object"] != "error"

    # Creates a new database in page_id page built for Canvas assignments and returns it's database_id
    def createNewDatabase(self, page_id):
        newPageData = {
            "parent": {
                "type": "page_id",
                "page_id": page_id,
            },
            "icon": {"type": "emoji", "emoji": "🔖"},
            "cover": {
                "type": "external",
                "external": {"url": "https://website.domain/images/image.png"},
            },
            "title": [
                {
                    "type": "text",
                    "text": {
                        "content": "Canvas Assignments",
                        "link": None,
                    },
                }
            ],
            "properties": NOTION_DB_PROPERTIES,
        }

        data = json.dumps(newPageData)

        res = requests.request(
            "POST",
            "https://api.notion.com/v1/databases",
            headers=self.notionHeaders,
            data=data,
        )

        print(res.text)

        newDbId = json.loads(res.text).get("id")

        return newDbId

    def createNewDatabaseItem(
        self,
        id,
        className,
        assignmentName,
        has_submitted=False,
        url=None,
        dueDate=None,
    ):
        # if status:
        #     status = "To do"
        # else:
        #     status = "Completed"

        createUrl = "https://api.notion.com/v1/pages"

        status_name = "Done" if has_submitted else "Not started"

        newPageData = {
            "parent": {"database_id": self.database_id},
            "properties": {
                "Status": {
                    "status": {
                        "name": status_name,
                    }
                },
                "Assignment": {
                    "type": "title",
                    "title": [
                        {
                            "text": {
                                "content": assignmentName,
                            },
                        }
                    ],
                },
                "Class": {
                    "select": {
                        "name": className,
                    }
                },
                "Due Date": {
                    "date": {
                        "start": dueDate,
                    } if dueDate else None,
                },
                "URL": {
                    "url": url,
                },
                "Week": {
                    "select": {
                        "name": compute_week_from_due(dueDate),
                    }
                },
                "Semester": {
                    "select": {
                        "name": compute_semester_from_due(dueDate),
                    }
                },
            },
        }

        data = json.dumps(newPageData)

        res = requests.request("POST", createUrl, headers=self.notionHeaders, data=data)

        print(res.text)

        return res
    
    def updateDatabaseItem(
        self,
        page_id,
        className,
        assignmentName,
        has_submitted=False,
        url=None,
        dueDate=None,
    ):
        updateUrl = f"https://api.notion.com/v1/pages/{page_id}"

        status_name = "Done" if has_submitted else "Not started"

        updatePageData = {
            "properties": {
                "Status": {
                    "status": {
                        "name": status_name,
                    }
                },
                "Assignment": {
                    "type": "title",
                    "title": [
                        {
                            "text": {
                                "content": assignmentName,
                            },
                        }
                    ],
                },
                "Class": {
                    "select": {
                        "name": className,
                    }
                },
                "Due Date": {
                    "date": {
                        "start": dueDate,
                    } if dueDate else None,
                },
                "URL": {
                    "url": url,
                },
                "Week": {
                    "select": {
                        "name": compute_week_from_due(dueDate),
                    }
                },
                "Semester": {
                    "select": {
                        "name": compute_semester_from_due(dueDate),
                    }
                },
            },
        }

        data = json.dumps(updatePageData)

        res = requests.request("PATCH", updateUrl, headers=self.notionHeaders, data=data)

        print(res.text)

        return res

    def parseDatabaseForAssignments(self):
        # Return a mapping of assignment URL -> notion page id for quick lookups
        mapping = {}
        data = self.queryDatabase()

        results = data.get("results") if data is not None else []
        if results:
            for item in results:
                try:
                    url = item["properties"]["URL"]["url"]
                    page_id = item.get("id")
                    if url:
                        mapping[url] = page_id
                except Exception:
                    continue

        return mapping
