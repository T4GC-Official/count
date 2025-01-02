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
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from telegram.ext import CallbackQueryHandler

# Load all env vars from chatbot's .env - this file is not tracked by
# git but created by the caller of this script and contains the API_KEY
# environment variable.
load_dotenv()

logger = logging.getLogger(__name__)


async def _start(update: Update, context: CallbackContext) -> None:
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


async def start(update: Update, context: CallbackContext) -> None:
    """Handles the /start command and displays the main category buttons."""
    if update.callback_query:
        message = update.callback_query.message
    elif update.message:
        message = update.message
    else:
        logging.error("Both update.message and update.callback_query are None")
        return

    keyboard = [
        [InlineKeyboardButton("Food 🥘", callback_data="category:food")],
        [InlineKeyboardButton("Household Items 🏠",
                              callback_data="category:household")],
        [InlineKeyboardButton("Fuel ⛽", callback_data="category:fuel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text("Choose a category:", reply_markup=reply_markup)


async def handle_button(update: Update, context: CallbackContext) -> None:
    """Handles button presses and displays subcategories for further options."""
    query = update.callback_query
    await query.answer()

    data = query.data.split(":")
    if data[0] == "category":
        category = data[1]
        if category == "food":
            keyboard = [
                [InlineKeyboardButton(
                    "Vegetables 🥔🍅", callback_data="subcategory:food:vegetables")],
                [InlineKeyboardButton(
                    "Fruits 🍌🍉", callback_data="subcategory:food:fruits")],
                [InlineKeyboardButton(
                    "Meats 🍗🥚", callback_data="subcategory:food:meats")],
                [InlineKeyboardButton(
                    "Rice 🍚", callback_data="subcategory:food:rice")],
                [InlineKeyboardButton(
                    "Dairy Products 🐮🥛", callback_data="subcategory:food:dairy")]
            ]
        elif category == "household":
            keyboard = [
                [InlineKeyboardButton(
                    "Soap 🧼", callback_data="subcategory:household:soap")],
                [InlineKeyboardButton(
                    "Clothes 👚👖", callback_data="subcategory:household:clothes")],
                [InlineKeyboardButton(
                    "Stationary 📚📝", callback_data="subcategory:household:stationary")],
                [InlineKeyboardButton(
                    "Cosmetics 💄", callback_data="subcategory:household:cosmetics")]
            ]
        elif category == "fuel":
            keyboard = [
                [InlineKeyboardButton(
                    "Petrol ⛽", callback_data="subcategory:fuel:petrol")],
                [InlineKeyboardButton(
                    "Gas ⛽", callback_data="subcategory:fuel:gas")],
                [InlineKeyboardButton(
                    "Diesel", callback_data="subcategory:fuel:diesel")]
            ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(f"Choose a subcategory under {category.title()}:", reply_markup=reply_markup)
    elif data[0] == "subcategory":
        category, subcategory = data[1], data[2]
        keyboard = [
            [InlineKeyboardButton("Produced within the village",
                                  callback_data=f"source:{category}:{subcategory}:within")],
            [InlineKeyboardButton("Produced outside the village",
                                  callback_data=f"source:{category}:{subcategory}:outside")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(f"Where was this {subcategory} produced?", reply_markup=reply_markup)

    elif data[0] == "source":
        category, subcategory, source = data[1], data[2], data[3]

        # Store some key details for later use
        context.user_data["category"] = category
        context.user_data["subcategory"] = subcategory
        context.user_data["source"] = source

        keyboard = [
            [InlineKeyboardButton("0-50", callback_data="price:0-50"),
             InlineKeyboardButton("50-100", callback_data="price:50-100"),
             InlineKeyboardButton("100-200", callback_data="price:100-200")],
            [InlineKeyboardButton("Custom", callback_data="price:custom")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"You selected: {category.title()} > {subcategory.title()} > {source.title()}.\n\nPlease select a price:",
            reply_markup=reply_markup
        )
        return

    elif data[0] == "price":
        price_range = data[1]

        if price_range == "custom":
            await query.message.reply_text(
                "Enter your price:",
                reply_markup=ForceReply(selective=True)
            )

            context.user_data["state"] = "awaiting_custom_price"
            return
        else:
            context.user_data["price"] = price_range
            await query.edit_message_text(f"Price selected: {price_range}")
            await start(update, context)
            return


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
        default="INFO",
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
    # Handles inline button presses
    app.add_handler(CallbackQueryHandler(handle_button))

    app.run_polling()


if __name__ == '__main__':
    main()
