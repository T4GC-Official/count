"""Organic Mandya (OM) Telegram bot implementation.

Usage: 
    To start this chatbot, run the following command from the root directory of this repo:

    ./chatbot.py --plugin om

Notes:
    1. To run the chatbot you need a file named ".env" in the root directory of this repo.
    This file is NOT included in git, you need to create it with your API_KEY:
        API_KEY=<your api key>

    2. To run the chatbot through docker you can then issue:
        docker build -t t4g-om-chatbot:0.1 .
        docker run -d t4g-om-chatbot:0.1

       Note that this will copy your API_KEY from your .env file into the container and then run the chatbot.

    3. To run the chatbot outside docker, you need to first
        $ source env/bin/activate
        $ python ./chatbot.py

       This will automatically read your .env file for API_KEY.

    4. See telegram.ext package documentation:
    https://docs.python-telegram-bot.org/en/stable/telegram.ext.html
"""

from summary import create_summary
from constants import START_MSG, LABELS
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, filters
from telegram import Update, ReplyKeyboardMarkup
from pprint import pprint
from .base import BaseBot
from store.db import TelegramStore, MongoManager
import logging


class OMBot(BaseBot):
    def setup_handlers(self):
        self.logger.info("Setting up OM bot handlers...")
        # Initialize MongoDB store
        ts = TelegramStore(
            MongoManager(f"mongodb://{self.host}:{self.port}"),
            bot=self.app.bot,
            bot_name=self.bot_name
        )
        print('Initialized telegram store ', ts)

        # Add handlers
        self.app.add_handler(CommandHandler("start", start))
        self.app.add_handler(MessageHandler(
            filters.StatusUpdate.NEW_CHAT_MEMBERS, start))
        self.app.add_handler(MessageHandler(filters.TEXT, handle_updates))
        self.app.add_handler(MessageHandler(filters.LOCATION, handle_updates))
        self.app.add_handler(MessageHandler(filters.PHOTO, handle_pic))


def run_bot(**kwargs):
    bot = OMBot(**kwargs)
    bot.run()


async def start(update: Update, context: CallbackContext) -> None:
    """Handles what happens on /start. 

    Args: 
        update: The update from the telegram bot framework. 
        context: The callback context passed in by the telegram bot framework. 
            This arg is unused. 

    Returns: 
        None: The return value is ignored by the telegram bot framework. 
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Start command received from user {update.effective_user.id}")
    keyboard = [
        [LABELS["c1"], LABELS["c2"]],
        [LABELS["c3"], LABELS["c4"]],
        [LABELS["c5"], LABELS["other"]],
        [LABELS["cost"]],
        [LABELS["summary"]]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(START_MSG, reply_markup=reply_markup)


async def handle_updates(update: Update, context: CallbackContext) -> None:
    """Manages updates from the telegram bot.

    Every other handler internally calls handle_update to insert the update into the db. 

    Args: 
        update: The update from the telegram bot framework. 
        context: The callback context passed in by the telegram bot framework. 
            This arg is unused.

    Returns: 
        None: The return value is ignored by the telegram bot framework. 
    """
    logger = logging.getLogger(__name__)
    logger.debug(f"Received message: {update.message.text}")
    pprint(update.to_dict())

    # Lipok state management. This state was set in the last inline keyboard
    # button and is handled here because the custom price is captured through a
    # force reply keyboard.
    if context.user_data.get("state") == "awaiting_custom_price":
        price = update.message.text
        if price.isdigit():
            context.user_data["price"] = int(price)
            context.user_data.pop("state")
            await update.message.reply_text(f"Custom price entered: {price}")

            logging.info(f"Collected data: {context.user_data}")

            await update.message.reply_text(
                "Thank you! returning to main menu..")
            await start(update, context)
        else:
            await update.message.reply_text(
                "Please enter a valid integer price.")
        return

    ts = TelegramStore()
    if update.message and update.message.text == LABELS["picture"]:
        await update.message.reply_text("Upload a picture by pressing 📎")

    if update.message and update.message.text == LABELS["summary"]:
        logging.info(
            f"Getting updates for user {update.message.from_user.name} with id {update.message.from_user.id}")
        user_updates = ts.get_updates(
            filter={"message.from.id": update.message.from_user.id})

        # TODO(prashanth@): if this fails, send a reply_text asking the
        # user to retry.
        await update.message.reply_document(
            document=create_summary(updates=user_updates, metadata=[]),
            filename="summary.pdf")

    ts.insert_update(update)


async def handle_pic(update: Update, context: CallbackContext) -> None:
    """Handles messages with attached pictures.

    NB: this is not the handler for the pic button. On hitting the pic button the user is sent to the generic text message handler (handle_updates). This is the handler for photo messages.  

    Args:
        update: The update from the telegram bot framework.
        context: The callback context passed in by the telegram bot framework.
            This arg is unused.

    Returns:
        None: The return value is ignored by the telegram bot framework.
    """
    if update.message.photo is None:
        await update.message.reply_text('No photo found for update' + update)
        return None

    await handle_updates(update, context)

    # TODO(prashanth@): handle multiple photo uploads
    # photo_id = update.message.photo[-1].file_id
    # pic = await update.message.photo[-1].get_file()
    # pic.download_to_drive(f'{pic.file_path}')
    await update.message.reply_text(
        "Your summary will be updated if the photo is a receipt.")
