from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection

# --- Configuration ---
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "flightaware_db"
LIVE_COLLECTION = "live_flights"
LOG_COLLECTION = "completed_flights_log"
# ---------------------

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.server_info()
    print(f"Connected to MongoDB at {MONGO_URI}")
except Exception as e:
    print(f"FATAL: Could not connect to MongoDB. Please ensure it is running.")
    print(f"Error details: {e}")
    client = None

def get_database() -> Database:
    """Returns the application's database instance."""
    if not client:
        raise ConnectionError("MongoDB client is not available.")
    return client[DATABASE_NAME]

def get_live_flights_collection() -> Collection:
    """
    Returns the 'live_flights' collection for actively tracked flights.
    """
    db = get_database()
    return db[LIVE_COLLECTION]

def get_completed_logs_collection() -> Collection:
    """
    Returns the 'completed_flights_log' collection for archived flights.
    """
    db = get_database()
    return db[LOG_COLLECTION]