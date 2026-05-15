"""Database connection handler."""

import logging

from motor.motor_asyncio import AsyncIOMotorClient

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class Database:
    client: AsyncIOMotorClient = None


db = Database()


async def connect_to_mongo():
    """Creates database connection."""
    db.client = AsyncIOMotorClient(settings.mongo_uri)
    logger.info("Connected to MongoDB.")


async def close_mongo_connection():
    """Closes database connection."""
    db.client.close()
    logger.info("Disconnected from MongoDB.")


def get_database():
    """Returns the database instance."""
    return db.client[settings.mongo_db_name]