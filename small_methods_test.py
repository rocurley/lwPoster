import unittest
import datetime
import apis


class TestNextWeekday(unittest.TestCase):

    def test_monday_tuesday(self):
        monday_noon = datetime.datetime(2023, 5, 1, 12, 0, 0) # May 1 2023 is a Monday
        target_number = 1 # Tuesday
        tuesday_noon = datetime.datetime(2023, 5, 2, 12, 0, 0) # 24 hours later exactly
        self.assertEqual(apis.next_weekday(monday_noon, target_number), tuesday_noon)
        print("correct weekday")

    def test_tuesday_monday(self):
        tuesday_noon = datetime.datetime(2023, 5, 2, 12, 0, 0) #May 2 2023 is a Tuesday
        next_monday_noon = datetime.datetime(2023, 5, 8, 12, 0, 0) # 6*24 hours later exactly
        target_number = 0 # Monday
        self.assertEqual(apis.next_weekday(tuesday_noon, target_number), next_monday_noon)
        print("correct weekday in next week")

    def test_tuesday_saturday(self):
        tuesday_noon = datetime.datetime(2023, 5, 2, 12, 0, 0) #May 2 2023 is a Tuesday
        next_saturday_noon = datetime.datetime(2023, 5, 6, 12, 0, 0) # 4*24 hours later exactly
        target_number = 5 # Monday
        self.assertEqual(apis.next_weekday(tuesday_noon, target_number), next_saturday_noon)
        print("correct weekday late in week")

if __name__ == '__main__':
    unittest.main()
