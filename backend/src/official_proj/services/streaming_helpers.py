import json
from typing import Tuple


def ndjson_line(payload: dict) -> bytes:
    return (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")


class ChapterJsonStreamParser:
    def __init__(self) -> None:
        self._buffer = ""
        self._state = "search"
        self._pending_key: str | None = None
        self._current_key: str | None = None
        self._escape = False
        self._unicode_buffer: str | None = None
        self._title = ""
        self._title_emitted = False
        self._max_key_len = max(len('"chapter_title"'), len('"content"'))

    def reset(self) -> None:
        self._buffer = ""
        self._state = "search"
        self._pending_key = None
        self._current_key = None
        self._escape = False
        self._unicode_buffer = None
        self._title = ""
        self._title_emitted = False

    def feed(self, text: str) -> Tuple[str | None, str]:
        self._buffer += text
        title_out: str | None = None
        content_delta = ""
        i = 0

        while i < len(self._buffer):
            ch = self._buffer[i]

            if self._state == "capture":
                if self._unicode_buffer is not None:
                    if ch.lower() in "0123456789abcdef":
                        self._unicode_buffer += ch
                        if len(self._unicode_buffer) == 4:
                            try:
                                decoded = chr(int(self._unicode_buffer, 16))
                            except ValueError:
                                decoded = "\\u" + self._unicode_buffer
                            content_delta, title_out = self._append_char(
                                decoded, content_delta, title_out
                            )
                            self._unicode_buffer = None
                        i += 1
                        continue
                    else:
                        fallback = "\\u" + self._unicode_buffer + ch
                        content_delta, title_out = self._append_char(
                            fallback, content_delta, title_out
                        )
                        self._unicode_buffer = None
                        i += 1
                        continue

                if self._escape:
                    if ch == "u":
                        self._unicode_buffer = ""
                    else:
                        decoded = {
                            "n": "\n",
                            "r": "\r",
                            "t": "\t",
                            "b": "\b",
                            "f": "\f",
                            '"': '"',
                            "\\": "\\",
                            "/": "/",
                        }.get(ch, ch)
                        content_delta, title_out = self._append_char(
                            decoded, content_delta, title_out
                        )
                    self._escape = False
                    i += 1
                    continue

                if ch == "\\":
                    self._escape = True
                    i += 1
                    continue

                if ch == '"':
                    if self._current_key == "chapter_title" and not self._title_emitted:
                        title_out = self._title
                        self._title_emitted = True
                    self._state = "search"
                    self._current_key = None
                    i += 1
                    continue

                content_delta, title_out = self._append_char(
                    ch, content_delta, title_out
                )
                i += 1
                continue

            if self._state == "wait_value":
                if ch == '"':
                    self._state = "capture"
                    self._current_key = self._pending_key
                    self._pending_key = None
                i += 1
                continue

            if self._buffer.startswith('"chapter_title"', i):
                self._pending_key = "chapter_title"
                self._state = "wait_value"
                i += len('"chapter_title"')
                continue

            if self._buffer.startswith('"content"', i):
                self._pending_key = "content"
                self._state = "wait_value"
                i += len('"content"')
                continue

            i += 1

        if self._state == "search":
            if len(self._buffer) > self._max_key_len:
                self._buffer = self._buffer[-self._max_key_len :]
        else:
            self._buffer = ""

        return title_out, content_delta

    def _append_char(
        self,
        ch: str,
        content_delta: str,
        title_out: str | None
    ) -> Tuple[str, str | None]:
        if self._current_key == "chapter_title":
            self._title += ch
        elif self._current_key == "content":
            content_delta += ch
        return content_delta, title_out
