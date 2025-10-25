import os
import datetime
from datetime import timezone

def get_utc_datetime():
    """
    Get the current UTC datetime as an ISO 8601 string with microsecond precision.
    """
    return datetime.datetime.now(timezone.utc).isoformat()


# print(get_utc_datetime())