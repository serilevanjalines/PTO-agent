import json

from . import config

_REQUESTS = json.loads(
    (config.DATA_DIR / "requests.json").read_text()
)

_REQUESTS_BY_EMPLOYEE = {}

for request in _REQUESTS:
    employee_id = request["employee_id"]

    if employee_id not in _REQUESTS_BY_EMPLOYEE:
        _REQUESTS_BY_EMPLOYEE[employee_id] = []

    _REQUESTS_BY_EMPLOYEE[employee_id].append(request)


def list_leave_requests(employee_id: str,status: str | None = None,leave_type: str | None = None,) -> list[dict]:
    """
    Return all leave requests for an employee,
    optionally filtered by status and leave type.
    """
    employee_requests = _REQUESTS_BY_EMPLOYEE.get(employee_id, [])
    filtered_requests = []
    
    for request in employee_requests:
        if status is not None and request["status"] != status:
            continue
        if leave_type is not None and request["leave_type"] != leave_type:
            continue
        filtered_requests.append(request)

    return filtered_requests