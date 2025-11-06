# app/models/Class.py
from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, UniqueConstraint
from app.models.Spell import Base


class Class(Base):
    """
    D&D Character Class model.
    Stores basic information about player character classes like Wizard, Cleric, etc.
    """
    __tablename__ = "classes"
    __table_args__ = (UniqueConstraint("name", name="uq_classes_name"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    index: Mapped[str] = mapped_column(String(64), nullable=False)
    health: Mapped[int] = mapped_column(Integer, nullable=False)  # Calculated as hit_die * 10

    def __repr__(self) -> str:
        return f"<Class(name='{self.name}', health={self.health})>"

