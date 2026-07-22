from datetime import datetime


def format_date(date_str: str | None, language: str) -> str | None:
    if not date_str:
        return None

    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return date_str

    if language == "he":
        return dt.strftime("%d/%m/%Y")

    return dt.strftime("%B %d, %Y")


def format_time_range(
    start_time: str | None,
    end_time: str | None,
) -> str | None:

    if start_time and end_time:
        return f"{start_time[:5]} - {end_time[:5]}"

    if start_time:
        return start_time[:5]

    return None


def translate_repeat_type(
    repeat_type: str | None,
    language: str,
) -> str | None:

    if repeat_type is None:
        return None

    translations = {
        "he": {
            "none": "ללא חזרה",
            "daily": "יומי",
            "weekly": "שבועי",
            "monthly": "חודשי",
            "yearly": "שנתי",
        },
        "en": {
            "none": "Does not repeat",
            "daily": "Daily",
            "weekly": "Weekly",
            "monthly": "Monthly",
            "yearly": "Yearly",
        },
    }

    return translations.get(language, translations["en"]).get(
        repeat_type,
        repeat_type,
    )