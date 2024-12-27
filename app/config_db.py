from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

# Connect to MongoDB (Replace URI with your MongoDB connection string if needed)
client = MongoClient(MONGO_URI)

# Create a new database
db_name = "twitter_trends"  # Replace with your desired database name
db = client[db_name]
print(f"Database '{db_name}' created.")

# Create a new collection
collection_name = "trend_data"  # Replace with your desired collection name
collection = db[collection_name]
print(f"Collection '{collection_name}' created in database '{db_name}'.")

# Insert a sample document to ensure creation
sample_data = {
    "trends": {
        "trend1": "#SampleTrend1",
        "trend2": "#SampleTrend2",
        "trend3": "#SampleTrend3",
        "trend4": "#SampleTrend4"
    },
    "start_time": "2024-12-26 10:00:00",
    "end_time": "2024-12-26 10:10:00",
    "ip_address": "203.0.113.195"
}

result = collection.insert_one(sample_data)
print(f"Sample document inserted with ID: {result.inserted_id}")
