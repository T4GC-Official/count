"""Base class for Telegram bot plugins."""

from abc import ABC, abstractmethod
from telegram.ext import Application
import logging


class BaseBot(ABC):
    def __init__(self, api_key, host, port, bot_name, **kwargs):
        self.api_key = api_key
        self.host = host
        self.port = port
        self.bot_name = bot_name
        self.app = Application.builder().token(api_key).build()
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def setup_handlers(self):
        """Setup bot-specific command handlers"""
        pass

    def run(self):
        """Start the bot"""
        self.logger.info(f"Starting {self.__class__.__name__} bot...")
        self.setup_handlers()
        self.app.run_polling()
