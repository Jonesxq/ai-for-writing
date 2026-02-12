from crewai import Agent, Crew, Process, Task
from crewai.tasks.conditional_task import ConditionalTask
from crewai.tasks.task_output import TaskOutput
from official_proj.schema.json_tasks import (StoryPlanningOutput,WorldBuildingOutput,CharacterDesignOutput,
                                             PlotAnalysisOutput,MemoryUpdateOutput,WritingTaskOutput,
                                             ChapterRewriteOutput,ChapterReviewOutput)
from official_proj.services.llm_factory import get_default_llm
class OfficialProj():
    """OfficialProj crew"""
    # ========= Agents =========
    # ========= Story Planner =========
    def __init__(self) -> None:
        self.llm = get_default_llm()

    def story_planner(self) -> Agent:
        return Agent(
            role="资深小说故事策划师",
            goal="为小说设计清晰、可持续展开的整体剧情结构",
            backstory=(
                "你是一名经验丰富的小说策划师，精通长篇连载小说的叙事结构、"
                "节奏控制和伏笔设计，擅长构建长期不崩盘的故事主线。"
            ),
            llm=self.llm,
            verbose=True,
        )

    # ========= World Builder =========
    def world_builder(self) -> Agent:
        return Agent(
            role="资深世界观构建师",
            goal="构建逻辑自洽、细节丰富的小说世界观",
            backstory=(
                "你擅长设计世界规则、社会结构、力量体系和历史背景，"
                "能够确保世界观在长篇故事中始终保持一致，不出现逻辑漏洞。"
            ),
            llm=self.llm,
            verbose=True,
        )

    # ========= Character Architect =========
    def character_architect(self) -> Agent:
        return Agent(
            role="资深人物架构师",
            goal="设计立体、有成长性的小说人物",
            backstory=(
                "你精通人物心理学与角色成长曲线，"
                "能够确保人物动机合理、情绪变化自然，"
                "并在长期连载中保持人设稳定。"
            ),
            llm=self.llm,
            verbose=True,
        )

    # ========= Narrative Writer =========
    def narrative_writer(self) -> Agent:
        return Agent(
            role="专业小说写手",
            goal="创作情节生动、情感真实的小说章节正文",
            backstory=(
                "你是一名职业小说作者，擅长描写场景、人物对话与情绪变化，"
                "严格遵循剧情规划、世界观设定和人物设定进行写作。"
            ),
            llm=self.llm,
            verbose=True,
        )

    # ========= Plot Analyst =========
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
            verbose=True,
        )

    # ========= Memory Keeper =========
    def memory_keeper(self) -> Agent:
        return Agent(
            role="长期剧情记忆与一致性管理员",
            goal="维护小说的长期记忆和剧情一致性",
            backstory=(
                "你负责追踪人物状态、人物关系和未解决的剧情线索，"
                "确保重要信息被正确记录，并在后续章节中不被遗忘或矛盾。"
            ),
            llm=self.llm,
            verbose=True,
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
            verbose=True,
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
    def story_planning_task(self) -> Task:
        return Task(
            name="story_planning_task",
            description=(
                "围绕小说主题 {topic}，设计整体故事走向，"
                "明确核心冲突、长期剧情主线，并给出下一章节的写作目标。"
            ),
            expected_output=(
                "请严格只输出 JSON（最外层必须是对象），不允许输出数组或多余文字。\n"
                "格式如下：\n"
                "{\n"
                '  "story_overview": "整体剧情主线概述",\n'
                '  "core_conflicts": [\n'
                '    "核心冲突1",\n'
                '    "核心冲突2"\n'
                "  ],\n"
                '  "next_chapter_goal": "下一章节的写作目标"\n'
                "}"
            ),
            agent=self.story_planner(),
            output_pydantic=StoryPlanningOutput
        )

    # =========================
    # 2. 世界观构建 Task
    # =========================
    def world_building_task(self) -> Task:
        return Task(
            name="world_building_task",
            description=(
                "根据当前故事策划，构建或补充小说的世界观设定，"
                "明确世界规则、力量或科技水平，以及本章节的整体氛围。"
            ),
            expected_output=(
                "请严格只输出 JSON（最外层必须是对象），格式如下：\n"
                "{\n"
                '  "world_rules": [\n'
                '    "规则1",\n'
                '    "规则2"\n'
                "  ],\n"
                '  "tone": "整体基调",\n'
                '  "technology_level": "科技或文明水平"\n'
                "}"
            ),
            agent=self.world_builder(),
            output_pydantic=WorldBuildingOutput
        )

    # =========================
    # 3. 人物设定 Task
    # =========================
    def character_design_task(self) -> Task:
        return Task(
            name="character_design_task",
            description=(
                "设计或更新下一章节中涉及的主要人物，"
                "明确他们的性格特征、动机、缺陷与成长方向。"
            ),
            expected_output=(
                "请严格只输出 JSON（最外层必须是对象），不允许直接输出数组。\n"
                "格式如下：\n"
                "{\n"
                '  "characters": [\n'
                "    {\n"
                '      "name": "角色名",\n'
                '      "role": "角色定位",\n'
                '      "personality": "性格特征",\n'
                '      "motivation": "核心动机",\n'
                '      "flaws": "性格或能力缺陷",\n'
                '      "growth_arc": "成长弧线"\n'
                "    }\n"
                "  ]\n"
                "}"
            ),
            agent=self.character_architect(),
            output_pydantic=CharacterDesignOutput
        )

    # =========================
    # 4. 小说正文 Task
    # =========================
    def writing_task(self) -> Task:
        return Task(
            name="writing_task",
            description=(
                "基于故事策划、世界观设定、人物设定以及历史剧情回忆，用白话描述，"
                "撰写下一章节小说正文，确保剧情连贯、节奏合理。"
                "每章节的字数为5000左右，确保内容清晰、结构合理。"
                "必须使用白话文写作，避免古风/文言风格；"
                "仅当用户主题或世界观明确要求古风时才可使用对应文风。"
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
                "请以评审 issues 为主要依据进行针对性改写。\n"
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

    # =========================
    # 5. 剧情分析 Task
    # =========================
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

    # =========================
    # 6. 记忆更新 Task
    # =========================
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

    # =========================
    # 7. 章节评审 Task
    # =========================
    def chapter_review_task(self) -> Task:
        return Task(
            name="chapter_review_task",
            description=(
                "对本章节内容进行评审，重点检查是否跑题或脱离世界观设定，"
                "并给出总体质量评分与简短评语。"
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
                "请以 chapter_rewrite_task 输出的 content 为准进行评审。"
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
            #写的顺序代表agent和任务的执行顺序。
            agents=[
                self.story_planner(),
                self.world_builder(),
                self.character_architect(),
                self.narrative_writer(),
                self.plot_analyst(),
                self.memory_keeper(),
                self.chapter_reviewer()
            ],
            tasks=[
                self.story_planning_task(),
                self.world_building_task(),
                self.character_design_task(),
                self.writing_task(),
                self.chapter_review_task(),
                self.chapter_rewrite_task(),
                self.chapter_rewrite_review_task(),
                self.plot_analysis_task(),
                self.memory_update_task(),
            ],
            process=Process.sequential,
            verbose=True
        )

# #debugg
# from crewai import Agent, Crew, Process, Task
# from crewai.project import CrewBase, agent, crew, task, output_pydantic
# from crewai.agents.agent_builder.base_agent import BaseAgent
# from typing import List
# from official_proj.schemas.json_tasks import WorldBuildingOutput
#
# @CrewBase
# class OfficialProj():
#     """OfficialProj crew"""
#
#     agents: List[BaseAgent]
#     tasks: List[Task]
#
#     @agent
#     def world_builder(self) -> Agent:
#         return Agent(
#             config=self.agents_config['world_builder'],  # type: ignore[index]
#             verbose=True
#         )
#
#     @agent
#     def story_planner(self) -> Agent:
#         return Agent(
#             config=self.agents_config['story_planner'],  # type: ignore[index]
#             verbose=True
#         )
#
#     @task
#     def world_building_task(self) -> Task:
#         return Task(
#             config=self.tasks_config['world_building_task'],  # type: ignore[index]
#             output_file=r"E:\code\official_proj\knowledge\output\world.json",
#             # output_json=WorldBuildingOutput,
#             output_pydantic=WorldBuildingOutput
#         )
#
#     @task
#     def story_planning_task(self) -> Task:
#         return Task(
#             config=self.tasks_config['story_planning_task'],  # type: ignore[index]
#             output_file=r"E:\code\official_proj\knowledge\output\story.md",
#             markdown=True,
#         )
#
#     @crew
#     def crew(self) -> Crew:
#         return Crew(
#             agents=self.agents,  # Automatically created by the @agent decorator
#             tasks=self.tasks,  # Automatically created by the @task decorator
#             process=Process.sequential,
#             verbose=True,
#             # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
#         )
