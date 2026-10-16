"""Calendar periods are deterministic and respect the user's date boundary."""
from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
from accounts import BridgeError
from mail_dates import resolve_range


class CalendarTests(unittest.TestCase):
    def test_since_month_includes_local_midnight(self):
        value = resolve_range(after="2026-10-01", time_zone="+09:00")
        self.assertEqual(value["after"], "2026-09-30T15:00:00+00:00")
        self.assertIsNone(value["before"])

    def test_this_week_uses_local_date_and_monday(self):
        # Sunday UTC is already Monday in Korea.
        now = datetime(2026, 10, 11, 15, 30, tzinfo=timezone.utc)
        value = resolve_range(period="this_week", time_zone="+09:00", now=now)
        self.assertEqual(value["after"], "2026-10-11T15:00:00+00:00")
        self.assertEqual(value["before"], "2026-10-18T15:00:00+00:00")
        previous = resolve_range(period="last_week", time_zone="+09:00", now=now)
        self.assertEqual(previous["before"], value["after"])
        self.assertEqual(previous["after"], "2026-10-04T15:00:00+00:00")

    def test_month_year_and_leap_boundaries(self):
        for now, period, start, end in [
            ("2027-01-01", "last_month", "2026-12-01", "2027-01-01"),
            ("2026-12-16", "this_month", "2026-12-01", "2027-01-01"),
            ("2024-03-01", "last_month", "2024-02-01", "2024-03-01"),
        ]:
            value = resolve_range(period=period, now=datetime.fromisoformat(now).replace(tzinfo=timezone.utc))
            self.assertEqual(value["after"], start + "T00:00:00+00:00")
            self.assertEqual(value["before"], end + "T00:00:00+00:00")

    def test_negative_offset_and_exclusive_end(self):
        value = resolve_range("2026-10-01", "2026-11-01", time_zone="-05:30")
        self.assertEqual(value["after"], "2026-10-01T05:30:00+00:00")
        self.assertEqual(value["before"], "2026-11-01T05:30:00+00:00")

    def test_invalid_or_conflicting_ranges_fail_closed(self):
        for arguments in ({"after": "2026-02-31"}, {"after": "2026-1-1"},
                          {"after": "2026-10-02", "before": "2026-10-01"},
                          {"after": "2026-10-01", "period": "this_week"},
                          {"period": "unknown"}, {"time_zone": "+14:01"},
                          {"time_zone": "+09:60"}, {"time_zone": "invalid-zone"}):
            with self.subTest(arguments=arguments), self.assertRaises(BridgeError):
                resolve_range(**arguments)


if __name__ == "__main__":
    unittest.main()
