from typing import Any, TypedDict


class ChatContent(TypedDict):
    role: str
    content: str


class GameState(TypedDict, total=False):
    chat_history: list[ChatContent]
    top_k_messages: int
    summary: str
    input: str
