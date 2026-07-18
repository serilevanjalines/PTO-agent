import json
from .data_store import _EMPLOYEES , _REQUESTS_BY_EMPLOYEE ,_BALANCES_BY_EMPLOYEE
from . import config
from .rag import hybrid_search
from .leave_service import submit_leave_request as submit_leave


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


def search_policy(query: str, employee_id:str, top_k: int = 3,):
    """
    Search company leave policies using Hybrid RAG.
    """

    employee = _EMPLOYEES[employee_id]
    country = employee["country"]
    
    retrieved_chunks = hybrid_search(
    query=query,
    country=country,
    top_k=top_k,
    )

    contexts = []

    for chunk in retrieved_chunks:
        contexts.append(
        f"""Policy: {chunk["policy"]}
        Country: {chunk["country"]}

        {chunk["text"]}"""
        )

    return "\n\n----------------------\n\n".join(contexts)



def submit_leave_request(
    employee_id: str,
    leave_type: str,
    start_date: str,
    end_date: str,
    reason: str,
):
    """
    Submit a leave request.
    """

    return submit_leave(employee_id , leave_type , start_date , end_date , reason)
    