from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
from .config import settings

class Database:
    client: Optional[AsyncIOMotorClient] = None
    database = None

database = Database()

async def get_database():
    return database.database

async def connect_to_mongo():
    database.client = AsyncIOMotorClient(settings.mongodb_uri)
    database.database = database.client[settings.database_name]
    print(f"Connected to MongoDB at {settings.mongodb_uri}")

async def close_mongo_connection():
    if database.client:
        database.client.close()
        print("Disconnected from MongoDB")