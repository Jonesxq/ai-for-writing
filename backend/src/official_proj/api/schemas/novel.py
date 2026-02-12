"""小说相关 API 的请求与响应结构。"""

from pydantic import BaseModel


class AuthReq(BaseModel):
    """登录/注册请求体。"""

    username: str
    password: str


class InitNovelRequest(BaseModel):
    """初始化小说请求体。"""

    novel_id: str
    topic: str


class NextChapterRequest(BaseModel):
    """生成下一章请求体。"""

    novel_id: str


class ChapterReview(BaseModel):
    """章节评审结果结构。"""

    overall_score: int
    world_consistency_score: int
    off_topic: bool
    issues: list[str]
    summary: str


class RewriteInfo(BaseModel):
    """重写信息（是否重写与原因）。"""

    reasons: list[str]
    applied: bool = True


class ChapterResponse(BaseModel):
    """章节生成返回结构。"""

    novel_id: str
    chapter_number: int
    title: str
    content: str
    review: ChapterReview | None = None
    rewrite: RewriteInfo | None = None


class CreateNovelRequest(BaseModel):
    """创建小说请求体。"""

    novel_id: str
    topic: str


class InitResponse(BaseModel):
    """初始化小说返回结构。"""

    novel_id: str
    chapter_number: int
    title: str
    content: str
    world_rules: list[str]
    review: ChapterReview | None = None
    rewrite: RewriteInfo | None = None
