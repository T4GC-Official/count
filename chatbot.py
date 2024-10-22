"""This script handles Telegram bot commands.

Usage: 
    ./chatbot.py

Notes:
    1. To run the chatbot you need a file named ".env" in the cwd. 
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

import argparse
import os
import logging
from pprint import pprint
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler, filters
from store.db import TelegramStore, MongoManager
from constants import START_MSG, LABELS
from summary import create_summary
from bson import json_util
from dotenv import load_dotenv

# Load all env vars from chatbot's .env - this file is not tracked by
# git but created by the caller of this script and contains the API_KEY
# environment variable.
load_dotenv()

logger = logging.getLogger(__name__)


async def start(update: Update, context: CallbackContext) -> None:
    """Handles what happens on /start. 

    Args: 
        update: The update from the telegram bot framework. 
        context: The callback context passed in by the telegram bot framework. 
            This arg is unused. 

    Returns: 
        None: The return value is ignored by the telegram bot framework. 
    """
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
    pprint(update.to_dict())
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
            document=create_summary(user_updates),
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


def main():
    api_key = os.getenv('API_KEY', default=None)
    if api_key is None:
        raise ValueError("API_KEY env var is not set.")

    parser = argparse.ArgumentParser(description="Connect to MongoDB")
    parser.add_argument("--host", type=str, default="127.0.0.1",
                        help="The MongoDB host/container name")
    parser.add_argument("--port", type=str, default="27017",
                        help="The MongoDB port")
    parser.add_argument("--bot_name", type=str, default="ari",
                        help="User supplied chatbot name. If unspecified the name is pulled from the name associated with the API key. ")
    parser.add_argument(
        "--log-level",
        default="DEBUG",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level"
    )

    # Parse the arguments
    args = parser.parse_args()

    # Set the global log level
    logging.getLogger().setLevel(args.log_level)

    # Initialize a refrence to the bot
    app = Application.builder().token(api_key).build()
    logging.info("Starting chatbot " + args.bot_name)

    # Set the global telegram store before adding command handlers.
    ts = TelegramStore(
        MongoManager(f"mongodb://{args.host}:{args.port}"),
        bot=app.bot,
        bot_name=args.bot_name)
    logger.debug(f"Bootstrapped telegram store: {ts.get_updates(limit=1)}")

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS, start))

    app.add_handler(MessageHandler(filters.TEXT, handle_updates))
    app.add_handler(MessageHandler(filters.LOCATION, handle_updates))
    app.add_handler(MessageHandler(filters.PHOTO, handle_pic))

    app.run_polling()


if __name__ == '__main__':
    main()
