# official_proj/db/mongo.py
from pymongo import MongoClient

class MongoDB:
    def __init__(
        self,
        uri: str = "mongodb://localhost:27017",
        db_name: str = "novel_db"
    ):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]

    def collection(self, name: str):
        return self.db[name]
