# official_proj/db/dao/world_setting_dao.py
import uuid
from datetime import datetime

class WorldSettingDAO:
    def __init__(self, mongo):
        self.col = mongo.collection("world_settings")

    def create(
        self,
        novel_id: str,
        world_rules: list,
        tone: str,
        technology_level: str
    ) -> dict:
        doc = {
            "_id": str(uuid.uuid4()),
            "novel_id": novel_id,
            "world_rules": world_rules,
            "tone": tone,
            "technology_level": technology_level,
            "created_at": datetime.utcnow()
        }
        self.col.insert_one(doc)
        return doc

    def get_latest(self, novel_id: str) -> list | None:
        """
        获取指定novel_id的最新世界设定的world_rules
        返回值：仅返回world_rules列表（无其他字段），无数据则返回None
        """
        # 投影参数：只保留world_rules，排除默认的_id
        projection = {
            "world_rules": 1,
            "_id": 0
        }

        # 查询最新文档 + 只返回指定字段
        result_doc = self.col.find_one(
            {"novel_id": novel_id},
            projection=projection,  # 新增：指定只返回world_rules
            sort=[("created_at", -1)]
        )

        # 提取纯world_rules列表（而非包含world_rules的字典）
        if result_doc:
            return result_doc.get("world_rules", [])
        return None

    def get_latest_full(self, novel_id: str) -> dict | None:
        """
        获取指定novel_id的最新世界设定完整信息
        返回字段：world_rules/tone/technology_level/created_at（不含_id）
        """
        projection = {
            "world_rules": 1,
            "tone": 1,
            "technology_level": 1,
            "created_at": 1,
            "_id": 0
        }

        return self.col.find_one(
            {"novel_id": novel_id},
            projection=projection,
            sort=[("created_at", -1)]
        )


# 测试代码（可选）
if __name__ == "__main__":
    from official_proj.db.mongo_db.mongo import MongoDB

    mongo = MongoDB()
    dao = WorldSettingDAO(mongo)
    print(dao.get_latest("novel_001"))

