# official_proj/db/dao/character_state_dao.py
import uuid
from datetime import datetime

class CharacterStateDAO:
    def __init__(self, mongo):
        self.col = mongo.collection("character_states")

    def create(
        self,
        character_name: str,
        character_id: str,
        chapter_id: str | None,
        location: str,
        emotion: str,
        goal: str,
        relationships: dict
    ) -> dict:
        doc = {
            "character_name": character_name,
            "_id": str(uuid.uuid4()),
            "character_id": character_id,
            "chapter_id": chapter_id,
            "location": location,
            "emotion": emotion,
            "goal": goal,
            "relationships": relationships,
            "created_at": datetime.utcnow()
        }
        self.col.insert_one(doc)
        return doc

    def get_latest(self, character_id: str) -> dict | None:
        return self.col.find_one(
            {"character_id": character_id},
            sort=[("created_at", -1)]
        )

    def get_character_name_with_relationships(self, query: dict = None) -> list[dict]:
        """
        获取角色的character_name及其对应的relationships
        :param query: 可选查询条件（比如按chapter_id/character_id筛选），默认查询所有
        :return: 仅包含character_name和relationships的文档列表
        """
        # 1. 确定查询条件（默认查所有，也可传条件如{"chapter_id": "xxx"}）
        query_condition = query or {}

        # 2. 投影参数：保留character_name和relationships，排除其他字段（含默认的_id）
        projection = {
            "character_name": 1,  # 保留character_name
            "relationships": 1,  # 保留relationships
            "_id": 0  # 排除默认返回的_id
        }

        # 3. 执行查询并返回结果
        return list(self.col.find(query_condition, projection))

    def simplify_character_relationships(self,raw_data: list[dict]) -> str:
        """
        将冗长的角色关系数据精简为LLM友好的简洁文本
        :param raw_data: 原始的角色关系列表（get_character_name_with_relationships返回的结果）
        :return: 精简后的文本字符串
        """
        simplified_lines = []
        for item in raw_data:
            char_name = item["character_name"]
            relationships = item["relationships"]

            # 精简每个关系的描述：提取核心关键词，去掉冗余修饰
            simplified_rels = []
            for rel_char, rel_desc in relationships.items():
                # 核心逻辑：保留「关系对象+核心关系」，截取关键信息（前20字内）或提取核心标签
                # 也可以根据实际需求自定义精简规则
                if len(rel_desc) > 20:
                    # 方式1：截取核心短句（适合保留上下文）
                    simplified_desc = rel_desc[:20].strip() + "..."
                    # 方式2：提取核心关键词（更精简，注释掉可切换）
                    #simplified_desc = ",".join([word for word in rel_desc.split() if len(word) > 2][:3])
                else:
                    simplified_desc = rel_desc

                simplified_rels.append(f"{rel_char}: {simplified_desc}")

            # 拼接当前角色的精简信息
            simplified_lines.append(f"{char_name}：{'; '.join(simplified_rels)}")

        # 最终拼接成LLM易读的文本
        return "\n".join(simplified_lines)


if __name__ == "__main__":
    from official_proj.db.mongo_db.mongo import MongoDB
    mongo = MongoDB()
    dao = CharacterStateDAO(mongo)
    print(dao.simplify_character_relationships(dao.get_character_name_with_relationships()))

