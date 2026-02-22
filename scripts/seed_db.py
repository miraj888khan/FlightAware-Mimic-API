import json
from pymongo import MongoClient
from pathlib import Path
from datetime import datetime, timezone

# --- Configuration ---
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "flightaware_db"
LIVE_COLLECTION = "live_flights"
LOG_COLLECTION = "completed_flights_log"

# Define the path to the data file relative to this script
DATA_FILE_PATH = Path(__file__).parent.parent / "data" / "seed_flights.json"
# ---------------------

def seed_database():
    """
    Seeds the MongoDB 'live_flights' collection with sample flight data.
    It first clears *both* collections to ensure a clean state.
    """
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.server_info()
        print(f"Successfully connected to MongoDB at {MONGO_URI}")
    except Exception as e:
        print(f"Error: Could not connect to MongoDB. Is it running? \nDetails: {e}")
        return

    db = client[DATABASE_NAME]
    live_collection = db[LIVE_COLLECTION]
    log_collection = db[LOG_COLLECTION]

    try:
        # 1. Read the JSON data file
        if not DATA_FILE_PATH.exists():
            print(f"Error: Data file not found at {DATA_FILE_PATH.resolve()}")
            return
            
        with open(DATA_FILE_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"Loaded {len(data)} flight records from {DATA_FILE_PATH}")

        # 2. Clear existing collections for a clean run
        del_live = live_collection.delete_many({})
        del_log = log_collection.delete_many({})
        print(f"Cleared {del_live.deleted_count} records from '{LIVE_COLLECTION}'.")
        print(f"Cleared {del_log.deleted_count} records from '{LOG_COLLECTION}'.")

        # 3. Insert the new data into 'live_flights'
        if data:
            # Convert date strings from JSON to datetime objects for MongoDB
            for flight in data:
                flight["last_update"] = datetime.fromisoformat(flight["last_update"].replace("Z", "+00:00"))

            insert_result = live_collection.insert_many(data)
            print(f"Successfully inserted {len(insert_result.inserted_ids)} new records into '{LIVE_COLLECTION}'.")
        else:
            print("No data to insert.")
            
    except Exception as e:
        print(f"An error occurred during the seeding process: {e}")
    finally:
        client.close()
        print("MongoDB connection closed.")

if __name__ == "__main__":
    seed_database()