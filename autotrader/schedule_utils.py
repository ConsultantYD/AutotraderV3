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


def is_datetime_in_any_cron_range(
    timestamp: dt.datetime, cron_ranges: list[str]
) -> bool:
    """
    Check if a given datetime matches any cron expression in a list.

    Args:
        timestamp (datetime): The datetime to check.
        cron_ranges (list[str]): A list of cron expressions to match against.

    Returns:
        bool: True if the datetime matches any of the cron expressions, False otherwise.
    """
    return any(
        is_datetime_in_cron_range(timestamp, cron_expr) for cron_expr in cron_ranges
    )


# Example usage
if __name__ == "__main__":
    cron_list = ["15-59 9 * * 1-5", "* 10-13 * * 1-5", "0-30 14 * * 1-5"]
    exit_cron_list = ["45-59 14 * * 1-5", "* 15-19 * * 1-5", "0-45 20 * * 1-5"]
    t = dt.datetime(2024, 12, 17, 0, 0)

    print("OPENING HOURS")
    while t < dt.datetime(2024, 12, 24, 0, 0):
        if is_datetime_in_any_cron_range(t, cron_list):
            print(t)
        t += dt.timedelta(minutes=1)

    print("\nCLOSING HOURS")
    t = dt.datetime(2024, 12, 17, 0, 0)
    while t < dt.datetime(2024, 12, 24, 0, 0):
        if not is_datetime_in_any_cron_range(t, exit_cron_list):
            print("exit at ", t)
        t += dt.timedelta(minutes=1)
