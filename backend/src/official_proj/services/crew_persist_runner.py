"""初始化流程的执行与持久化（带容错）。"""

import traceback

from official_proj.crews.compete_crew import OfficialProj

from official_proj.db.mongo_db.mongo import MongoDB
from official_proj.db.mongo_db.dao.world_setting_dao import WorldSettingDAO
from official_proj.db.mongo_db.dao.character_dao import CharacterDAO
from official_proj.db.mongo_db.dao.plot_summary_dao import PlotSummaryDAO
from official_proj.db.mongo_db.dao.character_state_dao import CharacterStateDAO
from official_proj.db.mongo_db.dao.chapter_dao import ChapterDAO
from official_proj.db.mongo_db.dao.agent_log_dao import AgentLogDAO
from official_proj.db.mongo_db.dao.chapter_review_dao import ChapterReviewDAO

from official_proj.services.character_state_persist_service import (
    persist_character_state
)
from official_proj.services.knowledge_cleanup import cleanup_generated_knowledge
from official_proj.utils.task_outputs import extract_writing, iter_review_outputs


class CrewPersistRunner:
    """执行初始化 crew 并将输出写入 MongoDB。"""

    def __init__(self, mongo: MongoDB):
        """初始化 DAO 依赖与持久化工具。"""
        self.mongo = mongo

        self.chapter_dao = ChapterDAO(mongo)
        self.world_dao = WorldSettingDAO(mongo)
        self.character_dao = CharacterDAO(mongo)
        self.plot_dao = PlotSummaryDAO(mongo)
        self.state_dao = CharacterStateDAO(mongo)
        self.agent_log_dao = AgentLogDAO(mongo)
        self.review_dao = ChapterReviewDAO(mongo)

    def run(self, inputs: dict):
        """运行 crew 并在结束后持久化所有输出。"""
        # 组装 crew 并执行任务。
        crew = OfficialProj().crew()
        crew.kickoff(inputs=inputs)

        # 将每个任务输出整理成字典，便于后续处理。
        task_outputs = {
            task.name: task.output
            for task in crew.tasks
        }

        try:
            self.persist_outputs(inputs, task_outputs)
            return task_outputs
        finally:
            # 无论成功与否都清理临时知识文件。
            cleanup_generated_knowledge()

    def persist_outputs(self, inputs: dict, task_outputs: dict):
        """将 crew 输出写入世界观、人物、章节、评审等集合。"""
        novel_id = inputs["novel_id"]
        # print("🧪 task_outputs keys:", task_outputs.keys())
        #
        # for name, output in task_outputs.items():
        #     print(f"\n--- {name} ---")
        #     print("raw:", output.raw)
        #     print("pydantic:", output.pydantic)
        # ---------- 1️⃣ 世界观 ----------
        try:
            world_output = task_outputs["world_building_task"].pydantic
            self.world_dao.create(
                novel_id=novel_id,
                world_rules=world_output.world_rules,
                tone=world_output.tone,
                technology_level=world_output.technology_level
            )
        except Exception:
            print("⚠️ 世界观写入失败")
            traceback.print_exc()

        # ---------- 2️⃣ 人物 ----------
        try:
            character_output = task_outputs["character_design_task"].pydantic
            for char in character_output.characters:
                self.character_dao.create(
                    novel_id=novel_id,
                    name=char.name,
                    role=char.role,
                    personality=char.personality,
                    motivation=char.motivation,
                    flaws=char.flaws,
                    growth_arc=char.growth_arc
                )
        except Exception:
            print("⚠️ 人物写入失败")
            traceback.print_exc()

        # ---------- 3️⃣ 章节 ----------
        try:
            # 抽取最终正文与重写信息。
            writing_pack = extract_writing(task_outputs)
            writing_output = writing_pack.writing_output
            rewrite_output = writing_pack.rewrite_output

            chapter = self.chapter_dao.create(
                novel_id=novel_id,
                chapter_number=inputs.get("chapter_number", 1),
                title=writing_pack.final_title,
                content=writing_pack.final_content
            )
            chapter_id = chapter["_id"]

            # 若有重写，记录原始正文与重写原因。
            if rewrite_output:
                self.chapter_dao.set_rewrite_meta(
                    chapter_id=chapter_id,
                    reasons=rewrite_output.fail_reasons,
                    original_title=writing_output.chapter_title,
                    original_content=writing_output.content
                )
        except Exception:
            print("❌ 章节写入失败，终止后续流程")
            traceback.print_exc()
            return
        # ---------- 4️⃣ 章节评审 ----------
        try:
            for review_output in iter_review_outputs(task_outputs):
                self.review_dao.create(
                    novel_id=novel_id,
                    chapter_id=chapter_id,
                    overall_score=review_output.overall_score,
                    world_consistency_score=review_output.world_consistency_score,
                    off_topic=review_output.off_topic,
                    issues=review_output.issues,
                    summary=review_output.summary
                )
        except Exception:
            print("⚠️ 章节评审写入失败")
            traceback.print_exc()
        # ---------- 5️⃣ 剧情分析 ----------
        try:
            analysis_output = task_outputs["plot_analysis_task"].pydantic
            self.plot_dao.create(
                novel_id=novel_id,
                chapter_id=chapter_id,
                key_events=analysis_output.key_events,
                consequences=analysis_output.consequences
            )
        except Exception:
            print("⚠️ 剧情分析写入失败")
            traceback.print_exc()

        # ---------- 6️⃣ 人物状态 ----------
        try:
            memory_output = task_outputs["memory_update_task"].pydantic
            for s in memory_output.states:
                # 写入角色状态（若角色不存在则跳过）。
                persist_character_state(
                    mongo=self.mongo,
                    novel_id=novel_id,
                    chapter_id=chapter_id,
                    state={
                        "character_name": s.character_name,
                        "location": s.location,
                        "emotion": s.emotion,
                        "goal": s.goal,
                        "relationships": s.relationships
                    }
                )
        except Exception:
            print("⚠️ 人物状态写入失败")
            traceback.print_exc()

        # ---------- 7️⃣ Agent 日志（只用 raw） ----------
        for task_name, output in task_outputs.items():
            # 统一转为字符串，避免非字符串类型写入失败。
            text = (
                output.raw
                if isinstance(output.raw, str)
                else str(output.raw)
            )

            self.agent_log_dao.create(
                novel_id=novel_id,
                agent_name=task_name,
                input_summary="auto",
                output_summary=text[:2000]
            )
        return task_outputs
