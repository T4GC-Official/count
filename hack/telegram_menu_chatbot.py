from telegram_menu import BaseMessage, TelegramMenuSession, NavigationHandler, MenuButton, ButtonType

from telegram import Update
from telegram.ext._callbackcontext import CallbackContext
from telegram.ext._utils.types import BD, BT, CD, UD
from telegram.ext._application import DEFAULT_GROUP
from telegram.ext import MessageHandler
from telegram.ext.filters import TEXT
from pathlib import Path
from os import path


API_KEY = "7447994267:AAE93orftBiqYP1BXyEoCvYV8quuh9aDFPA";

class StartMessage(BaseMessage):
    """Start menu, create all app sub-menus."""

    LABEL = "start" 


    def __init__(self, navigation: NavigationHandler) -> None:
        """Init StartMessage class."""
        super().__init__(navigation, StartMessage.LABEL)
        
        self.add_button(
            label="What did you buy?", 
            callback=MenuMessage(navigation)
            )
        
        self.add_button(
            label="How much did it cost?",
            callback=MenuMessage(navigation)
        )

        self.add_button(
            label="Summary",
            callback=MenuMessage(navigation)
        )

    # def update(self) -> str:
    #     """Update message content."""
    #     return "Hello, world!"


class MenuMessage(BaseMessage):
    """Second menu, create an inlined button."""

    LABEL = "action"


    def __init__(self, navigation: NavigationHandler) -> None: 
        """Init SecondMenuMessage class."""
        super().__init__(navigation, StartMessage.LABEL, inlined=True)

        # 'run_and_notify' function executes an action and return a string as Telegram notification.
        # self.add_button(label="Action", callback=self.run_and_notify)

        # self.add_button(
        #         label="Display content", 
        #         callback=self.get_content, 
        #         btype=ButtonType.MESSAGE)

        self.add_button(
            label="Show picture", 
            callback=self.get_picture, 
            btype=ButtonType.PICTURE, 
            new_row=True
            )

        self.add_button(
            label="Show sticker", callback=self.get_sticker, btype=ButtonType.STICKER
        )


    def get_sticker(self) -> str:
        return "https://raw.githubusercontent.com/mevellea/telegram_menu/master/resources/stats_default.webp"
    

    def get_picture(self) -> str:
        root = Path(__file__).parent
        return path.join(root, "images", "food.jpg")


    def get_content(self):
        """Returns text content to display with markdown formatting."""
        return "## This is get_content"
    

    def update(self) -> str: 
        """Update message content."""
        return ":warning: second message"


    @staticmethod
    def run_and_notify() -> str: 
        """Update message content."""
        return "This is a notification"

async def echo(update: Update, context: CallbackContext[BT, UD, CD, BD]) -> None:
    await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)


import pudb; pudb.set_trace()
tms = TelegramMenuSession(API_KEY, msg_handler=echo)
# Add our handler after the default button handler. 
tms.application.add_handler(handler=MessageHandler(TEXT, echo), group=DEFAULT_GROUP+1)
tms.start(StartMessage)
