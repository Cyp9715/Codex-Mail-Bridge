"""Validate explicit time bounds; natural-language interpretation belongs to the caller."""
from datetime import datetime, timezone
import re

from accounts import BridgeError

UTC = timezone.utc
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)")


def boundary(value):
    if value is None or value == "":
        return None
    try:
        if DATE.fullmatch(value):
            return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=UTC)
        if not TIMESTAMP.fullmatch(value):
            raise ValueError()
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
    except (ValueError, OverflowError, OSError):
        raise BridgeError("Use YYYY-MM-DD (UTC midnight) or an RFC 3339 timestamp with Z/offset and up to six fractional digits.",
                          code="invalid_date_range", next_action="provide_explicit_time_bounds") from None


def resolve_range(after=None, before=None):
    start, end = boundary(after), boundary(before)
    if start and end and end <= start:
        raise BridgeError("before must be later than after.", code="invalid_date_range",
                          next_action="provide_explicit_time_bounds")
    return {"after": start.isoformat() if start else None,
            "before": end.isoformat() if end else None,
            "bounds": "inclusive_start_exclusive_end"}


def epoch_microseconds(value):
    delta = datetime.fromisoformat(value) - datetime(1970, 1, 1, tzinfo=UTC)
    return (delta.days * 86400 + delta.seconds) * 1_000_000 + delta.microseconds
