import logging
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from backend.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

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
    try:
        db.client = AsyncIOMotorClient(settings.MONGO_URL)
        # Verify the connection is working by pinging the server
        await db.client.admin.command('ping')
        print("Successfully connected to MongoDB.")
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        raise e

async def close_mongo_connection():
    """
    Closes the MongoDB connection when the app shuts down.
    """
    print("Closing MongoDB connection...")
    try:
        if db.client is not None:
            db.client.close()
            db.client = None  # Reset client to None after closing
            print("MongoDB connection closed.")
        else:
            print("MongoDB connection was already closed or not initialized.")
    except Exception as e:
        print(f"Error closing MongoDB connection: {e}")
        # Still set client to None even if close fails
        db.client = None

async def check_database_health() -> bool:
    """
    Checks if the database connection is healthy.
    Returns True if connection is working, False otherwise.
    """
    try:
        if db.client is None:
            return False
        
        # Ping the database to check if it's responsive
        await db.client.admin.command('ping')
        return True
    except Exception as e:
        print(f"Database health check failed: {e}")
        return False

async def get_database_info() -> dict:
    """
    Returns information about the database connection for monitoring.
    """
    try:
        if db.client is None:
            return {"status": "disconnected", "database": None}
        
        # Get server info
        server_info = await db.client.admin.command('ping')
        database_name = settings.DATABASE_NAME
        
        return {
            "status": "connected",
            "database": database_name,
            "server_response": "ok" if server_info.get("ok") == 1 else "error"
        }
    except Exception as e:
        return {
            "status": "error", 
            "database": settings.DATABASE_NAME,
            "error": str(e)
        }

def get_database() -> AsyncIOMotorDatabase:
    """
    Returns the database instance from the client.
    This is a dependency that our API endpoints will use to interact with the database.
    """
    if db.client is None:
        # This should ideally not happen if the startup event works correctly.
        raise ConnectionError("Database client not initialized. Call 'connect_to_mongo' first.")
    
    try:
        return db.client[settings.DATABASE_NAME]
    except Exception as e:
        raise ConnectionError(f"Failed to get database instance: {e}")

async def test_database_connection() -> bool:
    """Test database connection and return status."""
    try:
        database = get_database()
        # Try to ping the database
        await database.command("ping")
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False

async def get_database_health() -> dict:
    """Get comprehensive database health information."""
    try:
        database = get_database()
        
        # Test basic connectivity
        ping_result = await database.command("ping")
        
        # Get server status (limited info for security)
        try:
            server_status = await database.command("serverStatus")
            uptime = server_status.get("uptime", 0)
        except Exception:
            # Some MongoDB instances may not allow serverStatus
            uptime = None
        
        # Count documents in key collections
        collections_info = {}
        for collection_name in ["conversations", "user_profiles", "financial_goals", "financial_plans"]:
            try:
                count = await database[collection_name].count_documents({})
                collections_info[collection_name] = {"document_count": count, "status": "accessible"}
            except Exception as e:
                collections_info[collection_name] = {"status": "error", "error": str(e)}
        
        return {
            "status": "healthy",
            "database_name": database.name,
            "ping": ping_result,
            "uptime_seconds": uptime,
            "collections": collections_info,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }