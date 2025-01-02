"""Lipok Telegram bot implementation.

Usage: 
    To start this chatbot, run the following command from the root directory of this repo:

    ./chatbot.py --plugin lipok

Notes:
    1. To run the chatbot you need a file named ".env" in the root directory of this repo.
    This file is NOT included in git, you need to create it with your API_KEY:
        API_KEY=<your api key>

    2. To run the chatbot through docker you can then issue:
        docker build -t t4g-lipok-chatbot:0.1 .
        docker run -d t4g-lipok-chatbot:0.1

       Note that this will copy your API_KEY from your .env file into the container and then run the chatbot.

    3. To run the chatbot outside docker, you need to first
        $ source env/bin/activate
        $ python ./chatbot.py

       This will automatically read your .env file for API_KEY.

    4. See telegram.ext package documentation:
    https://docs.python-telegram-bot.org/en/stable/telegram.ext.html
"""

from telegram.ext import CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from store.db import TelegramStore, MongoManager
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, filters
from telegram import Update
import logging
from .base import BaseBot


class LipokBot(BaseBot):
    def setup_handlers(self):
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
        # Handles inline button presses
        self.app.add_handler(CallbackQueryHandler(handle_button))
        # Add new handler for custom price input
        self.app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, handle_custom_price))


def run_bot(**kwargs):
    bot = LipokBot(**kwargs)
    bot.run()


async def start(update: Update, context: CallbackContext) -> None:
    """Handles the /start command and displays the main category buttons."""
    logger = logging.getLogger(__name__)
    logger.info(f"Start command received from user {update.effective_user.id}")
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
    logger = logging.getLogger(__name__)
    logger.info(f"Button pressed: {update.callback_query.data}")
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


async def handle_custom_price(update: Update, context: CallbackContext) -> None:
    """Handles custom price input from user."""
    if context.user_data.get("state") != "awaiting_custom_price":
        return

    price = update.message.text
    context.user_data["price"] = price
    context.user_data.pop("state")  # Clear the awaiting state

    await update.message.reply_text(f"Price set to: {price}")
    await start(update, context)
