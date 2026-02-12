"""清理 crew 运行时生成的知识文件。"""

from pathlib import Path


# 运行时会生成的 agent 知识文件清单。
_AGENT_KNOWLEDGE_FILES = (
    "story_planner.json",
    "world_builder.json",
    "character_architect.json",
    "narrative_writer.json",
    "plot_analyst.json",
    "memory_keeper.json",
    "chapter_reviewer.json",
)


def cleanup_generated_knowledge() -> None:
    """删除自动生成的 agent 知识文件（若存在）。"""
    # knowledge 目录位于项目根目录下。
    knowledge_dir = Path(__file__).resolve().parents[3] / "knowledge"
    if not knowledge_dir.exists():
        return
    for filename in _AGENT_KNOWLEDGE_FILES:
        try:
            target = knowledge_dir / filename
            if target.exists():
                target.unlink()
        except Exception:
            # 清理失败不阻塞主流程。
            continue
