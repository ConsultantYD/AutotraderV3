import datetime as dt

from croniter import croniter


def is_datetime_in_cron_range(timestamp: dt.datetime, cron_expr: str) -> bool:
    """
    Check if a given datetime matches a cron expression.

    Args:
        dt (datetime): The datetime to check.
        cron_expr (str): The cron expression to match against.

    Returns:
        bool: True if the datetime matches the cron expression, False otherwise.
    """
    # Normalize datetime to the nearest minute
    timestamp = timestamp.replace(second=0, microsecond=0)

    # Create a cron iterator starting at the current datetime
    cron = croniter(cron_expr, timestamp)

    # Get the next and previous matching times
    next_time = cron.get_next(dt.datetime)
    prev_time = cron.get_prev(dt.datetime)

    # Check if the current time exactly matches either the next or previous match
    return prev_time == timestamp or next_time == timestamp


# Example usage
if __name__ == "__main__":
    cron_expression = "* 9-15 * * 1-5"  # Trading window: 9:00 AM to 3:59 PM on weekdays
    test_time = dt.datetime(2024, 12, 20, 15, 59)  # Monday at 1:00 PM

    print(is_datetime_in_cron_range(test_time, cron_expression))  # Output: True
