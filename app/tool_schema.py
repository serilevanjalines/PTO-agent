TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_policy",
            "description": "Search company leave policies using hybrid retrieval.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The user's policy question."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_balance",
            "description": "Check an employee's leave balance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_id": {
                        "type": "string",
                        "description": "The ID of the employee."
                    },
                    "leave_type": {
                        "type": "string",
                        "description": "The type of leave to check."
                    }
                },
                "required": ["employee_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_leave_requests",
            "description": "List an employee's leave requests.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_id": {
                        "type": "string",
                        "description": "The ID of the employee."
                    },
                    "status": {
                        "type": "string",
                        "description": "The status of the leave requests to list."
                    },
                    "leave_type": {
                        "type": "string",
                        "description": "The type of leave to list."
                    }
                },
                "required": ["employee_id"]
            }
        }
    }
]

