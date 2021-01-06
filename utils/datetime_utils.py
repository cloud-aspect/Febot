"""Utility functions for datetime objects"""

def td_format(td_object, precision='day'):
    """converts timedelta to a nice human readable str with years, months, days"""
    seconds = int(td_object.total_seconds())
    periods = [
        ('year', 60*60*24*365),
        ('month', 60*60*24*30),
        ('day', 60*60*24),
        ('hour', 60*60),
        ('minute', 60),
        ('second', 1)
    ]
    strings = []
    for period_name, period_seconds in periods:
        if seconds > period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            has_s = 's' if period_value > 1 else ''
            appendage = "%s %s%s" % (period_value, period_name, has_s)
            strings += [appendage]
        if period_name == precision:
            break

    if not strings:
        return "less than a {}".format(precision)

    return ", ".join(strings)
