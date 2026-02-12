"""小说相关接口：初始化、续写、流式输出、导出等。"""

from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.responses import StreamingResponse
from sqlmodel import Session
from official_proj.db.mysql_db.mysql import get_session
from official_proj.api.auth.deps import get_current_user_id
from official_proj.db.mysql_db.dao.novel_dao import NovelDAO
from official_proj.db.mongo_db.mongo import MongoDB
from official_proj.db.mongo_db.dao.chapter_dao import ChapterDAO
from official_proj.db.mongo_db.dao.plot_summary_dao import PlotSummaryDAO
from official_proj.db.mongo_db.dao.world_setting_dao import WorldSettingDAO
from official_proj.services.crew_persist_runner import CrewPersistRunner
from official_proj.services.chapter_loop_runner import ChapterLoopRunner
from official_proj.services.streaming_helpers import (
    ChapterJsonStreamParser,
    ndjson_line
)
from official_proj.utils.task_outputs import extract_writing, select_review
from official_proj.services.knowledge_cleanup import cleanup_generated_knowledge
from official_proj.crews.compete_crew import OfficialProj
from official_proj.crews.chapter_crew import ChapterCrew
from official_proj.services.chapter_persist_service import persist_chapter_result
from official_proj.api.schemas.novel import (
    InitNovelRequest,
    NextChapterRequest,
    ChapterResponse,
    InitResponse
)
from official_proj.api.schemas.common import ApiResponse, success


# 路由注册：统一 /novel 前缀。
router = APIRouter(prefix="/novel", tags=["Novel"])

# 共享的数据库与服务实例（路由级别单例）。
mongo = MongoDB()
init_runner = CrewPersistRunner(mongo)
chapter_runner = ChapterLoopRunner(mongo)
chapter_dao = ChapterDAO(mongo)
world_dao = WorldSettingDAO(mongo)
plot_dao = PlotSummaryDAO(mongo)


def _chunk_text(chunk) -> str:
    """从流式 chunk 中尽量提取文本字段。"""
    for attr in ("content", "delta", "text", "chunk", "raw"):
        value = getattr(chunk, attr, None)
        if not value:
            continue
        if isinstance(value, bytes):
            try:
                return value.decode("utf-8")
            except Exception:
                continue
        if isinstance(value, dict):
            for key in ("content", "text", "delta"):
                inner = value.get(key)
                if isinstance(inner, str) and inner:
                    return inner
            continue
        if isinstance(value, str):
            return value
    return ""


def _task_outputs_from_result(result, fallback_tasks: list | None = None) -> dict:
    """从 crew 结果中构建 task_outputs 字典（带回退逻辑）。"""
    task_outputs: dict = {}
    if result is not None and getattr(result, "tasks_output", None):
        for output in result.tasks_output:
            name = getattr(output, "name", None)
            if name:
                task_outputs[name] = output
    if not task_outputs and fallback_tasks:
        task_outputs = {
            task.name: task.output
            for task in fallback_tasks
            if task.name and task.output is not None
        }
    return task_outputs


def _stream_content_chunks(content: str, chunk_size: int = 200):
    """将完整正文切成小块，用于流式回传。"""
    for idx in range(0, len(content), chunk_size):
        yield content[idx : idx + chunk_size]

