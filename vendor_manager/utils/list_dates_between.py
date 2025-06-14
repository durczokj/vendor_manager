"""Utility function to generate a list of dates between two datetime instances."""

from datetime import timedelta


def list_dates_between(start_date, end_date):
    """Generate a list of dates between two datetime instances.

    :param start_date: The start date as a datetime instance.
    :param end_date: The end date as a datetime instance.
    :return: A list of dates between start_date and end_date.
    """
    if start_date > end_date:
        raise ValueError("start_date must be before end_date")

    delta = end_date - start_date
    return [start_date + timedelta(days=i) for i in range(delta.days + 1)]
