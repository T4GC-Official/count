import unittest
from telegram import Update, Message, User, Chat
from summary import create_summary, Summary
from datetime import datetime
from constants import INDIA_TZ, LABELS
from pytz import timezone

TEST_USER_ID = 123456
TEST_USER_NAME = "TestUser"


class TestCase:
    def __init__(self, update_messages, assertions):
        self.update_messages = update_messages
        self.assertions = assertions


class TestSummary(unittest.IsolatedAsyncioTestCase):

    def _update(self, msg="/start", user_id=TEST_USER_ID):
        date = datetime.fromtimestamp(
                int(datetime.now(timezone(INDIA_TZ)).timestamp()))
        u = User(id=user_id, first_name=TEST_USER_NAME, is_bot=False)
        return Update(
            update_id=1,
            message=Message(
                message_id=1,
                date=date,
                chat=Chat(id=123456, type="private"),
                text=msg,
                from_user=u,
            ),
        )
    async def test_generate_summary(self):
        test_cases = [
            TestCase(
                update_messages=[
                    LABELS["start"],
                    LABELS["c1"],
                    LABELS["cost"],
                    "20",
                    LABELS["c5"],
                    LABELS["cost"],
                    "100",
                    LABELS["summary"],
                ],
                assertions=[
                    lambda summary: summary[LABELS["c1"]] == 20,
                    lambda summary: summary[LABELS["c5"]] == 100,
                ]
            ),
            # With descriptions 
            TestCase(
                update_messages=[
                    LABELS["start"],
                    LABELS["c5"],
                    "Shrugs",
                    "10",
                    LABELS["c1"],
                    "100",
                    LABELS["summary"],
                ],
                assertions=[
                    lambda summary: summary[LABELS["c1"]] == 100,
                    lambda summary: summary[LABELS["c5"]] == 10,
                ]
            ),
            # Multiple Categories - last one wins 
            TestCase(
                update_messages=[
                    LABELS["start"],
                    LABELS["c5"],
                    LABELS["c1"],
                    "Shrugs",
                    "10",
                    LABELS["summary"],
                ],
                assertions=[
                    lambda summary: summary[LABELS["c1"]] == 10,
                ]
            ),
            # TODO(prashanth@): test start/end date. 

        ]

        for test_case in test_cases:
            update_objects = []
            for um in test_case.update_messages:
                update_objects.append(self._update(um))
            summary_bytes = create_summary(update_objects)
            json_summary = Summary.to_json(summary_bytes)
            for assertion in test_case.assertions:
                assert assertion(json_summary)


if __name__ == '__main__':
    unittest.main()
