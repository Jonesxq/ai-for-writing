# official_proj/db/dao/character_dao.py
import uuid
from datetime import datetime

class CharacterDAO:
    def __init__(self, mongo):
        self.col = mongo.collection("characters")

    def create(self, novel_id: str, **kwargs) -> dict:
        doc = {
            "_id": str(uuid.uuid4()),
            "novel_id": novel_id,
            **kwargs,
            "created_at": datetime.utcnow()
        }
        self.col.insert_one(doc)
        return doc

    def list_by_novel(self, novel_id: str) -> list[dict]:
        return list(self.col.find({"novel_id": novel_id}))

    def get_by_name(self, novel_id: str, name: str) -> dict | None:
        return self.col.find_one({
            "novel_id": novel_id,
            "name": name
        })

if __name__ == "__main__":
    from official_proj.db.mongo_db.mongo import MongoDB
    mongo = MongoDB()
    dao = CharacterDAO(mongo)
    print(dao.get_by_name)