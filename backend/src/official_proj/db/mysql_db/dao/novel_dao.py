# official_proj/db/dao/novel_dao.py
from typing import Sequence

from sqlmodel import Session, select
from official_proj.db.mysql_db.model.novel import Novel


class NovelDAO:
    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        novel_id: str,
        topic: str,
        user_id: int
    ) -> Novel:
        novel = Novel(
            novel_id=novel_id,
            topic=topic,
            user_id=user_id
        )
        self.session.add(novel)
        self.session.commit()
        self.session.refresh(novel)
        return novel

    def get(self, novel_id: str) -> Novel | None:
        return self.session.get(Novel, novel_id)

    def get_by_user(
        self,
        novel_id: str,
        user_id: int
    ) -> Novel | None:
        stmt = select(Novel).where(
            Novel.novel_id == novel_id,
            Novel.user_id == user_id
        )
        return self.session.exec(stmt).first()

    def list_by_user(self, user_id: int) -> Sequence[Novel]:
        stmt = select(Novel).where(Novel.user_id == user_id)
        return self.session.exec(stmt).all()
