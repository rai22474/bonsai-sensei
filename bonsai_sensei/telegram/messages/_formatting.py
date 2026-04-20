from datetime import datetime


def format_date(date_value) -> str:
    if isinstance(date_value, str):
        date_value = datetime.strptime(date_value, "%Y-%m-%d").date()
    return date_value.strftime("%d/%m/%Y")
