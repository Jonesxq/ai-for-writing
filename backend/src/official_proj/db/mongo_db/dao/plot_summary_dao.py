# official_proj/db/dao/plot_summary_dao.py
import uuid
from datetime import datetime

class PlotSummaryDAO:
    def __init__(self, mongo):
        self.col = mongo.collection("plot_summaries")

    def create(
        self,
        novel_id: str,
        chapter_id: str,
        key_events: list,
        consequences: list
    ) -> dict:
        doc = {
            "_id": str(uuid.uuid4()),
            "novel_id": novel_id,
            "chapter_id": chapter_id,
            "key_events": key_events,
            "consequences": consequences,
            "created_at": datetime.utcnow()
        }
        self.col.insert_one(doc)
        return doc

    def list_recent(self, novel_id: str, limit: int = 5) -> list[dict]:
        # 投影参数：1=保留该字段，0=排除该字段
        # 注意：_id字段默认会返回，需要显式设为0排除
        projection = {
            "key_events": 1,  # 保留key_events
            "consequences": 1,  # 保留consequences
            "_id": 0  # 排除默认返回的_id字段
        }

        return list(
            self.col.find(
                {"novel_id": novel_id},  # 查询条件
                projection  # 投影（只返回指定字段）
            )
            .sort("created_at", -1)
            .limit(limit)
        )
if __name__ == "__main__":
    # 测试现在已经可以只返回指定字段了是一个list
    from official_proj.db.mongo_db.mongo import MongoDB
    mongo = MongoDB()
    dao = PlotSummaryDAO(mongo)
    print(type(dao.list_recent("novel_001")))