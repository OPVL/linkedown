from datetime import datetime
from time import time


def pretty_date(time=False):
    """
    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc
    """
    from datetime import datetime

    now = datetime.now()
    if type(time) is int:
        diff = now - datetime.fromtimestamp(time)
    elif isinstance(time, datetime):
        diff = now - time
    elif not time:
        diff = 0
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ""

    if day_diff == 0:
        if second_diff < 10:
            return "just now"
        if second_diff < 60:
            return f"{str(second_diff)} seconds ago"
        if second_diff < 120:
            return "a minute ago"
        if second_diff < 3600:
            return f"{str(second_diff // 60)} minutes ago"
        if second_diff < 7200:
            return "an hour ago"
        if second_diff < 86400:
            return f"{str(second_diff // 3600)} hours ago"
    if day_diff == 1:
        return "Yesterday"
    if day_diff < 7:
        return str(day_diff) + " days ago"
    if day_diff < 31:
        return str(day_diff // 7) + " weeks ago"
    if day_diff < 365:
        return str(day_diff // 30) + " months ago"
    return str(day_diff // 365) + " years ago"


def pretty_time_difference(start_time: float) -> str:
    seconds = int(time() - start_time)

    if seconds < 60:
        return f"{seconds} seconds"

    if seconds < 120:
        return f"1 minute {seconds % 60} seconds"

    if seconds < 3600:
        return f"{seconds // 60} minutes {seconds % 60} seconds"

    if seconds < 7200:
        return f"1 hour {seconds // 3600} minutes {seconds % 60} seconds"

    return f"{seconds // 3600} hours {seconds // 3600} minutes {seconds % 60} seconds"
