from pymongo import MongoClient
from datetime import datetime
import os

client = MongoClient('mongodb://localhost:27017/')

db = client.rocketchat

def update_setting(setting, value):
    db.rocketchat_settings.update_one(
        {"_id": setting},
        {"$set": {
            "value": value,
            # Updated at:
            "_updatedAt": datetime.utcnow()
        }}
        
    )

def is_mongodb_available():
    try:
        client.server_info()
        return True
    except:
        return False