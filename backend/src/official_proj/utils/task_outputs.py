from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterator


def _pydantic_output(output: Any) -> Any:
    """优先返回 pydantic 输出，否则返回原始输出对象。"""
    return getattr(output, "pydantic", output)


@dataclass(frozen=True)
class WritingExtraction:
    """写作相关输出的标准化结果集合。"""

    writing_output: Any
    rewrite_output: Any | None
    final_title: str
    final_content: str
    rewrite_info: dict | None


def extract_writing(task_outputs: dict) -> WritingExtraction:
    """从任务输出中提取最终标题/正文与重写信息。"""
    # 必须包含写作任务输出。
    writing_output = _pydantic_output(task_outputs["writing_task"])
    # 重写任务是可选的，依流程而定。
    rewrite_output = (
        _pydantic_output(task_outputs["chapter_rewrite_task"])
        if "chapter_rewrite_task" in task_outputs
        else None
    )
    # 若存在重写结果，优先使用重写内容。
    final_title = (
        rewrite_output.chapter_title
        if rewrite_output
        else writing_output.chapter_title
    )
    final_content = (
        rewrite_output.content
        if rewrite_output
        else writing_output.content
    )
    # 记录重写原因，便于在 API 响应中展示。
    rewrite_info = (
        {"reasons": rewrite_output.fail_reasons, "applied": True}
        if rewrite_output
        else None
    )
    return WritingExtraction(
        writing_output=writing_output,
        rewrite_output=rewrite_output,
        final_title=final_title,
        final_content=final_content,
        rewrite_info=rewrite_info
    )


def select_review(task_outputs: dict) -> Any | None:
    """返回优先级最高的评审结果（重写评审优先）。"""
    rewrite_review = (
        _pydantic_output(task_outputs["chapter_rewrite_review_task"])
        if "chapter_rewrite_review_task" in task_outputs
        else None
    )
    review_output = (
        _pydantic_output(task_outputs["chapter_review_task"])
        if "chapter_review_task" in task_outputs
        else None
    )
    return rewrite_review or review_output


def iter_review_outputs(task_outputs: dict) -> Iterator[Any]:
    """按固定顺序输出所有可用的评审结果。"""
    for key in ("chapter_review_task", "chapter_rewrite_review_task"):
        if key not in task_outputs:
            continue
        output = _pydantic_output(task_outputs[key])
        if output:
            yield output
