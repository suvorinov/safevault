"""Database connection handler."""
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import get_settings

settings = get_settings()

class Database:
    client: AsyncIOMotorClient = None

db = Database()

async def connect_to_mongo():
    """Creates database connection."""
    db.client = AsyncIOMotorClient(settings.mongo_uri)
    print("Connected to MongoDB.")

async def close_mongo_connection():
    """Closes database connection."""
    db.client.close()
    print("Disconnected from MongoDB.")

def get_database():
    """Returns the database instance."""
    return db.client[settings.mongo_db_name]
