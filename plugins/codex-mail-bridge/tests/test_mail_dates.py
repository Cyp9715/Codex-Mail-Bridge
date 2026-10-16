"""Explicit date bounds are timezone-aware, precise and language-independent."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
from accounts import BridgeError
from mail_dates import epoch_microseconds, resolve_range


class DateBoundTests(unittest.TestCase):
    def test_explicit_offset_normalizes_to_utc(self):
        value = resolve_range(after="2026-10-01T00:00:00+09:00")
        self.assertEqual(value["after"], "2026-09-30T15:00:00+00:00")
        self.assertIsNone(value["before"])

    def test_subday_range_and_equivalent_offsets(self):
        value = resolve_range("2026-10-01T10:30:15-05:30", "2026-10-01T16:00:16Z")
        self.assertEqual(value["after"], "2026-10-01T16:00:15+00:00")
        self.assertEqual(value["before"], "2026-10-01T16:00:16+00:00")
        with self.assertRaises(BridgeError):
            resolve_range("2026-10-01T00:00:00+09:00", "2026-09-30T15:00:00Z")

    def test_legacy_date_only_is_utc_midnight(self):
        value = resolve_range("2026-10-01", "2026-11-01")
        self.assertEqual(value["after"], "2026-10-01T00:00:00+00:00")
        self.assertEqual(value["before"], "2026-11-01T00:00:00+00:00")
        self.assertEqual(value["bounds"], "inclusive_start_exclusive_end")

    def test_fractional_boundaries_do_not_use_float_rounding(self):
        first = resolve_range("2026-10-01T00:00:00.000001Z")["after"]
        base = resolve_range("2026-10-01")["after"]
        self.assertEqual(epoch_microseconds(first) - epoch_microseconds(base), 1)
        last = resolve_range("2026-10-01T00:00:00.999999Z")["after"]
        self.assertEqual(epoch_microseconds(last) - epoch_microseconds(base), 999999)

    def test_invalid_or_ambiguous_bounds_have_machine_error(self):
        for value in ("this week", "2026-02-31", "2026-1-1", "2026-10-01T10:00:00",
                      "2026-10-01T24:00:00Z", "2026-10-01T00:00:00+09:99",
                      "2026-10-01T00:00:00.1234567Z"):
            with self.subTest(value=value), self.assertRaises(BridgeError) as error:
                resolve_range(after=value)
            self.assertEqual(error.exception.code, "invalid_date_range")


if __name__ == "__main__":
    unittest.main()
