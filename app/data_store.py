import json
from . import config


employees = json.loads(
    (config.DATA_DIR / "employees.json").read_text()
)

_EMPLOYEES = {}

for e in employees:
    key = e["id"]
    value = e
    _EMPLOYEES[key] = value


_REQUESTS = json.loads(
    (config.DATA_DIR / "requests.json").read_text()
)

_REQUESTS_BY_EMPLOYEE = {}


for request in _REQUESTS:
    employee_id = request["employee_id"]

    if employee_id not in _REQUESTS_BY_EMPLOYEE:
        _REQUESTS_BY_EMPLOYEE[employee_id] = []

    _REQUESTS_BY_EMPLOYEE[employee_id].append(request)



__BALANCES = json.loads(
    (config.DATA_DIR / "balances.json").read_text()
)


_BALANCES_BY_EMPLOYEE = {}




for balance in __BALANCES:
    employee_id = balance["employee_id"]
    
    if employee_id not in _BALANCES_BY_EMPLOYEE:
        _BALANCES_BY_EMPLOYEE[employee_id] = []

    _BALANCES_BY_EMPLOYEE[employee_id].append(balance)




def save_requests():
    """
    Persist all leave requests to requests.json.
    """

    (config.DATA_DIR / "requests.json").write_text(
        json.dumps(
            _REQUESTS,
            indent=2
        )
    )
    