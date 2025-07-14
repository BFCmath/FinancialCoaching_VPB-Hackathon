from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from backend.core.config import settings

class DataBase:
    """
    A class to manage the MongoDB connection.
    Ensures that we have a single client instance across the application.
    """
    client: AsyncIOMotorClient = None

db = DataBase()

async def connect_to_mongo():
    """
    Establishes the connection to the MongoDB database when the app starts.
    """
    print("Connecting to MongoDB...")
    db.client = AsyncIOMotorClient(settings.MONGO_URL)
    # You can add a check here to ensure the connection is successful if needed,
    # for example, by pinging the server.
    # await db.client.admin.command('ping')
    print("Successfully connected to MongoDB.")

async def close_mongo_connection():
    """
    Closes the MongoDB connection when the app shuts down.
    """
    print("Closing MongoDB connection...")
    db.client.close()
    print("MongoDB connection closed.")

def get_database() -> AsyncIOMotorDatabase:
    """
    Returns the database instance from the client.
    This is a dependency that our API endpoints will use to interact with the database.
    """
    if db.client is None:
        # This should ideally not happen if the startup event works correctly.
        raise Exception("Database client not initialized. Call 'connect_to_mongo' first.")
    return db.client[settings.DATABASE_NAME]