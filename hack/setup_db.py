import common

from store.db import MongoManager, TelegramStore
from pymongo import ASCENDING
from pymongo.collection import Collection


def print_indices(collection: Collection):
    print(f"Listing indices in {TelegramStore.update_table_name}: ") 
    print([idx for idx in collection.index_information()])


db = MongoManager.client[TelegramStore.db_name]
collection = db[TelegramStore.update_table_name]
index_key = [("user_id", ASCENDING)]
print_indices(collection)
collection.create_index(index_key)
print_indices(collection)
