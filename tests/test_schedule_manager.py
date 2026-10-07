import unittest
from datetime import date, timedelta
from core.schedule_manager import ButlerScheduleManager

class TestScheduleManager(unittest.TestCase):
    def setUp(self):
        # Use a fresh in-memory database for each test to isolate tests and avoid Windows file locks
        self.mgr = ButlerScheduleManager(db_path=":memory:")

    def test_add_and_get_events(self):
        today = date.today().strftime("%Y-%m-%d")
        ev = self.mgr.add_event(
            title="Meeting with Tony Stark",
            event_date=today,
            event_time="15:00",
            priority="high"
        )
        self.assertEqual(ev["title"], "Meeting with Tony Stark")

        events = self.mgr.get_events_for_date(today)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["title"], "Meeting with Tony Stark")

    def test_natural_language_add_tomorrow(self):
        is_handled, res = self.mgr.parse_and_handle("schedule meeting with Bruce Wayne at 4pm tomorrow")
        self.assertTrue(is_handled)
        self.assertIn("Bruce Wayne", res)

        tmrw = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        events = self.mgr.get_events_for_date(tmrw)
        self.assertEqual(len(events), 1)
        self.assertIn("Bruce Wayne", events[0]["title"])
        self.assertEqual(events[0]["event_time"], "16:00")

    def test_daily_briefing(self):
        today = date.today().strftime("%Y-%m-%d")
        self.mgr.add_event("Stark Labs Review", today, "10:00")
        is_handled, briefing = self.mgr.parse_and_handle("daily briefing")
        self.assertTrue(is_handled)
        self.assertIn("Stark Labs Review", briefing)

    def test_cancel_event(self):
        today = date.today().strftime("%Y-%m-%d")
        self.mgr.add_event("Dentist appointment", today, "11:00")
        is_handled, cancel_msg = self.mgr.parse_and_handle("cancel appointment Dentist")
        self.assertTrue(is_handled)
        self.assertIn("Cancelled", cancel_msg)

        events = self.mgr.get_events_for_date(today)
        self.assertEqual(len(events), 0)

if __name__ == "__main__":
    unittest.main()
