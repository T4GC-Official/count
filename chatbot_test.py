import unittest
from unittest.mock import patch, ANY, Mock
from telegram import Update, Message, Chat, User, Bot
from telegram.ext import CallbackContext
from chatbot import start, handle_updates, START_MSG
import mongomock
from pymongo import MongoClient
from store.db import MongoManager, TelegramStore
from summary import Summary
from datetime import datetime
from constants import INDIA_TZ, LABELS
from pytz import timezone

TEST_USER_ID = 123456
TEST_USER_NAME = "TestUser"


class TestChatbot(unittest.IsolatedAsyncioTestCase):

    def _update(self, msg="/start", user_id=TEST_USER_ID):
        date = int(datetime.now(timezone(INDIA_TZ)).timestamp())
        u = User(id=user_id, first_name=TEST_USER_NAME, is_bot=False)
        return Update(
            update_id=1,
            message=Message(
                message_id=1,
                date=date,
                chat=self.chat,
                text=msg,
                from_user=u,
            ),
        )

    async def asyncSetUp(self):
        # Create a fake Update object
        self.user = User(id=123456, first_name="TestUser", is_bot=False)
        self.chat = Chat(id=123456, type="private")
        self.message = Message(
            message_id=1,
            date=None,
            chat=self.chat,
            text="/start",
            from_user=self.user
        )
        self.update = self._update()
        self.client = mongomock.MongoClient()

        # Create a CallbackContext object (can be a mock if not used in the handler)
        self.context = Mock(spec=CallbackContext)
        self.bot = Mock(spec=Bot)
        self.bot.name = "Test"

    @patch.object(Message, 'reply_text', return_value=None)
    async def test_start(self, mock_reply_text):
        await start(self.update, self.context)
        args, _ = mock_reply_text.call_args
        self.assertEqual(args[0], START_MSG)

    async def test_handle_updates(self):
        """Test inserting an update preserves the message.

        This involves a deserialize/serialize cycle. 
        """
        ts = TelegramStore(MongoManager(client=self.client),
                           bot=self.bot, bot_name="test")
        await handle_updates(self.update, self.context)
        update = ts.get_updates()[0].to_dict()
        self.assertEqual(
            update['message'], self.update.to_dict()['message'])


    # Summary related tests
    # Example sequence of messages:
    #
    # msg    state
    # ------------------
    # 0        /start
    #           |
    # 1       category
    #           |_______
    #         /         \
    # 2    string       digit -> uncategorized cost in category
    #         |__________
    #        /           \
    # 3   "Cost"         description
    #        |             |_______________
    #        |             |               \
    # 4    n+1 is digit    n+1 is digit     n+1 is "Cost"
    # 5      |               |              n+2 is digit
    #        |               |              |
    #    uncategorized       categorized cost
    #    cost
    #
    def check_summary(document=None, *args, **kwargs):
        """Side effect function to validate summary report generation."""
        s = Summary.to_json(document)
        assert (s[LABELS["c1"]] == 20)
        assert (s[LABELS["c5"]] == 10)

    @patch.object(Message, 'reply_text', return_value=None)
    @patch.object(Message, 'reply_document', return_value=None, side_effect=check_summary)
    async def test_handle_updates_summary(
            self, mock_reply_document, mock_reply_text):
        """Test that summaries generated from updates are WAI."""

        ts = TelegramStore(MongoManager(client=self.client),
                           bot=self.bot, bot_name="ari")
        update_messages = [
            LABELS["start"],
            LABELS["c1"],
            LABELS["cost"],
            "20",
            LABELS["c5"],
            LABELS["cost"],
            "10",
            LABELS["summary"],
        ]
        for um in update_messages:
            obj = self._update(um)
            await handle_updates(obj, self.context)


if __name__ == '__main__':
    unittest.main()
