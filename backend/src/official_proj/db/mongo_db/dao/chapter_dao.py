# official_proj/db/dao/chapter_dao.py
import uuid
from datetime import datetime

class ChapterDAO:
    def __init__(self, mongo):
        self.col = mongo.collection("chapters")

    def create(
        self,
        novel_id: str,
        chapter_number: int,
        title: str,
        content: str
    ) -> dict:
        doc = {
            "_id": str(uuid.uuid4()),
            "novel_id": novel_id,
            "chapter_number": chapter_number,
            "title": title,
            "content": content,
            "created_at": datetime.utcnow()
        }
        self.col.insert_one(doc)
        return doc

    def set_rewrite_meta(
        self,
        chapter_id: str,
        reasons: list[str],
        original_title: str,
        original_content: str
    ) -> dict | None:
        rewrite_meta = {
            "reasons": reasons,
            "original_title": original_title,
            "original_content": original_content,
            "created_at": datetime.utcnow()
        }
        self.col.update_one(
            {"_id": chapter_id},
            {"$set": {"rewrite_meta": rewrite_meta}}
        )
        return self.col.find_one({"_id": chapter_id})

    def get_last_chapter(self, novel_id: str) -> dict | None:
        return self.col.find_one(
            {"novel_id": novel_id},
            sort=[("chapter_number", -1)]
        )

    def list_by_novel(self, novel_id: str) -> list[dict]:
        return list(
            self.col.find(
                {"novel_id": novel_id}
            ).sort("chapter_number", 1)
        )
