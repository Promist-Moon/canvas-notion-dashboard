import requests, json
from .config.schema import NOTION_DB_PROPERTIES
from .scripts.select_helpers import compute_week_from_due, compute_semester_from_due

class NotionApi:
    def __init__(
        self,
        notionToken=None,
        database_id=None,
        schoolAb=None,
        semester_start_date=None,
        semester_end_date=None,
        semester_label=None,
        semester_phases=None,
        version="2021-08-16",
    ):
        self.database_id = database_id
        self.notionToken = notionToken
        self.schoolAb = schoolAb
        self.semester_start_date = semester_start_date
        self.semester_end_date = semester_end_date
        self.semester_label = semester_label
        self.semester_phases = semester_phases or []
        self.notionHeaders = {
            "Authorization": "Bearer " + notionToken,
            "Content-Type": "application/json",
            "Notion-Version": "2021-08-16",
        }
        self._db_properties = None
        self._assignment_cache = None

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

    def refresh_database_properties(self):
        self._db_properties = None
        self._assignment_cache = None
        return self._get_database_properties()

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
                        "name": compute_week_from_due(
                            dueDate,
                            custom_range=(self.semester_start_date, self.semester_end_date),
                            custom_label=self.semester_label,
                            custom_phases=self.semester_phases,
                        ),
                    }
                },
                "Semester": {
                    "select": {
                        "name": compute_semester_from_due(
                            dueDate,
                            custom_range=(self.semester_start_date, self.semester_end_date),
                            custom_label=self.semester_label,
                            custom_phases=self.semester_phases,
                        ),
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
                        "name": compute_week_from_due(
                            dueDate,
                            custom_range=(self.semester_start_date, self.semester_end_date),
                            custom_label=self.semester_label,
                            custom_phases=self.semester_phases,
                        ),
                    }
                },
                "Semester": {
                    "select": {
                        "name": compute_semester_from_due(
                            dueDate,
                            custom_range=(self.semester_start_date, self.semester_end_date),
                            custom_label=self.semester_label,
                            custom_phases=self.semester_phases,
                        ),
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
        return self._parse_database_for_assignments().get("by_url", {})

    def parseDatabaseForAssignmentsByKey(self):
        # Return a mapping of (class|assignment) -> notion page id for quick lookups
        return self._parse_database_for_assignments().get("by_key", {})

    def _parse_database_for_assignments(self):
        if self._assignment_cache is not None:
            return self._assignment_cache

        mapping_by_url = {}
        mapping_by_key = {}
        data = self.queryDatabase()

        results = data.get("results") if data is not None else []
        if results:
            for item in results:
                page_id = item.get("id")
                props = item.get("properties", {})

                url = None
                try:
                    url = props.get("URL", {}).get("url")
                except Exception:
                    url = None

                assignment_title = None
                try:
                    title_parts = props.get("Assignment", {}).get("title", [])
                    assignment_title = "".join([t.get("plain_text", "") for t in title_parts]).strip() or None
                except Exception:
                    assignment_title = None

                class_name = None
                try:
                    class_name = props.get("Class", {}).get("select", {}).get("name")
                except Exception:
                    class_name = None

                if url:
                    mapping_by_url[url] = page_id
                if class_name and assignment_title:
                    key = f"{class_name}||{assignment_title}"
                    mapping_by_key[key] = page_id

        self._assignment_cache = {
            "by_url": mapping_by_url,
            "by_key": mapping_by_key,
        }
        return self._assignment_cache
