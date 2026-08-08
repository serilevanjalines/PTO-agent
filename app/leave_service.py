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


def validate_leave_reason(leave_type: str, reason: str):
    """
    Validate that a leave reason is provided and is distinct
    from the leave type.
    """

    if not reason or not reason.strip():
        raise ValueError(
            "A leave reason is required before submitting the request."
        )

    if leave_type.strip().lower() == reason.strip().lower():
        raise ValueError(
            f"Leave type '{leave_type}' and leave reason "
            f"'{reason}' cannot be the same."
        )
    
    return reason



def normalize_dates(
    start_date: str,
    end_date: str,
):
    """
    Normalize user-provided dates into YYYY-MM-DD format.

    Supported formats:
    - 2026-08-04
    - Aug 4
    - August 4
    - 4 Aug
    - 4 August
    - Aug 4 2026
    - August 4, 2026
    - 4 Aug 2026

    If the year is omitted, the next occurrence of that
    date relative to today is used.
    """

    today = date.today()

    supported_formats = [

        # ISO
        "%Y-%m-%d",

        # Month Day
        "%b %d",
        "%B %d",

        # Day Month
        "%d %b",
        "%d %B",

        # Month Day Year
        "%b %d %Y",
        "%B %d %Y",

        # Month Day, Year
        "%b %d, %Y",
        "%B %d, %Y",

        # Day Month Year
        "%d %b %Y",
        "%d %B %Y",
    ]


    def parse_single(raw_date: str):

        raw_date = raw_date.strip()

        for fmt in supported_formats:

            try:

                parsed = datetime.strptime(raw_date, fmt)

                # Year already supplied
                if "%Y" in fmt:
                    return parsed.date().strftime("%Y-%m-%d")

                # Year missing
                parsed = parsed.replace(year=today.year)

                parsed_date = parsed.date()

                if parsed_date < today:
                    parsed_date = parsed_date.replace(
                        year=today.year + 1
                    )

                return parsed_date.strftime("%Y-%m-%d")

            except ValueError:
                continue

        raise ValueError(
            f"Could not understand date '{raw_date}'. "
            "Use formats like "
            "'2026-08-04', 'Aug 4', or 'August 4, 2026'."
        )

    normalized_start = parse_single(start_date)
    normalized_end = parse_single(end_date)

    return normalized_start, normalized_end

    
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
            f"But today's date is {today} , Start date {start_date} cannot be in the past."
        )

    if start > end:
        raise ValueError(
            f"BUt today's date is {today} Start date cannot be after end date."
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


    validate_employee(employee_id)

    validate_leave_type(
        employee_id,
        leave_type,
    )

    validate_leave_reason(leave_type,reason)

    start_date, end_date = normalize_dates(
    start_date,
    end_date
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