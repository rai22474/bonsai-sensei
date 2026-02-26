from datetime import date


def get_current_date() -> dict:
    """Returns today's date in ISO format (YYYY-MM-DD).

    Use this tool whenever you need to know the current date, for example to
    interpret relative dates like "next week" or to provide context when
    delegating planning requests to other agents.

    Returns:
        A dict with today's date.
        Output JSON: {"date": "YYYY-MM-DD"}.
    """
    return {"date": date.today().isoformat()}
