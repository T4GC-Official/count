"""This module handles all storage operations for the chatbot. 

Usage: 
    TelegramStore(MongoManager)
    For other usage examples, see hack/. 

Notes: 
    MongoManager: abstracts all the mongo logic.
    TelegramStore: encapsulates all the telegram logic.

Ideally, these would not mix. Meaning, the telegram store would not expose the structure of a specific telegram datastructure to the mongo manager, and the mongo manager would not expose the connection details to the telegram store. That way, the store can use a different backend (eg mariadb) for storing the updates. 

Specifically, the logic of how often and when to retry is embedded in the mongo manager, because this is very write-failure dependent. The mongo client exposes different types of write failures, not all of which are retryable. 
"""

import retry
import logging
from pymongo import MongoClient, errors, ASCENDING
from pymongo.collection import Collection
from pymongo.database import Database
from typing import Any, Dict, List
from abc import ABC, abstractmethod
from telegram import Update, Bot


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DBManager(ABC):
    """Abstract class for all database managers."""

    @abstractmethod
    def insert(
            self, payload: Dict[str, Any], db_name: str, table_name: str) -> None:
        """Insert a payload into the db_name:table_name.

        It is up to the db manager to interpret how to transform keys and values in the given payload. 
        """
        pass

    @abstractmethod
    def find(
            self, filter: dict, db_name: str, table_name: str) -> list[Dict[str, Any]]:
        """Find records matching the given filter in db_name:table_name."""
        pass

    @abstractmethod
    def sync_indices(self, db_name: str, table_name: str, indices: list) -> None:
        """Sync the given list of indices. 

        Create the new ones, delete the stale ones.
        """
        pass


class MongoManager(DBManager):
    """MongoManager has all the logic to deal with the mongo connection."""

    # TODO(prashanth@): is the client thread safe? is that a concern in python3?
    # TODO(prashanth@): if it is thread safe, can we make this a singleton?
    # TODO(prashanth@): retry connection creation on network error.
    def __init__(self, mongo_uri="mongodb://localhost:27017", client=None):
        if client is None:
            self.client = MongoClient(mongo_uri)
        else:
            self.client = client

    @retry.retry(
        (errors.NetworkTimeout, errors.AutoReconnect),
        tries=5,
        delay=2,
        backoff=2
    )
    def insert(self, payload: Dict[str, Any], db_name: str, table_name: str) -> None:
        """insert is a retry wrapper for insert_one. 

        If the collection in question does not exist, mongo will auto create it.
        github.com/mongodb/mongo/blob/r7.0.11/src/mongo/base/error_codes.yml
        """
        # TODO(prashanth@): creating the collection if it doesn't exist will
        # skip index creation. Currently to setup the collection with indices
        # you must run hack/setup_db.py.
        self.client[db_name][table_name].insert_one(payload)

    @retry.retry(
        (errors.NetworkTimeout, errors.AutoReconnect),
        tries=5,
        delay=2,
        backoff=2
    )
    def find(
            self, filter: dict, limit: int, db_name: str, table_name: str) -> list[Dict[str, Any]]:
        return [u for u in
                self.client[db_name][table_name].find(filter).limit(limit)]

    def _delete_all(self, db_name: str, table_name: str) -> None:
        """_delete_all deletes an entire collection.

        This is only used in testing. For product use `delete`.
        """
        self.client[db_name][table_name].delete_many({})

    def _drop_database(self, db_name: str) -> None:
        """_drop_table deletes the entire table."""
        self.client.drop_database(db_name)

    def sync_indices(self, db_name: str, table_name: str, indices: list) -> None:
        """create_index creates all indices in the indices list"""
        self.client[db_name][table_name].create_index(indices)
        # TODO(prashanth@): Delete stale indices


