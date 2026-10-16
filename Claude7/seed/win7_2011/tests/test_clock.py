import unittest
from datetime import datetime

from win7_2011.win7sim.clock import format_locked_date, format_locked_time


class LockedClockTests(unittest.TestCase):
    def test_date_uses_live_parts_but_fixed_year(self) -> None:
        now = datetime(2026, 10, 11, 21, 7)
        self.assertEqual(format_locked_date(now), "Sunday, October 11, 2011")

    def test_time_uses_live_local_time_in_12_hour_format(self) -> None:
        self.assertEqual(format_locked_time(datetime(2026, 10, 11, 21, 7)), "9:07 PM")
        self.assertEqual(format_locked_time(datetime(2026, 10, 11, 9, 7)), "9:07 AM")


if __name__ == "__main__":
    unittest.main()
