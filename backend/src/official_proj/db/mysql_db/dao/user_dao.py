from sqlmodel import Session, select
from official_proj.db.mysql_db.model.user import User

class UserDAO:
    def __init__(self, session: Session):
        self.session = session

    def create(self, username: str, password: str) -> User:
        user = User(username=username, password=password)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def get_by_username(self, username: str) -> User | None:
        statement = select(User).where(User.username == username)
        return self.session.exec(statement).first()

    def get_by_id(self, user_id: int) -> User | None:
        return self.session.get(User, user_id)