class TelegramStore:
    """TelegramStore understands and stores raw telegram objects.

    This class manages a singleton instances that talks to the database. Every invocation goes through the same instance created in __new__. 
    """
    update_table_name = "updates"
    metadata_table_name = "metadata"
    indices = [("user_id", ASCENDING)]

    # Singleton attributes
    _instance = None
    _db_manager = None

    def __new__(
            cls,
            db_manager: DBManager = None,
            bot: Bot = None,
            bot_name: str = "",
    ):
        """__new__ is python's way of enabling singletons.

        The first invocation of TelegramStore initalizes the singleton with the provided db_manager. Eg: 

        TelegramStore(MongoManager(f"mongodb://localhost:27107"), bot=app.bot)

        Every other invocation can happen without a db manager and just uses the singleton's instance. Eg: 

        TelegramStore().get_all_updates()

        Will return a list of Telegram Update objects. 

        Arguments:
            db_manager: Required on first invocation. A pointer to the db. 

            bot: The bot instance is used to "de json" the dicts returned by 
            mongo into the Update class. 

            The main purpose of the bot object is so that the returned update, 
            which has methods like reply_*, is fully functional. If bot=None, 
            the update will still have the required read-only data, but its 
            telegram api calls won't work. 

            bot_name: A user supplied name used to namespace the db tables for 
            this bot.

        Returns: 
            Must return the _instance created via the super call. 
        """
        if cls._instance is None:
            if db_manager is None:
                raise ValueError("Need a db manager to access the database.")
            cls._instance = super(TelegramStore, cls).__new__(cls)
            cls._instance._initialize(db_manager, bot, bot_name)
        return cls._instance

    def _initialize(self, db_manager: DBManager, bot: Bot, bot_name: str):
        if self._db_manager is None:
            self.db_name = TelegramStore.get_db_name(bot_name)
            self._db_manager = db_manager
            self._bot = bot
            self._db_manager.sync_indices(
                self.db_name, self.update_table_name, self.indices)

    @staticmethod
    def get_db_name(bot_name: str) -> str:
        """get_db_name returns the db name from the bot name. 

        All db names must be lower case.
        """
        return ("%s_%s" % (bot_name, "telegram_bot")).lower()

    def insert_update(self, telegram_update: Update) -> None:
        self._db_manager.insert(
            telegram_update.to_dict(), self.db_name, self.update_table_name)

    def get_updates(self, filter={}, limit=0) -> list[Update]:
        """Returns updates. 

        Args:
            filter: the query filter. 
            limit: if set to a positive integer, limits the returned results.
                if set to 0, returns all results, but pre-fetches them.  
                if set to -1, returns all results, but only fetches them one at a time. 

        Return: 
            All updates under the filter/limit constraint. 
        """
        update_dicts = self._db_manager.find(
            filter, limit, self.db_name, self.update_table_name)
        return [Update.de_json(u, self._bot) for u in update_dicts]

    def insert_metadata(self, metadata: dict) -> None:
        """Insert metadata into the metadata collection.

        Args:
            metadata: The metadata to insert, eg: 
            {
                "update_id": 123,
                "selection_path": "button1:button2",
                "timestamp": datetime.datetime.now(),
                "user_id": 123,
                "user_name": "user1",
                "user_username": "user1",
                "user_language_code": "en",
            }
        """
        self._db_manager.insert(metadata, self.db_name,
                                self.metadata_table_name)

    def get_metadata(self, selection_path_pattern: str, limit: int = 0) -> List[Dict[str, Any]]:
        """Get metadata by selection path pattern.

        Args:
            selection_path_pattern: The selection path pattern to filter by.

        Returns:
            A list of updates that match the selection path pattern.
        """
        return self._db_manager.find(
            {"selection_path": {"$regex": selection_path_pattern}},
            limit=limit,
            db_name=self.db_name,
            table_name=self.metadata_table_name
        )

    def get_updates_by_metadata(self, selection_path_pattern: str) -> List[Update]:
        """Get updates by metadata.

        Args:
            selection_path_pattern: The selection path pattern to filter by.

        Returns:
            A list of updates that match the selection path pattern.
        """
        metadata_docs = self.get_metadata(selection_path_pattern)
        if not metadata_docs:
            return []

        update_ids = [doc["update_id"] for doc in metadata_docs]

        updates = []
        for update_id in update_ids:
            update_dict = self._db_manager.find_one(
                {"update_id": update_id},
                self.db_name,
                self.update_table_name
            )
            if update_dict:
                update = Update.de_json(update_dict, self._bot)
                updates.append(update)

        return updates
