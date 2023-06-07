import unittest
import datetime
import apis
import json


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

class TestNextMeetup(unittest.TestCase):

    def test_monday_to_tuesday(self):
        monday_noon = datetime.datetime(2023, 5, 1, 12, 0, 0) # May 1 2023 is a Monday
        tuesday = datetime.date(2023, 5, 2)
        self.assertEqual(apis.next_meetup_date_testable({"weekday_number": 1}, monday_noon), tuesday)
        print("correct day")

    def test_tuesday_to_monday(self):
        tuesday_noon = datetime.datetime(2023, 5, 2, 12, 0, 0) # May 2 2023 is a Tuesday
        next_monday = datetime.date(2023, 5, 8)
        self.assertEqual(
            apis.next_meetup_date_testable({"weekday_number": 0}, tuesday_noon),
            next_monday
        )
        print("correct day in next week")

    def test_tuesday_to_saturday(self):
        tuesday_noon = datetime.datetime(2023, 5, 2, 12, 0, 0) # May 2 2023 is a Tuesday
        saturday = datetime.date(2023, 5, 6)
        self.assertEqual(
            apis.next_meetup_date_testable({"weekday_number": 5}, tuesday_noon),
            saturday
        )
        print("correct day later in week")

    def test_tuesday_evening_to_next_tuesday(self):
        tuesday_night = datetime.datetime(2023, 5, 2, 20, 1, 0) # May 2 2023 is a Tuesday
        next_tuesday = datetime.date(2023, 5, 9)
        self.assertEqual(
            apis.next_meetup_date_testable({"weekday_number": 1}, tuesday_night),
            next_tuesday
        )
        print("correct day in next week")

    def test_tuesday_morning_to_tuesday_evening(self):
        tuesday_noon = datetime.datetime(2023, 5, 2, 10, 0, 0) # May 2 2023 is a Tuesday
        this_tuesday = datetime.date(2023, 5, 2)
        self.assertEqual(
            apis.next_meetup_date_testable({"weekday_number": 1}, tuesday_noon),
            this_tuesday
        )

class TestLWFormatting(unittest.TestCase):

    test_config = {
        "phone": "555 123 4567",
        "location":
        {
            "instructions": "Buzz for H. Celine or enter code 893",
            "phone": "555 987 6543"
        },
        "meetup_name": "LW For Dummy",
        "boilerplate_path": "test_boilerplate"
    }

    def test_gen_title(self):
        self.assertEqual(
            apis.lw2_title("reading", self.test_config),
            "LW For Dummy: Reading & Discussion"
        )

    def test_gen_body(self):
        expected_boilerplate = """
Buzz for H. Celine or enter code 893
Entrance call: 555 987 6543 (general meetup info at 555 123 4567).
Format: Doors 6:15, Topic Start: 6:45
About: Some structure.
"""
        self.assertEqual(
            apis.lw2_body("test_topic", self.test_config),
            "This is a test topic.\n"+expected_boilerplate
        )

    def test_gen_real_body(self):
        # Make this more like a real config
        config = json.loads(json.dumps(self.test_config))
        del config["boilerplate_path"]
        del config["location"]["phone"]
        config["phone"] = "${phone}"

        with open("meetups/body/reading") as f:
            topic_text = f.read()
        with open("boilerplate") as f:
            boilerplate = f.read()
        expected = topic_text+"\n"+config["location"]["instructions"]+"\n"+boilerplate
        self.maxDiff = None
        self.assertEqual(apis.lw2_body("reading", config), expected)

if __name__ == '__main__':
    unittest.main()
