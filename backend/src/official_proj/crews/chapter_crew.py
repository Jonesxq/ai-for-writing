from crewai import Agent, Crew, Task, Process
from crewai.tasks.conditional_task import ConditionalTask
from crewai.tasks.task_output import TaskOutput
from official_proj.services.llm_factory import get_default_llm
from official_proj.schema.json_tasks import (
    WritingTaskOutput,
    PlotAnalysisOutput,
    MemoryUpdateOutput,
    ChapterRewriteOutput,
    ChapterReviewOutput
)
class ChapterCrew:
    """章节创作 Crew（纯代码定义，等价于 YAML）"""

    # ========= Agents =========
    def __init__(self) -> None:
        self.llm = get_default_llm()

    def narrative_writer(self) -> Agent:
        return Agent(
            role="专业小说写手",
            goal="创作情节生动、情感真实的小说章节正文",
            backstory=(
                "你是一名职业小说作者，擅长描写场景、人物对话与情绪变化，"
                "严格遵循剧情规划、世界观设定和人物设定进行写作。"
            ),
            llm=self.llm,
            verbose=True
        )

    def plot_analyst(self) -> Agent:
        return Agent(
            role="资深剧情分析师",
            goal="从小说正文中提炼关键剧情信息",
            backstory=(
                "你擅长从复杂叙事中提取关键信息，"
                "能够将小说文本转化为结构化剧情知识，"
                "方便后续分析和长期记忆。"
            ),
            llm=self.llm,
            verbose=True
        )

    def memory_keeper(self) -> Agent:
        return Agent(
            role="长期剧情记忆与一致性管理员",
            goal="维护小说的长期记忆和剧情一致性",
            backstory=(
                "你负责追踪人物状态、人物关系和未解决的剧情线索，"
                "确保重要信息被正确记录，并在后续章节中不被遗忘或矛盾。"
            ),
            llm=self.llm,
            verbose=True
        )

    def chapter_reviewer(self) -> Agent:
        return Agent(
            role="章节评审官",
            goal="评估章节质量与世界观一致性",
            backstory=(
                "你是一名严格的小说编辑与审核员，"
                "擅长发现跑题、设定违背和逻辑断裂的问题，"
                "并给出简洁客观的评分与评语。"
            ),
            llm=self.llm,
            verbose=True
        )

    # ========= Tasks =========
    @staticmethod
    def _needs_rewrite(output: TaskOutput) -> bool:
        review = output.pydantic
        if not review:
            return False
        try:
            return (
                review.overall_score < 7
                or review.world_consistency_score < 7
                or review.off_topic is True
            )
        except Exception:
            return False

    @staticmethod
    def _has_rewrite_output(output: TaskOutput) -> bool:
        return bool(output.raw and output.pydantic)

    def writing_task(self) -> Task:
        return Task(
            name="writing_task",
            description=(
                "基于故事策划、世界观设定、人物设定以及历史剧情回忆，用白话描述，"
                "撰写下一章节小说正文，确保剧情连贯、节奏合理。\n"
                "每章节的字数为5000左右，确保内容清晰、结构合理。\n"
                "必须使用白话文写作，避免古风/文言风格；"
                "仅当用户主题或世界观明确要求古风时才可使用对应文风。\n\n"
                "【世界观设定】\n{world}\n\n"
                "【历史剧情回忆】\n{last_plot}\n\n"
                "请撰写第 {chapter_number} 章。"
            ),
            expected_output=(
                "请严格只输出 JSON（最外层必须是对象），不允许直接输出小说文本。\n"
                "格式如下：\n"
                "{\n"
                '  "chapter_title": "章节标题（如：第一章 血夜萤火）",\n'
                '  "content": "完整章节正文内容，使用自然段落描述"\n'
                "}"
            ),
            agent=self.narrative_writer(),
            output_pydantic=WritingTaskOutput
        )

    def chapter_rewrite_task(self) -> ConditionalTask:
        return ConditionalTask(
            name="chapter_rewrite_task",
            description=(
                "基于上一任务的评审问题，对本章节进行重写，"
                "必须先列出不合格原因，再给出重写后的章节正文。\n"
                "请以评审 issues 为主要依据进行针对性改写。\n\n"
                "【世界观设定】\n{world}\n\n"
                "【历史剧情回忆】\n{last_plot}\n\n"
                "请从上下文中的 writing_task 输出获取原章节内容。"
            ),
            expected_output=(
                "请严格只输出 JSON（最外层必须是对象），不允许输出多余文字。\n"
                "格式如下：\n"
                "{\n"
                '  "fail_reasons": [\n'
                '    "不合格原因1",\n'
                '    "不合格原因2"\n'
                "  ],\n"
                '  "chapter_title": "重写后的章节标题",\n'
                '  "content": "重写后的完整章节正文内容"\n'
                "}"
            ),
            agent=self.chapter_reviewer(),
            output_pydantic=ChapterRewriteOutput,
            condition=self._needs_rewrite
        )

    def plot_analysis_task(self) -> Task:
        return Task(
            name="plot_analysis_task",
            description=(
                "分析本章节小说内容，提取关键事件、重要信息和潜在影响，"
                "重点关注对后续剧情有长期影响的内容。\n"
                "若存在 chapter_rewrite_task 输出，请以重写后的 content 为准进行分析；"
                "否则以 writing_task 的 content 为准。"
            ),
            expected_output=(
                "请严格只输出 JSON（最外层必须是对象），格式如下：\n"
                "{\n"
                '  "key_events": [\n'
                '    "关键事件1",\n'
                '    "关键事件2"\n'
                "  ],\n"
                '  "consequences": [\n'
                '    "可能产生的影响1",\n'
                '    "可能产生的影响2"\n'
                "  ]\n"
                "}"
            ),
            agent=self.plot_analyst(),
            output_pydantic=PlotAnalysisOutput
        )

    def memory_update_task(self) -> Task:
        return Task(
            name="memory_update_task",
            description=(
                "基于剧情分析结果，更新小说的长期记忆内容，"
                "标注必须长期保留的信息和不可被后续剧情违背的设定。"
            ),
            expected_output=(
                "请严格只输出 JSON（最外层必须是对象），不允许直接输出数组。\n"
                "格式如下：\n"
                "{\n"
                '  "states": [\n'
                "    {\n"
                '      "character_name": "角色名",\n'
                '      "location": "当前位置",\n'
                '      "emotion": "当前情绪",\n'
                '      "goal": "短期或长期目标",\n'
                '      "relationships": {}\n'
                "    }\n"
                "  ]\n"
                "}"
            ),
            agent=self.memory_keeper(),
            output_pydantic=MemoryUpdateOutput
        )

    def chapter_review_task(self) -> Task:
        return Task(
            name="chapter_review_task",
            description=(
                "对本章节内容进行评审，重点检查是否跑题或脱离世界观设定，"
                "并给出总体质量评分与简短评语。\n\n"
                "【世界观设定】\n{world}\n\n"
                "【历史剧情回忆】\n{last_plot}\n"
            ),
            expected_output=(
                "请严格只输出 JSON（最外层必须是对象），不允许输出多余文字。\n"
                "格式如下：\n"
                "{\n"
                '  "overall_score": 8,\n'
                '  "world_consistency_score": 9,\n'
                '  "off_topic": false,\n'
                '  "issues": [\n'
                '    "问题1",\n'
                '    "问题2"\n'
                "  ],\n"
                '  "summary": "简短评语"\n'
                "}"
            ),
            agent=self.chapter_reviewer(),
            output_pydantic=ChapterReviewOutput
        )

    def chapter_rewrite_review_task(self) -> ConditionalTask:
        return ConditionalTask(
            name="chapter_rewrite_review_task",
            description=(
                "对重写后的章节内容进行评审，重点检查是否跑题或脱离世界观设定，"
                "并给出总体质量评分与简短评语。\n"
                "请以 chapter_rewrite_task 输出的 content 为准进行评审。\n\n"
                "【世界观设定】\n{world}\n\n"
                "【历史剧情回忆】\n{last_plot}\n"
            ),
            expected_output=(
                "请严格只输出 JSON（最外层必须是对象），不允许输出多余文字。\n"
                "格式如下：\n"
                "{\n"
                '  "overall_score": 8,\n'
                '  "world_consistency_score": 9,\n'
                '  "off_topic": false,\n'
                '  "issues": [\n'
                '    "问题1",\n'
                '    "问题2"\n'
                "  ],\n"
                '  "summary": "简短评语"\n'
                "}"
            ),
            agent=self.chapter_reviewer(),
            output_pydantic=ChapterReviewOutput,
            condition=self._has_rewrite_output
        )

    # ========= Crew =========

    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.narrative_writer(),
                self.plot_analyst(),
                self.memory_keeper(),
                self.chapter_reviewer()
            ],
            tasks=[
                self.writing_task(),
                self.chapter_review_task(),
                self.chapter_rewrite_task(),
                self.chapter_rewrite_review_task(),
                self.plot_analysis_task(),
                self.memory_update_task()
            ],
            process=Process.sequential,
            verbose=True
        )
