"""LLM 工厂：根据环境变量返回默认模型实例。"""

from __future__ import annotations

import os

from crewai.llm import LLM

from official_proj.services.streaming_openai import DashScopeOpenAICompletion


def _is_dashscope(base_url: str | None) -> bool:
    """判断 base_url 是否为 DashScope 兼容接口。"""
    if not base_url:
        return False
    return "dashscope.aliyuncs.com" in base_url.lower()


def get_default_llm():
    """获取默认 LLM 实例，优先根据环境变量配置。"""
    # 读取模型与 OpenAI 兼容配置。
    model = os.getenv("MODEL") or "gpt-4o-mini"
    base_url = os.getenv("OPENAI_API_BASE") or os.getenv("OPENAI_BASE_URL")
    api_key = os.getenv("OPENAI_API_KEY")

    # DashScope 走自定义的流式兼容实现。
    if _is_dashscope(base_url):
        return DashScopeOpenAICompletion(
            model=model,
            api_key=api_key,
            base_url=base_url,
        )

    # 其余兼容 OpenAI 的基类实现。
    return LLM(
        model=model,
        api_key=api_key,
        base_url=base_url,
    )