@router.post("/init", response_model=ApiResponse[InitResponse])
def init_novel(
    req: InitNovelRequest,
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """初始化小说：创建 MySQL 记录、生成世界观/人物/首章并落库。"""
    # 当前请求的数据库会话（MySQL）。
    novel_dao = NovelDAO(session)
    novel = novel_dao.get(req.novel_id)

    # 1️⃣ novel 不存在 → 创建
    if not novel:
        novel = novel_dao.create(
            novel_id=req.novel_id,
            topic=req.topic,
            user_id=user_id
        )
    else:
        # 2️⃣ 存在但不是本人 → 禁止
        if novel.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权初始化该小说")

    # 3️⃣ Mongo：已经初始化过 → 幂等返回
    if mongo.db.world_settings.find_one({"novel_id": req.novel_id}):
        return success(
            data={"novel_id": req.novel_id},
            msg="小说已初始化"
        )

    # 4️⃣ 真正初始化（只会执行一次）
    task_outputs=init_runner.run({
        "novel_id": req.novel_id,
        "topic": req.topic
    })
    # 提取最终正文、评审与世界观结果。
    writing_pack = extract_writing(task_outputs)
    world_settings = task_outputs["world_building_task"].pydantic
    final_review = select_review(task_outputs)
    data= InitResponse(
        novel_id=req.novel_id,
        chapter_number=1,
        title=writing_pack.final_title,
        content=writing_pack.final_content,
        world_rules=world_settings.world_rules,
        review=final_review.dict()
        if final_review else None,
        rewrite=writing_pack.rewrite_info
    )

    return success(
        data=data,
        msg="小说初始化完成"
    )

@router.post(
    "/next_chapter",
    response_model=ApiResponse[ChapterResponse]
)
def generate_next_chapter(
    req: NextChapterRequest,
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """生成下一章（非流式）：写作→评审→返回结果。"""
    novel_dao = NovelDAO(session)

    # 🚨 权限判断（HTTP 层）
    if not novel_dao.get_by_user(req.novel_id, user_id):
        raise HTTPException(
            status_code=403,
            detail="无权操作该小说"
        )

    # 业务执行：调用章节生成流程。
    task_outputs = chapter_runner.run_one_chapter(req.novel_id)
    writing_pack = extract_writing(task_outputs)
    final_review = select_review(task_outputs)

    last_chapter = mongo.db.chapters.find_one(
        {"novel_id": req.novel_id},
        sort=[("chapter_number", -1)]
    )

    data = ChapterResponse(
        novel_id=req.novel_id,
        chapter_number=last_chapter["chapter_number"],
        title=writing_pack.final_title,
        content=writing_pack.final_content,
        review=final_review.dict()
        if final_review else None,
        rewrite=writing_pack.rewrite_info
    )
    return success(
        data=data,
        msg="生成下一章节成功"
    )


@router.post("/init_stream")
def init_novel_stream(
    req: InitNovelRequest,
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """初始化小说（流式）：边生成边输出标题与正文增量。"""
    novel_dao = NovelDAO(session)
    novel = novel_dao.get(req.novel_id)

    if not novel:
        novel = novel_dao.create(
            novel_id=req.novel_id,
            topic=req.topic,
            user_id=user_id
        )
    else:
        if novel.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权初始化该小说")

    # 已初始化则直接返回 final。
    if mongo.db.world_settings.find_one({"novel_id": req.novel_id}):
        def already_init():
            yield ndjson_line(
                {"type": "final", "data": {"novel_id": req.novel_id}}
            )
        return StreamingResponse(
            already_init(),
            media_type="application/x-ndjson"
        )

    inputs = {
        "novel_id": req.novel_id,
        "topic": req.topic
    }

    def stream():
        """流式生成器：输出 progress / title / content_delta / final。"""
        crew = OfficialProj().crew()
        crew.stream = True
        parser = ChapterJsonStreamParser()
        rewrite_parser = ChapterJsonStreamParser()
        seen_tasks: set[str] = set()
        draft_started = False
        rewrite_started = False
        rewrite_mode = False
        sent_delta = False

        try:
            streaming = crew.kickoff(inputs=inputs)
            for chunk in streaming:
                # 发送进度：每个任务只发一次。
                task_name = getattr(chunk, "task_name", "") or ""
                agent_role = getattr(chunk, "agent_role", "") or ""
                if task_name and task_name not in seen_tasks:
                    seen_tasks.add(task_name)
                    yield ndjson_line({"type": "progress", "task": task_name})

                # 提取文本片段，无法解析则跳过。
                text = _chunk_text(chunk)
                if not text:
                    continue

                # 发现重写任务或 fail_reasons 则进入重写模式。
                if task_name == "chapter_rewrite_task" or '"fail_reasons"' in text:
                    rewrite_mode = True

                if not rewrite_mode:
                    # 普通写作模式：解析标题与正文增量。
                    is_writing = (
                        task_name == "writing_task"
                        or agent_role == "专业小说写手"
                        or not draft_started
                    )
                    if is_writing:
                        title, delta = parser.feed(text)
                        if (title or delta) and not draft_started:
                            draft_started = True
                            yield ndjson_line({"type": "draft_start"})
                        if title:
                            yield ndjson_line({"type": "title", "data": title})
                        if delta:
                            sent_delta = True
                            yield ndjson_line({"type": "content_delta", "data": delta})

                if rewrite_mode:
                    # 重写模式：解析重写后的标题与正文增量。
                    title, delta = rewrite_parser.feed(text)
                    if (title or delta) and not rewrite_started:
                        rewrite_started = True
                        yield ndjson_line({"type": "rewrite_start"})
                    if title:
                        yield ndjson_line({"type": "title", "data": title})
                    if delta:
                        sent_delta = True
                        yield ndjson_line({"type": "content_delta", "data": delta})

            # 生成完成后，从结果中抽取 task_outputs 并持久化。
            result = streaming.result
            task_outputs = _task_outputs_from_result(result, crew.tasks)
            init_runner.persist_outputs(inputs, task_outputs)

            # 组装最终返回数据。
            writing_pack = extract_writing(task_outputs)
            world_settings = task_outputs["world_building_task"].pydantic
            review_output = select_review(task_outputs)

            if not sent_delta:
                # 若没有任何增量输出，则补发完整内容。
                writing_output = writing_pack.writing_output
                rewrite_output = writing_pack.rewrite_output
                if not draft_started:
                    draft_started = True
                    yield ndjson_line({"type": "draft_start"})
                if writing_output.chapter_title:
                    yield ndjson_line({"type": "title", "data": writing_output.chapter_title})
                for piece in _stream_content_chunks(writing_output.content or ""):
                    yield ndjson_line({"type": "content_delta", "data": piece})
                if rewrite_output:
                    yield ndjson_line({"type": "rewrite_start"})
                    if rewrite_output.chapter_title:
                        yield ndjson_line({"type": "title", "data": rewrite_output.chapter_title})
                    for piece in _stream_content_chunks(rewrite_output.content or ""):
                        yield ndjson_line({"type": "content_delta", "data": piece})

            # 最终响应：包含标题/正文/评审/重写信息。
            data = InitResponse(
                novel_id=req.novel_id,
                chapter_number=1,
                title=writing_pack.final_title,
                content=writing_pack.final_content,
                world_rules=world_settings.world_rules,
                review=review_output.dict()
                if review_output else None,
                rewrite=writing_pack.rewrite_info
            )
            yield ndjson_line({"type": "final", "data": data.dict()})
        except Exception as e:
            # 捕获异常并以流式错误返回。
            yield ndjson_line({"type": "error", "message": str(e)})
        finally:
            # 清理由 crew 生成的知识文件。
            cleanup_generated_knowledge()

    return StreamingResponse(stream(), media_type="application/x-ndjson")


@router.post("/next_chapter_stream")
def next_chapter_stream(
    req: NextChapterRequest,
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """生成下一章（流式）：边生成边返回正文增量。"""
    novel_dao = NovelDAO(session)

    if not novel_dao.get_by_user(req.novel_id, user_id):
        raise HTTPException(
            status_code=403,
            detail="无权操作该小说"
        )

    # 推算下一章的章节号。
    last = chapter_dao.get_last_chapter(req.novel_id)
    chapter_number = 1 if not last else last["chapter_number"] + 1

    # 世界观必须存在，否则无法生成续章。
    world = world_dao.get_latest(req.novel_id)
    if not world:
        raise HTTPException(status_code=400, detail="世界观未初始化")

    # 拉取最近剧情摘要，作为续写上下文。
    last_plot_doc = plot_dao.list_recent(req.novel_id, limit=1)
    last_plot = (
        last_plot_doc[0]["key_events"]
        if last_plot_doc else []
    )

    inputs = {
        "novel_id": req.novel_id,
        "chapter_number": chapter_number,
        "world": world,
        "last_plot": last_plot,
    }

    def stream():
        """流式生成器：progress / title / content_delta / final。"""
        crew = ChapterCrew().crew()
        crew.stream = True
        parser = ChapterJsonStreamParser()
        rewrite_parser = ChapterJsonStreamParser()
        seen_tasks: set[str] = set()
        draft_started = False
        rewrite_started = False
        rewrite_mode = False
        sent_delta = False

        try:
            streaming = crew.kickoff(inputs=inputs)
            for chunk in streaming:
                # 发送进度：每个任务只发一次。
                task_name = getattr(chunk, "task_name", "") or ""
                agent_role = getattr(chunk, "agent_role", "") or ""
                if task_name and task_name not in seen_tasks:
                    seen_tasks.add(task_name)
                    yield ndjson_line({"type": "progress", "task": task_name})

                # 提取可读文本内容。
                text = _chunk_text(chunk)
                if not text:
                    continue

                # 识别是否进入重写阶段。
                if task_name == "chapter_rewrite_task" or '"fail_reasons"' in text:
                    rewrite_mode = True

                if not rewrite_mode:
                    # 普通写作：解析标题与正文增量。
                    is_writing = (
                        task_name == "writing_task"
                        or agent_role == "专业小说写手"
                        or not draft_started
                    )
                    if is_writing:
                        title, delta = parser.feed(text)
                        if (title or delta) and not draft_started:
                            draft_started = True
                            yield ndjson_line({"type": "draft_start"})
                        if title:
                            yield ndjson_line({"type": "title", "data": title})
                        if delta:
                            sent_delta = True
                            yield ndjson_line({"type": "content_delta", "data": delta})

                if rewrite_mode:
                    # 重写阶段：解析重写后的标题与正文增量。
                    title, delta = rewrite_parser.feed(text)
                    if (title or delta) and not rewrite_started:
                        rewrite_started = True
                        yield ndjson_line({"type": "rewrite_start"})
                    if title:
                        yield ndjson_line({"type": "title", "data": title})
                    if delta:
                        sent_delta = True
                        yield ndjson_line({"type": "content_delta", "data": delta})

            # 生成完成后持久化章节内容与评审。
            result = streaming.result
            task_outputs = _task_outputs_from_result(result, crew.tasks)
            persist_chapter_result(
                mongo=mongo,
                novel_id=req.novel_id,
                chapter_number=chapter_number,
                task_outputs=task_outputs
            )

            # 组装最终响应。
            writing_pack = extract_writing(task_outputs)
            review_output = select_review(task_outputs)

            if not sent_delta:
                # 若没有输出增量，则补发完整正文。
                writing_output = writing_pack.writing_output
                rewrite_output = writing_pack.rewrite_output
                if not draft_started:
                    draft_started = True
                    yield ndjson_line({"type": "draft_start"})
                if writing_output.chapter_title:
                    yield ndjson_line({"type": "title", "data": writing_output.chapter_title})
                for piece in _stream_content_chunks(writing_output.content or ""):
                    yield ndjson_line({"type": "content_delta", "data": piece})
                if rewrite_output:
                    yield ndjson_line({"type": "rewrite_start"})
                    if rewrite_output.chapter_title:
                        yield ndjson_line({"type": "title", "data": rewrite_output.chapter_title})
                    for piece in _stream_content_chunks(rewrite_output.content or ""):
                        yield ndjson_line({"type": "content_delta", "data": piece})

            # 发送最终结果（包含评审与重写信息）。
            data = ChapterResponse(
                novel_id=req.novel_id,
                chapter_number=chapter_number,
                title=writing_pack.final_title,
                content=writing_pack.final_content,
                review=review_output.dict()
                if review_output else None,
                rewrite=writing_pack.rewrite_info
            )
            yield ndjson_line({"type": "final", "data": data.dict()})
        except Exception as e:
            # 异常转为流式错误消息。
            yield ndjson_line({"type": "error", "message": str(e)})
        finally:
            # 清理生成过程中的知识文件。
            cleanup_generated_knowledge()

    return StreamingResponse(stream(), media_type="application/x-ndjson")
@router.get(
    "/status/{novel_id}",
    response_model=ApiResponse[dict]
)
def novel_status(
    novel_id: str,
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """查询小说当前章节进度。"""
    novel_dao = NovelDAO(session)

    # 🚨 权限判断
    if not novel_dao.get_by_user(novel_id, user_id):
        raise HTTPException(
            status_code=403,
            detail="无权查看该小说"
        )

    # 取最新章节号，没有则返回 0。
    last = mongo.db.chapters.find_one(
        {"novel_id": novel_id},
        sort=[("chapter_number", -1)]
    )

    return success(
        data={
            "novel_id": novel_id,
            "current_chapter": last["chapter_number"] if last else 0
        }
    )

@router.get(
    "/list",
    response_model=ApiResponse[list[dict]]
)
def list_novels(
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """列出当前用户的小说列表。"""
    novel_dao = NovelDAO(session)
    novels = novel_dao.list_by_user(user_id)

    return success(
        data=[
            {
                "novel_id": n.novel_id,
                "topic": n.topic
            }
            for n in novels
        ]
    )


@router.get("/export/{novel_id}")
def export_novel(
    novel_id: str,
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """导出小说为纯文本。"""
    novel_dao = NovelDAO(session)

    # 🚨 权限判断
    novel = novel_dao.get_by_user(novel_id, user_id)
    if not novel:
        raise HTTPException(
            status_code=403,
            detail="无权操作该小说"
        )

    # 拉取世界观与章节内容（MongoDB）。
    world = world_dao.get_latest_full(novel_id) or {}
    chapters = chapter_dao.list_by_novel(novel_id)

    # 组装文本内容。
    lines: list[str] = []
    lines.append(f"小说ID: {novel_id}")
    if novel.topic:
        lines.append(f"主题: {novel.topic}")
    lines.append("")
    lines.append("世界观设定")
    tone = world.get("tone")
    tech = world.get("technology_level")
    if tone:
        lines.append(f"基调: {tone}")
    if tech:
        lines.append(f"科技/文明水平: {tech}")
    lines.append("世界规则:")
    world_rules = world.get("world_rules") or []
    if world_rules:
        for rule in world_rules:
            lines.append(f"- {rule}")
    else:
        lines.append("- （无）")

    lines.append("")
    lines.append("章节正文")
    if not chapters:
        lines.append("（暂无章节）")
    for ch in chapters:
        lines.append(f"第 {ch.get('chapter_number')} 章 · {ch.get('title')}")
        content = ch.get("content") or ""
        lines.append(content)
        lines.append("")

    content = "\n".join(lines)
    filename = f"novel_{novel_id}.txt"
    return Response(
        content=content,
        media_type="text/plain; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )
