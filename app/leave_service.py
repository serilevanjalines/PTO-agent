from .email_service import send_email
from .data_store import _EMPLOYEES,_BALANCES_BY_EMPLOYEE,_REQUESTS_BY_EMPLOYEE,_REQUESTS,save_requests
from datetime import datetime, date
from . import config
import logging

logger = logging.getLogger(__name__)



def validate_employee(employee_id: str):
    """
    Validate that the employee exists.
    """
    
    if employee_id not in _EMPLOYEES:
        raise ValueError(f"Employee {employee_id} not found.")
    
    return _EMPLOYEES[employee_id]
    



def validate_leave_type(employee_id: str, leave_type: str):
    """
    Validate that the employee has this type of leave.
    """
    
    balances = _BALANCES_BY_EMPLOYEE.get(employee_id, [])

    for balance in balances:
        if balance["leave_type"] == leave_type:
            return balance

    raise ValueError(f"Employee {employee_id} does not have leave type {leave_type}.")




def validate_dates(start_date: str, end_date: str):
    """
    Validate that the leave dates are valid
    and the start date is not in the past.
    """

    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()

    except ValueError:
        raise ValueError(
            "Dates must be in YYYY-MM-DD format."
        )

    today = date.today()

    if start < today:
        raise ValueError(
            f"Start date {start_date} cannot be in the past."
        )

    if start > end:
        raise ValueError(
            "Start date cannot be after end date."
        )

    return True



def calculate_leave_days(start_date: str, end_date: str) -> int:
    """
    Calculate the number of leave days between start and end dates.
    """

    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()

    delta = end - start

    return delta.days + 1  



def check_leave_balance(employee_id: str, leave_type: str, requested_days: int):
    """
    Check if the employee has enough leave balance for the requested leave type.
    """

    balance = validate_leave_type(employee_id, leave_type)

    if balance["remaining_days"] < requested_days:
        raise ValueError(
            f"Insufficient leave balance. "
            f"Available: {balance['remaining_days']}, "
            f"Requested: {requested_days}."
        )

    return True





def check_duplicate_or_overlapping_request(
    employee_id: str,
    start_date: str,
    end_date: str
):
    """
    Check whether the employee already has a pending or approved
    leave request that overlaps with the requested dates.
    """

    new_start = datetime.strptime(start_date, "%Y-%m-%d").date()
    new_end = datetime.strptime(end_date, "%Y-%m-%d").date()

    existing_requests = _REQUESTS_BY_EMPLOYEE.get(employee_id, [])

    for request in existing_requests:

        if request["status"] not in ["approved", "pending"]:
            continue

        existing_start = datetime.strptime(
            request["start_date"], "%Y-%m-%d"
        ).date()

        existing_end = datetime.strptime(
            request["end_date"], "%Y-%m-%d"
        ).date()

        if (
            new_start <= existing_end
            and new_end >= existing_start
        ):
            raise ValueError(
                f"Leave request overlaps with existing "
                f"{request['status']} request {request['id']} "
                f"from {request['start_date']} to {request['end_date']}."
            )

    return True




def create_leave_request(
    employee_id: str,
    leave_type: str,
    start_date: str,
    end_date: str,
    reason: str
) -> dict:
    
    request_id = f"REQ-{1000 + len(_REQUESTS) + 1}"

    new_request = {
        "id": request_id,
        "employee_id": employee_id,
        "leave_type": leave_type,
        "start_date": start_date,
        "end_date": end_date,
        "reason": reason,
        "status": "pending"
    }

    _REQUESTS.append(new_request)

    if employee_id not in _REQUESTS_BY_EMPLOYEE:
        _REQUESTS_BY_EMPLOYEE[employee_id] = []

    _REQUESTS_BY_EMPLOYEE[employee_id].append(new_request)

    return new_request



def notify_hr(leave_request: dict):
    """
    Notify HR about a newly submitted leave request.
    """

    employee = _EMPLOYEES[leave_request["employee_id"]]

    subject = (
        f"New Leave Request - {leave_request['id']}"
    )

    body = (
        f"Hello HR,\n\n"
        f"A new leave request has been submitted.\n\n"
        f"Employee : {employee['full_name']} ({employee['id']})\n"
        f"Country : {employee['country']}\n"
        f"Leave Type : {leave_request['leave_type']}\n"
        f"Start Date : {leave_request['start_date']}\n"
        f"End Date : {leave_request['end_date']}\n"
        f"Reason : {leave_request['reason']}\n"
        f"Status : {leave_request['status']}\n\n"
        f"Please review this request.\n\n"
        f"Regards,\n"
        f"PTO Agent"
    )

    try:
        send_email(
            recipient=config.HR_EMAIL,
            subject=subject,
            body=body,
        )

    except Exception:
        logger.exception(
            "Failed to send HR notification for request %s",
            leave_request["id"],
        )

    



def normalize_leave_type(leave_type: str) -> str:
    """
    Normalize user/LLM leave type names to internal values.
    """

    leave_type = leave_type.lower().strip()

    aliases = {
        "annual leave": "annual",
        "vacation": "annual",
        "vacation leave": "annual",

        "sick leave": "sick",

        "earned leave": "earned",

        "casual sick leave": "casual_sick",
    }

    return aliases.get(leave_type, leave_type)





def submit_leave_request(
    employee_id: str,
    leave_type: str,
    start_date: str,
    end_date: str,
    reason: str,
):
    """
    Submit a leave request after performing all validations.
    """

    leave_type = normalize_leave_type(leave_type)

    validate_employee(employee_id)

    validate_leave_type(
        employee_id,
        leave_type,
    )

    validate_dates(
        start_date,
        end_date,
    )

    requested_days = calculate_leave_days(
        start_date,
        end_date,
    )

    check_leave_balance(
        employee_id,
        leave_type,
        requested_days,
    )

    check_duplicate_or_overlapping_request(
        employee_id,
        start_date,
        end_date,
    )

    new_request = create_leave_request(
        employee_id,
        leave_type,
        start_date,
        end_date,
        reason,
    )

    save_requests()

    notify_hr(new_request)

    return {
        "message": "Leave request submitted successfully.",
        "request": new_request,
    }