"""crew 工作流的任务输出 Pydantic 结构。"""

from pydantic import BaseModel, Field
from typing import List, Dict


# 1. 故事策划
class StoryPlanningOutput(BaseModel):
    """故事规划：总体走向与冲突目标。"""

    story_overview: str
    core_conflicts: List[str]
    next_chapter_goal: str


# 2. 世界观
class WorldBuildingOutput(BaseModel):
    """世界观：规则、基调与科技水平。"""

    world_rules: List[str]
    tone: str
    technology_level: str


# 3. 人物设定
class CharacterDesignItem(BaseModel):
    """单个角色的设定条目。"""

    name: str
    role: str | None = None
    personality: str | None = None
    motivation: str | None = None
    flaws: str | None = None
    growth_arc: str | None = None


class CharacterDesignOutput(BaseModel):
    """角色设定集合。"""

    characters: List[CharacterDesignItem]


# 4. 剧情分析
class PlotAnalysisOutput(BaseModel):
    """剧情分析：关键事件与后果。"""

    key_events: List[str]
    consequences: List[str]


# 5. 人物状态
class MemoryUpdateItem(BaseModel):
    """章节完成后的角色状态快照。"""

    character_name: str
    location: str
    emotion: str
    goal: str
    relationships: Dict


class MemoryUpdateOutput(BaseModel):
    """角色状态更新集合。"""

    states: List[MemoryUpdateItem]


# 6. 写作
class WritingTaskOutput(BaseModel):
    """写作输出：标题与正文内容。"""

    chapter_title: str = Field(
        description="章节标题，例如：第一章 血夜萤火"
    )
    content: str = Field(
        description="完整章节正文内容，使用自然段落描述"
    )


# 7. 章节重写
class ChapterRewriteOutput(BaseModel):
    """章节重写输出（原稿未达标时）。"""

    fail_reasons: List[str] = Field(
        description="不达标原因列表"
    )
    chapter_title: str = Field(
        description="重写后的章节标题"
    )
    content: str = Field(
        description="重写后的章节正文内容"
    )


# 8. 章节评审
class ChapterReviewOutput(BaseModel):
    """章节评审结果。"""

    overall_score: int = Field(
        description="整体质量评分（0-10）"
    )
    world_consistency_score: int = Field(
        description="世界观一致性评分（0-10）"
    )
    off_topic: bool = Field(
        description="是否跑题或脱离世界观"
    )
    issues: List[str] = Field(
        description="主要问题或违和点"
    )
    summary: str = Field(
        description="简短评语"
    )
