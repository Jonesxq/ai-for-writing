"""人物状态持久化服务。"""

from official_proj.db.mongo_db.dao.character_dao import CharacterDAO
from official_proj.db.mongo_db.dao.character_state_dao import CharacterStateDAO
from official_proj.db.mongo_db.mongo import MongoDB


def persist_character_state(
    mongo: MongoDB,
    novel_id: str,
    chapter_id: str,
    state: dict
):
    """将单个角色的状态写入数据库（角色不存在则跳过）。"""
    # 初始化 DAO。
    character_dao = CharacterDAO(mongo)
    state_dao = CharacterStateDAO(mongo)

    # 通过角色名查找角色主记录。
    name = state["character_name"]

    character = character_dao.get_by_name(
        novel_id=novel_id,
        name=name
    )
    if not character:
        return

    # 写入该角色在当前章节的状态。
    state_dao.create(
        character_id=character["_id"],
        character_name=character["name"],
        chapter_id=chapter_id,
        location=state.get("location"),
        emotion=state.get("emotion"),
        goal=state.get("goal"),
        relationships=state.get("relationships", {})
    )
