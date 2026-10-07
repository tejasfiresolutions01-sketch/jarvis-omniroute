import unittest
from tools.briefing_tools import generate_executive_briefing
from tools.weather_tools import get_weather

class TestWeatherBriefing(unittest.TestCase):
    def test_weather_retrieval(self):
        w = get_weather("London")
        self.assertIsInstance(w, str)
        self.assertTrue(len(w) > 5)

    def test_executive_briefing_protocol_sunrise(self):
        briefing = generate_executive_briefing()
        self.assertIn("Protocol Sunrise", briefing)
        self.assertIn("TELEMETRY", briefing)
        self.assertIn("AGENDA", briefing)

if __name__ == "__main__":
    unittest.main()
