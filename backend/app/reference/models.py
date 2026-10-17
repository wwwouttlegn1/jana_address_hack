from __future__ import annotations

import enum
from typing import Any

from sqlalchemy import Boolean, ForeignKey, Index, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.storage.database import Base


class ReferenceType(str, enum.Enum):
    country = "country"
    region = "region"
    province = "province"
    district = "district"
    city = "city"
    settlement = "settlement"
    living_area = "living_area"
    street = "street"


class AddressReference(Base):
    __tablename__ = "address_references"
    __table_args__ = (
        UniqueConstraint(
            "kind", "normalized_name", "parent_id", name="uq_reference_kind_name_parent"
        ),
        Index("ix_reference_kind_normalized", "kind", "normalized_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kind: Mapped[str] = mapped_column(String(30), index=True)
    name: Mapped[str] = mapped_column(String(255))
    normalized_name: Mapped[str] = mapped_column(String(255))
    code: Mapped[str | None] = mapped_column(String(100), unique=True)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("address_references.id", ondelete="SET NULL"), index=True
    )
    attributes: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    parent: Mapped[AddressReference | None] = relationship(
        remote_side="AddressReference.id", back_populates="children"
    )
    children: Mapped[list[AddressReference]] = relationship(back_populates="parent")
