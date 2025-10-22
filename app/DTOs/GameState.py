from typing import TypedDict

from app.models.PlayerCharacter import PlayerCharacter


class ChatContent(TypedDict):
    role: str
    content: str


class GameState(TypedDict, total=False):
    chat_history: list[ChatContent]
    summary: str
    input: str
    players: list[PlayerCharacter]
    sys_msg: str
