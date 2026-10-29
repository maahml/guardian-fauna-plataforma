import unittest
from datetime import date, time

from streamlit_ui.time_utils import event_time_to_utc


class EventTimeTests(unittest.TestCase):
    def test_sao_paulo_occurrence_time_is_serialized_as_utc(self):
        result = event_time_to_utc(date(2026, 10, 28), time(19, 15, 30))
        self.assertEqual(result, "2026-10-28T22:15:30.000000Z")

    def test_invalid_time_values_are_rejected(self):
        with self.assertRaises(ValueError):
            event_time_to_utc(None, time(19, 15))


if __name__ == "__main__":
    unittest.main()
