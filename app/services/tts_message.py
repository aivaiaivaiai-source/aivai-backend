from __future__ import annotations

import re

MAX_TTS_MESSAGE_LENGTH = 400

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?…])\s+")


def prepare_tts_message(message: str, *, max_length: int = MAX_TTS_MESSAGE_LENGTH) -> str:
    """Short, calm TTS text — no long descriptions or preview dumps."""
    text = " ".join(message.split())
    if not text:
        return ""

    if len(text) <= max_length:
        return text

    sentences = _SENTENCE_SPLIT.split(text)
    if len(sentences) >= 2:
        first = sentences[0].strip()
        second = sentences[1].strip()
        short = f"{first} {second}".strip()
        if len(short) <= max_length:
            return short

    clipped = text[: max_length - 1].rstrip()
    if " " in clipped:
        clipped = clipped.rsplit(" ", 1)[0]
    return f"{clipped}."
