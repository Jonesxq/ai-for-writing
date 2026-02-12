from official_proj.crews.chapter_crew import ChapterCrew
from official_proj.db.mongo_db.dao.chapter_dao import ChapterDAO
from official_proj.db.mongo_db.dao.character_state_dao import CharacterStateDAO
from official_proj.db.mongo_db.dao.plot_summary_dao import PlotSummaryDAO
from official_proj.db.mongo_db.dao.world_setting_dao import WorldSettingDAO
from official_proj.services.chapter_persist_service import persist_chapter_result
from official_proj.services.knowledge_cleanup import cleanup_generated_knowledge


class ChapterLoopRunner:

    def __init__(self, mongo):
        self.mongo = mongo
        self.chapter_dao = ChapterDAO(mongo)
        self.plot_dao = PlotSummaryDAO(mongo)
        self.state_dao = CharacterStateDAO(mongo)
        self.world_dao = WorldSettingDAO(mongo)

    def run_one_chapter(self, novel_id: str):
        # 1️⃣ 章节号
        last = self.chapter_dao.get_last_chapter(novel_id)
        chapter_number = 1 if not last else last["chapter_number"] + 1

        # 2️⃣ 世界观（只读）
        world = self.world_dao.get_latest(novel_id)
        if not world:
            raise RuntimeError("World not initialized")

        # 3️⃣ 上一章剧情（结构化）
        last_plot_doc = self.plot_dao.list_recent(novel_id, limit=1)
        last_plot = (
            last_plot_doc[0]["key_events"]
            if last_plot_doc else []
        )

        inputs = {
            "novel_id": novel_id,
            "chapter_number": chapter_number,
            "world": world,
            "last_plot": last_plot,
        }

        crew = ChapterCrew().crew()
        crew.kickoff(inputs=inputs)

        task_outputs = {
            task.name: task.output
            for task in crew.tasks
        }

        try:
            persist_chapter_result(
                mongo=self.mongo,
                novel_id=novel_id,
                chapter_number=chapter_number,
                task_outputs=task_outputs
            )
        except Exception:
            print("❌ Persist failed")
            raise
        finally:
            cleanup_generated_knowledge()

        return task_outputs
