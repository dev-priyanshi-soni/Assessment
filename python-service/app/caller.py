from .models import Caller

CALLERS = {
    "atlas-employee-01": Caller(caller_id="atlas-employee-01", tenant="Atlas", role="employee"),
    "atlas-contractor-01": Caller(caller_id="atlas-contractor-01", tenant="Atlas", role="contractor"),
    "boreal-employee-01": Caller(caller_id="boreal-employee-01", tenant="Boreal", role="employee"),
}

def get_caller(caller_id: str) -> Caller:
    if caller_id not in CALLERS:
        raise ValueError("UNKNOWN_CALLER")
    return CALLERS[caller_id]
