import common
from pymongo import MongoClient 
from store import db
from pymongo import MongoClient, errors, ASCENDING


MONGO_URI = "mongodb://localhost:27017/"
TEST_DB_NAME = "testdb"
TEST_COLLECTION_NAME = "testcollection"
TELEGRAM_DB_NAME = db.TelegramStore.get_db_name(bot_name="ari")
TELEGRAM_COLLECTION_NAME = db.TelegramStore.update_table_name
INDICES = db.TelegramStore.indices


def check_test_db(client):
    db = client[TEST_DB_NAME]
    collection = db[TEST_COLLECTION_NAME]

    document = { "name": "Sample Item", "value": 456 }
    result = collection.insert_one(document)
    print(f"Inserted document ID: {result.inserted_id}")

    documents = collection.find()
    print(f"Documents in {TEST_DB_NAME}:{TEST_COLLECTION_NAME}:")
    for doc in documents: 
        print(doc)


def check_telegram_db(client):
    db = client[TELEGRAM_DB_NAME]
    collection = db[TELEGRAM_COLLECTION_NAME]
    collection.create_index(INDICES)
    

    documents = collection.find()
    print(f"Documents in {TELEGRAM_DB_NAME}:{TELEGRAM_COLLECTION_NAME}")
    for doc in documents[:10]:
        print(doc)


def main():
    client = MongoClient(MONGO_URI)
    check_test_db(client)
    check_telegram_db(client)


if __name__ == '__main__':
    import pudb; pudb.set_trace()
    main()
