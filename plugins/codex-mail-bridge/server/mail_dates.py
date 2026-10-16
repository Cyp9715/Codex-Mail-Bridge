"""Resolve calendar periods locally before either mailbox adapter searches."""
from datetime import datetime, timedelta, timezone
import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from accounts import BridgeError

UTC = timezone.utc
PERIODS = ("this_week", "last_week", "this_month", "last_month")


def current_time():
    return datetime.now(UTC)


def zone(name):
    if name == "UTC":
        return UTC
    if re.fullmatch(r"[+-]\d{2}:\d{2}", name):
        hours, minutes = map(int, name[1:].split(":"))
        if hours > 14 or minutes > 59 or hours == 14 and minutes:
            raise BridgeError("Invalid time_zone offset. Use UTC, an IANA zone, or an offset such as +09:00.")
        return timezone(timedelta(minutes=(hours * 60 + minutes) * (-1 if name[0] == "-" else 1)))
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):
        raise BridgeError("Time zone is unavailable. Use UTC or a fixed offset such as +09:00; IANA zones need local timezone data (tzdata on Windows).") from None


def resolve_range(after=None, before=None, period="", time_zone="UTC", now=None):
    tz = zone(time_zone)
    if period and (after or before):
        raise BridgeError("Use either period or explicit after/before dates, not both.")
    if period:
        if period not in PERIODS:
            raise BridgeError("Unsupported calendar period.")
        today = (now or current_time()).astimezone(tz).date()
        if period.endswith("week"):
            start = today - timedelta(days=today.weekday())
            if period == "last_week":
                start -= timedelta(days=7)
            end = start + timedelta(days=7)
        else:
            start = today.replace(day=1)
            if period == "last_month":
                end = start
                start = (start - timedelta(days=1)).replace(day=1)
            else:
                end = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
        after, before = start.isoformat(), end.isoformat()

    def boundary(value):
        if not value:
            return ""
        try:
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                raise ValueError()
            parsed = datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=tz)
            return parsed.astimezone(UTC).isoformat()
        except (ValueError, OverflowError, OSError):
            raise BridgeError("Dates must be valid YYYY-MM-DD calendar dates in time_zone.") from None

    start, end = boundary(after), boundary(before)
    if start and end and end <= start:
        raise BridgeError("before must be later than after.")
    return {"after": start or None, "before": end or None,
            "time_zone": time_zone, "period": period or None}
