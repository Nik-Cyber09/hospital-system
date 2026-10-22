import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.server_api import ServerApi
from app.config import settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient = None
_db: AsyncIOMotorDatabase = None

async def connect_database():
    """Connect to MongoDB and return the database instance."""
    global _client, _db
    if _client is not None:
        return _db

    uri = settings.mongodb_uri
    if not uri:
        raise RuntimeError(
            "MONGODB_URI is required. Configure it in server/.env."
        )

    # Extract db name if specified in URI
    db_name = "carepoint"
    clean_uri = uri.split("?")[0].rstrip("/")
    if "/" in clean_uri:
        candidate = clean_uri.split("/")[-1]
        if candidate and not candidate.startswith("mongodb") and not ":" in candidate:
            db_name = candidate

    kwargs = {"appName": "carepoint-hospital"}
    if "mongodb+srv" in uri:
        kwargs["server_api"] = ServerApi("1")

    _client = AsyncIOMotorClient(uri, **kwargs)
    _db = _client[db_name]

    try:
        await _client.admin.command("ping")
        logger.info(f"Connected to MongoDB database: {db_name}")
    except Exception as error:
        logger.error(f"MongoDB connection failed: {error}")
        _client = None
        _db = None
        raise

    return _db

async def disconnect_database():
    """Disconnect from MongoDB."""
    global _client, _db
    if _client is not None:
        _client.close()
        _client = None
        _db = None
        logger.info("Disconnected from MongoDB.")

def get_database() -> AsyncIOMotorDatabase:
    """Return the current database instance."""
    if _db is None:
        raise RuntimeError("Database not connected. Call connect_database() first.")
    return _db
