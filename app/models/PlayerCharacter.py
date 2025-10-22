from typing import Literal
from pydantic import BaseModel, Field


class CharacterStats(BaseModel):
    """Character stat info"""

    strength: int = Field(..., description="Physical power, affects melee damage")
    dexterity: int = Field(..., description="Agility and reflexes")
    constitution: int = Field(..., description="Endurance and health")
    intelligence: int = Field(..., description="Reasoning and knowledge")
    charisma: int = Field(..., description="Charm and social ability")
    wisdom: int = Field(..., description="Perception and intuition")


class Item(BaseModel):
    """Item info. If data is unknown, keep it as None."""

    name: str = Field(
        ...,
        min_length=1,
        description="Name of the item. If item is currency, name should contain only the currency name (e.g. 'gold', 'silver').",
    )
    type: Literal["weapon", "armor", "potion", "tool", "money"] = Field(
        ..., description="Category of the item"
    )
    weight: float | None = Field(None, ge=0, description="Weight in kilograms")
    value: int | None = Field(None, ge=0, description="Monetary value")


class PlayerCharacter(BaseModel):
    """Character general info"""

    name: str = Field(..., description="Character's name")
    race: str = Field(..., description="Character's race")
    level: int = Field(..., description="Character's current level")
    stat: CharacterStats = Field(..., description="Chracter's stats")
    inventory: list[Item] = Field(..., description="Character's item list")
