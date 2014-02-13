import re
from datetime import datetime, date, timedelta
from tea.utils import six


_DATE_REGEX = re.compile(
    r'(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})'
    r'(?: (?P<hour>\d{1,2}):(?P<minute>\d{1,2}):(?P<second>\d{1,2})'
    r'(?:\.(?P<microsecond>\d{1,6}))?)?')


def convert_to_datetime(value):
    """
    Converts the given object to a datetime object, if possible.
    If an actual datetime object is passed, it is returned unmodified.
    If the value is a string, it is parsed as a datetime.

    Date strings are accepted in three different forms: date only (Y-m-d),
    date with time (Y-m-d H:M:S) or with date+time with microseconds
    (Y-m-d H:M:S.micro).

    :rtype: datetime
    """
    if isinstance(value, datetime):
        return value
    elif isinstance(value, date):
        return datetime.fromordinal(value.toordinal())
    elif isinstance(value, six.string_types):
        m = _DATE_REGEX.match(value)
        if not m:
            raise ValueError('Invalid date string')
        values = [(k, int(v or 0)) for k, v in m.groupdict().items()]
        values = dict(values)
        return datetime(**values)
    raise TypeError('Unsupported value type: %s' % type(value))


def datetime_ceil(dateval):
    """
    Rounds the given datetime object upwards.

    :type dateval: datetime
    """
    if dateval.microsecond > 0:
        return dateval + timedelta(seconds=1,
                                   microseconds=-dateval.microsecond)
    return dateval
