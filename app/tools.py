import json

from . import config

_REQUESTS = json.loads(
    (config.DATA_DIR / "requests.json").read_text()
)

__BALANCES = json.loads(
    (config.DATA_DIR / "balances.json").read_text()
)

_REQUESTS_BY_EMPLOYEE = {}

_BALANCES_BY_EMPLOYEE = {}

for request in _REQUESTS:
    employee_id = request["employee_id"]

    if employee_id not in _REQUESTS_BY_EMPLOYEE:
        _REQUESTS_BY_EMPLOYEE[employee_id] = []

    _REQUESTS_BY_EMPLOYEE[employee_id].append(request)



for balance in __BALANCES:
    employee_id = balance["employee_id"]
    
    if employee_id not in _BALANCES_BY_EMPLOYEE:
        _BALANCES_BY_EMPLOYEE[employee_id] = []

    _BALANCES_BY_EMPLOYEE[employee_id].append(balance)


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




def check_balance(employee_id: str,leave_type: str|None=None) -> list[dict]:
    """
    Return the leave balance for an employee and leave type,
    or None if not found.
    """
    employee_balances  = _BALANCES_BY_EMPLOYEE.get(employee_id, [])
    filtered_balances = []

    for balance in employee_balances:
        if leave_type is not None and balance["leave_type"] != leave_type:
            continue
        filtered_balances.append(balance)

    return filtered_balances