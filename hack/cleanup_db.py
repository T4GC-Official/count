import common
from store import db

# Deletes all documents in the telegram updates collection.
m = db.MongoManager()
m._delete_all(
    db.TelegramStore.get_db_name("Ari"), db.TelegramStore.update_table_name)

# show dbs
# test> use Ari_telegram_bot
# switched to db Ari_telegram_bot
# Ari_telegram_bot> db.dropDatabase()

m._drop_database(db.TelegramStore.get_db_name("Ari"))
