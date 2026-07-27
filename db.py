from pymongo import MongoClient, ASCENDING
import logging
from config import Config

logger = logging.getLogger(__name__)

client = None
db = None

def get_db():
    global client, db
    if db is None:
        client = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client[Config.DATABASE_NAME]
    return db

def get_users_collection():
    return get_db()["users"]

def get_journals_collection():
    return get_db()["journals"]

def init_db():
    try:
        database = get_db()
        # Create indexes for optimized queries
        database["users"].create_index([("email", ASCENDING)], unique=True)
        database["users"].create_index([("username_lower", ASCENDING)], unique=True)
        database["journals"].create_index([("user_id", ASCENDING)])
        database["journals"].create_index([("is_public", ASCENDING), ("created_at", -1)])
        logger.info("MongoDB connection and indexes initialized successfully.")
    except Exception as e:
        logger.warning(f"Note: MongoDB initialization deferral or error: {e}")
