# app/db/models.py
from __future__ import annotations
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text, UniqueConstraint

class Base(DeclarativeBase):
    pass

class Spell(Base):
    __tablename__ = "spells_min"
    __table_args__ = (UniqueConstraint("name", name="uq_spells_min_name"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    cast_class: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    effect_kind: Mapped[str] = mapped_column(String(8), nullable=False)
    damage: Mapped[str | None] = mapped_column(String(32), nullable=True)
    heal:   Mapped[str | None] = mapped_column(String(32), nullable=True)
