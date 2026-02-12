from sqlmodel import create_engine, Session
from sqlmodel import SQLModel
from official_proj.db.mysql_db.model.user import User
from official_proj.db.mysql_db.model.novel import Novel

MYSQL_URL = (
    "mysql+pymysql://root:528467@127.0.0.1:3306/novel_db"
)

engine = create_engine(
    MYSQL_URL,
    echo=True,              # 开发期开启
    pool_pre_ping=True,     # 防止 MySQL 断连
    pool_recycle=3600
)


def get_session():
    with Session(engine) as session:
        yield session

# if __name__ == "__main__":
#
#     try:
#         print("===== 调试：查看metadata中的表 =====")
#         # 打印metadata里所有已注册的表（关键！看是否有users）
#         print(f"已注册的表列表：{list(SQLModel.metadata.tables.keys())}")
#
#         if "users" in SQLModel.metadata.tables:
#             print("✅ 识别到users表，开始创建...")
#             # 显式指定创建users表（强制绑定，不再依赖自动识别）
#             SQLModel.metadata.create_all(engine, tables=[User.__table__, Novel.__table__])
#         else:
#             print("❌ 未识别到users表！模型注册失败")
#
#         print("数据表创建完成！")
#     except Exception as e:
#         print(f"建表失败，错误信息：{e}")
