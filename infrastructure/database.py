from pymongo import MongoClient, ASCENDING
from dotenv import load_dotenv
import os
load_dotenv()
uri = os.getenv('MONGODB_URI')
class Database:
    def __init__(self, db_name='easyorder'):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]

    def get_collection(self, collection_name):
        return self.db[collection_name]

    def create_unique_index(self, collection_name, field_name):
        collection = self.get_collection(collection_name)
        collection.create_index([(field_name, ASCENDING)], unique=True)

# 使用範例
# db = Database()
# collection = db.get_collection('mycollection')