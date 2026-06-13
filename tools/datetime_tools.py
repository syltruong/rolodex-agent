import datetime
from agents import function_tool


@function_tool
def get_current_datetime() -> str:
    """Return the current local date and time in ISO 8601 format."""
    return datetime.datetime.now().isoformat(timespec="seconds")
