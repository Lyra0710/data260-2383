import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable is not set")

client = MongoClient(MONGO_URI)

db = client["s2383_doc"]
fixtures_collection = db["fixtures"]
messages_collection = db["messages"]
summaries_collection = db["summaries"]
episodes_collection = db["episodes"]
