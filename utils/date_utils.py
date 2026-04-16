from convertdate import hebrew


def hebrew_month_length(year: int, month: int) -> int:
    return int(hebrew.month_days(year, month))

