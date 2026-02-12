import uuid
from datetime import datetime


class ChapterReviewDAO:
    def __init__(self, mongo):
        self.col = mongo.collection("chapter_reviews")

    def create(
        self,
        novel_id: str,
        chapter_id: str,
        overall_score: int,
        world_consistency_score: int,
        off_topic: bool,
        issues: list,
        summary: str
    ) -> dict:
        doc = {
            "_id": str(uuid.uuid4()),
            "novel_id": novel_id,
            "chapter_id": chapter_id,
            "overall_score": overall_score,
            "world_consistency_score": world_consistency_score,
            "off_topic": off_topic,
            "issues": issues,
            "summary": summary,
            "created_at": datetime.utcnow()
        }
        self.col.insert_one(doc)
        return doc

    def get_latest_by_chapter(self, chapter_id: str) -> dict | None:
        return self.col.find_one(
            {"chapter_id": chapter_id},
            sort=[("created_at", -1)]
        )
