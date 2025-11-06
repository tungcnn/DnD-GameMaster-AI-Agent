from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

from app.models.PlayerCharacter import PlayerCharacter

class GameState(TypedDict, total=False):
    players: list[PlayerCharacter]
    messages: Annotated[list[BaseMessage], add_messages]
