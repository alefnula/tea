from typing import Optional
from datetime import datetime, date

import pytz
import tzlocal


TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M:%S"
HOURS = 60 * 60
MINUTES = 60


# Reuse so I don't need to import pytz too
utc = pytz.utc


def now():
    """Return an aware datetime.datetime now."""
    # timeit shows that datetime.now(tz=utc) is 24% slower
    return datetime.utcnow().replace(tzinfo=utc)


def is_aware(value):
    """Determine if a given datetime.datetime is aware.

    The concept is defined in Python's docs:
    https://docs.python.org/library/datetime.html#datetime.tzinfo

    Assuming value.tzinfo is either None or a proper datetime.tzinfo,
    value.utcoffset() implements the appropriate logic.
    """
    return value.utcoffset() is not None


def is_naive(value):
    """Determine if a given datetime.datetime is naive.

    The concept is defined in Python's docs:
    https://docs.python.org/library/datetime.html#datetime.tzinfo

    Assuming value.tzinfo is either None or a proper datetime.tzinfo,
    value.utcoffset() implements the appropriate logic.
    """
    return value.utcoffset() is None


def make_aware(value, timezone=None, is_dst=None):
    """Make a naive datetime.datetime in a given time zone aware."""
    if timezone is None:
        timezone = tzlocal.get_localzone()
    if hasattr(timezone, "localize"):
        # This method is available for pytz time zones.
        return timezone.localize(value, is_dst=is_dst)
    else:
        # Check that we won't overwrite the timezone of an aware datetime.
        if is_aware(value):
            raise ValueError(
                "make_aware expects a naive datetime, got %s" % value
            )
        # This may be wrong around DST changes!
        return value.replace(tzinfo=timezone)


def localtime(value=None, timezone=None):
    """
    Convert an aware datetime.datetime to local time.

    Only aware datetimes are allowed. When value is omitted, it defaults to
    now().

    Local time is defined by the current time zone, unless another time zone
    is specified.
    """
    if value is None:
        value = now()
    if timezone is None:
        timezone = tzlocal.get_localzone()
    # Emulate the behavior of astimezone() on Python < 3.6.
    if is_naive(value):
        raise ValueError("localtime() cannot be applied to a naive datetime")
    return value.astimezone(timezone)


def date_to_str(d: Optional[date]) -> Optional[str]:
    """Convert date to string."""
    if d is None:
        return None

    return d.strftime(DATE_FORMAT)


def date_to_datetime(d: Optional[date]) -> Optional[datetime]:
    """Convert a date to timezone aware datatetime."""
    if d is None:
        return None

    return make_aware(datetime.combine(d, datetime.min.time()))


def to_utc_str(dt: Optional[datetime]) -> Optional[str]:
    """Convert datetime to utc string."""
    if dt is None:
        return None

    if isinstance(dt, date):
        return dt.strftime(TIMESTAMP_FORMAT)

    if not is_aware(dt):
        dt = make_aware(dt, timezone=utc)
    return localtime(dt, timezone=utc).strftime(TIMESTAMP_FORMAT)


def to_localtime_str(dt: Optional[datetime]) -> Optional[str]:
    """Convert datetime to local time aware string."""
    if dt is None:
        return None

    if not is_aware(dt):
        dt = make_aware(dt, timezone=utc)
    return localtime(dt).strftime(TIME_FORMAT)


def from_utc_str(s: Optional[str]) -> Optional[datetime]:
    """Convert string to timezone aware datetime."""
    if s is None:
        return None
    return make_aware(datetime.strptime(s, TIMESTAMP_FORMAT), timezone=utc)


def humanize(duration: int) -> str:
    """Convert duration in seconds to human readable representation.

    Args:
        duration (int): Duration in seconds.
    """
    hours = duration // HOURS

    result = []
    if hours > 0:
        result.append(f"{hours}h")
        duration = duration - (HOURS * hours)

    minutes = duration // MINUTES
    if minutes > 0 or hours > 0:
        result.append(f"{minutes:02d}m")
        duration = duration - (MINUTES * minutes)

    result.append(f"{duration:02d}s")
    return " ".join(result)
