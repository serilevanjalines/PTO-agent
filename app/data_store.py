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
