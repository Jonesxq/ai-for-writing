"""章节结果持久化服务：将任务输出写入 MongoDB."""

from official_proj.db.mongo_db.dao.chapter_dao import ChapterDAO
from official_proj.db.mongo_db.dao.character_state_dao import CharacterStateDAO
from official_proj.db.mongo_db.dao.plot_summary_dao import PlotSummaryDAO
from official_proj.db.mongo_db.dao.chapter_review_dao import ChapterReviewDAO
from official_proj.services.character_state_persist_service import persist_character_state
from official_proj.utils.task_outputs import extract_writing, iter_review_outputs


def persist_chapter_result(
    mongo,
    novel_id: str,
    chapter_number: int,
    task_outputs: dict
):
    """将一章的任务输出统一落库（章节、剧情、人物状态、评审）。"""
    # 初始化 DAO，复用同一 MongoDB 连接。
    chapter_dao = ChapterDAO(mongo)
    plot_dao = PlotSummaryDAO(mongo)
    state_dao = CharacterStateDAO(mongo)
    review_dao = ChapterReviewDAO(mongo)

    # print("🧪 task_outputs keys:", task_outputs.keys())
    #
    # for name, output in task_outputs.items():
    #     print(f"\n--- {name} ---")
    #     print("raw:", output.raw)
    #     print("pydantic:", output.pydantic)

    # ---------- 章节 ----------
    # 抽取最终正文与重写信息（重写优先）。
    writing_pack = extract_writing(task_outputs)
    writing = writing_pack.writing_output
    rewrite_output = writing_pack.rewrite_output

    chapter = chapter_dao.create(
        novel_id=novel_id,
        chapter_number=chapter_number,
        title=writing_pack.final_title,
        content=writing_pack.final_content
    )
    chapter_id = chapter["_id"]

    # 有重写时记录原始内容与重写原因，便于回溯。
    if rewrite_output:
        chapter_dao.set_rewrite_meta(
            chapter_id=chapter_id,
            reasons=rewrite_output.fail_reasons,
            original_title=writing.chapter_title,
            original_content=writing.content
        )

    # ---------- 剧情分析 ----------
    # 可选任务：剧情分析可能不存在。
    if "plot_analysis_task" in task_outputs:
        analysis = task_outputs["plot_analysis_task"].pydantic
        plot_dao.create(
            novel_id=novel_id,
            chapter_id=chapter_id,
            key_events=analysis.key_events,
            consequences=analysis.consequences
        )

    # ---------- 人物状态 ----------
    # 可选任务：人物状态更新可能不存在。
    if "memory_update_task" in task_outputs:
        memory = task_outputs["memory_update_task"].pydantic
        for s in memory.states:
            # 逐个角色状态写入，内部会校验角色是否存在。
            persist_character_state(
                mongo=mongo,
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

    # ---------- 章节评审 ----------
    # 按顺序写入普通评审与重写评审（如存在）。
    for review in iter_review_outputs(task_outputs):
        review_dao.create(
            novel_id=novel_id,
            chapter_id=chapter_id,
            overall_score=review.overall_score,
            world_consistency_score=review.world_consistency_score,
            off_topic=review.off_topic,
            issues=review.issues,
            summary=review.summary
        )
