from __future__ import annotations

import json
import logging
import os
from typing import Any

from openai import Stream
from openai.types.chat import ChatCompletionChunk
from openai.types.chat.chat_completion_chunk import ChoiceDelta
from pydantic import BaseModel

from crewai.events.types.llm_events import LLMCallType
from crewai.llms.providers.openai.completion import OpenAICompletion
from crewai.utilities.agent_utils import is_context_length_exceeded
from crewai.utilities.exceptions.context_window_exceeding_exception import (
    LLMContextLengthExceededError,
)


class DashScopeOpenAICompletion(OpenAICompletion):
    """OpenAICompletion override that uses standard streaming for DashScope."""

    def _is_dashscope(self) -> bool:
        base = (
            self.base_url
            or self.api_base
            or os.getenv("OPENAI_API_BASE")
            or os.getenv("OPENAI_BASE_URL")
            or ""
        )
        return "dashscope.aliyuncs.com" in base.lower()

    def _prepare_completion_params(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None
    ) -> dict[str, Any]:
        params = super()._prepare_completion_params(messages, tools)
        if self.stream and self._is_dashscope():
            params.pop("stream_options", None)
            params.pop("response_format", None)
        return params

    def _handle_streaming_completion(
        self,
        params: dict[str, Any],
        available_functions: dict[str, Any] | None = None,
        from_task: Any | None = None,
        from_agent: Any | None = None,
        response_model: type[BaseModel] | None = None,
    ) -> str:
        """Handle streaming chat completion with standard stream API."""
        try:
            full_response = ""
            tool_calls: dict[int, dict[str, Any]] = {}

            completion_stream: Stream[ChatCompletionChunk] = (
                self.client.chat.completions.create(**params)
            )

            usage_data = {"total_tokens": 0}

            for completion_chunk in completion_stream:
                if hasattr(completion_chunk, "usage") and completion_chunk.usage:
                    usage_data = self._extract_openai_token_usage(completion_chunk)
                    continue

                if not completion_chunk.choices:
                    continue

                choice = completion_chunk.choices[0]
                chunk_delta: ChoiceDelta = choice.delta

                if chunk_delta.content:
                    full_response += chunk_delta.content
                    self._emit_stream_chunk_event(
                        chunk=chunk_delta.content,
                        from_task=from_task,
                        from_agent=from_agent,
                    )

                if chunk_delta.tool_calls:
                    for tool_call in chunk_delta.tool_calls:
                        tool_index = tool_call.index if tool_call.index is not None else 0
                        if tool_index not in tool_calls:
                            tool_calls[tool_index] = {
                                "id": tool_call.id,
                                "name": "",
                                "arguments": "",
                                "index": tool_index,
                            }
                        elif tool_call.id and not tool_calls[tool_index]["id"]:
                            tool_calls[tool_index]["id"] = tool_call.id

                        if tool_call.function and tool_call.function.name:
                            tool_calls[tool_index]["name"] = tool_call.function.name
                        if tool_call.function and tool_call.function.arguments:
                            tool_calls[tool_index]["arguments"] += (
                                tool_call.function.arguments
                            )

                        self._emit_stream_chunk_event(
                            chunk=tool_call.function.arguments
                            if tool_call.function and tool_call.function.arguments
                            else "",
                            from_task=from_task,
                            from_agent=from_agent,
                            tool_call={
                                "id": tool_calls[tool_index]["id"],
                                "function": {
                                    "name": tool_calls[tool_index]["name"],
                                    "arguments": tool_calls[tool_index]["arguments"],
                                },
                                "type": "function",
                                "index": tool_calls[tool_index]["index"],
                            },
                            call_type=LLMCallType.TOOL_CALL,
                        )

            self._track_token_usage_internal(usage_data)

            if tool_calls and available_functions:
                for call_data in tool_calls.values():
                    function_name = call_data["name"]
                    arguments = call_data["arguments"]

                    if not function_name or not arguments:
                        continue

                    if function_name not in available_functions:
                        logging.warning(
                            f"Function '{function_name}' not found in available functions"
                        )
                        continue

                    try:
                        function_args = json.loads(arguments)
                    except json.JSONDecodeError as e:
                        logging.error(f"Failed to parse streamed tool arguments: {e}")
                        continue

                    result = self._handle_tool_execution(
                        function_name=function_name,
                        function_args=function_args,
                        available_functions=available_functions,
                        from_task=from_task,
                        from_agent=from_agent,
                    )

                    if result is not None:
                        return result

            full_response = self._apply_stop_words(full_response)

            if response_model:
                try:
                    parsed_object = response_model.model_validate_json(full_response)
                    structured_json = parsed_object.model_dump_json()
                    self._emit_call_completed_event(
                        response=structured_json,
                        call_type=LLMCallType.LLM_CALL,
                        from_task=from_task,
                        from_agent=from_agent,
                        messages=params["messages"],
                    )
                    return structured_json
                except Exception as e:
                    logging.error(
                        f"Failed to parse structured output from stream: {e}"
                    )

            self._emit_call_completed_event(
                response=full_response,
                call_type=LLMCallType.LLM_CALL,
                from_task=from_task,
                from_agent=from_agent,
                messages=params["messages"],
            )

            return self._invoke_after_llm_call_hooks(
                params["messages"], full_response, from_agent
            )
        except Exception as e:
            if is_context_length_exceeded(e):
                logging.error(f"Context window exceeded: {e}")
                raise LLMContextLengthExceededError(str(e)) from e

            error_msg = f"OpenAI API call failed: {e!s}"
            logging.error(error_msg)
            self._emit_call_failed_event(
                error=error_msg, from_task=from_task, from_agent=from_agent
            )
            raise
