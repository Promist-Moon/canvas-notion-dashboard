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
        self._db_properties = None

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

    def _get_database_properties(self):
        if not self.database_id:
            return {}
        if self._db_properties is not None:
            return self._db_properties

        res = requests.request(
            "GET",
            f"https://api.notion.com/v1/databases/{self.database_id}/",
            headers=self.notionHeaders,
        )
        data = res.json() if res is not None else {}
        self._db_properties = data.get("properties", {}) if isinstance(data, dict) else {}
        return self._db_properties

    def _filter_properties_for_database(self, properties):
        db_properties = self._get_database_properties()
        if not db_properties:
            return properties
        return {name: value for name, value in properties.items() if name in db_properties}

    def _build_status_property(self, status_name):
        db_properties = self._get_database_properties()
        status_prop = db_properties.get("Status") if db_properties else None
        if status_prop and status_prop.get("type") == "select":
            return {"select": {"name": status_name}}
        return {"status": {"name": status_name}}

    def _build_properties_schema(self, property_names):
        """Build Notion property schema from a list of property names.
        
        Always includes required properties: Assignment (title), Class (course), Due Date
        Uses the default NOTION_DB_PROPERTIES as reference to build schema
        for the requested properties plus required ones.
        """
        # Required properties that must always be included
        required_props = ['Assignment', 'Class', 'Due Date']
        
        # Start with required properties
        schema = {}
        for prop in required_props:
            if prop in NOTION_DB_PROPERTIES:
                schema[prop] = NOTION_DB_PROPERTIES[prop]
        
        # Add any additional selected properties
        if property_names:
            for prop_name in property_names:
                if prop_name in NOTION_DB_PROPERTIES and prop_name not in schema:
                    schema[prop_name] = NOTION_DB_PROPERTIES[prop_name]
        
        return schema if schema else NOTION_DB_PROPERTIES

    # Creates a new database in page_id page built for Canvas assignments and returns it's database_id
    def createNewDatabase(self, page_id, properties=None):
        # Use provided properties or fall back to default
        db_properties = properties if properties else NOTION_DB_PROPERTIES
        
        # If properties is a list, convert to dict schema
        if isinstance(db_properties, list):
            db_properties = self._build_properties_schema(db_properties)
        
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
            "properties": db_properties,
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

        properties = {
            "Status": self._build_status_property(status_name),
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
        }

        newPageData = {
            "parent": {"database_id": self.database_id},
            "properties": self._filter_properties_for_database(properties),
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

        properties = {
            "Status": self._build_status_property(status_name),
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
        }

        updatePageData = {
            "properties": self._filter_properties_for_database(properties),
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
