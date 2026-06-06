from __future__ import annotations

from sqlalchemy import Boolean, Enum as SQLEnum, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.locale import DEFAULT_LOCALE
from app.db.base_class import Base, TimestampMixin
from app.models.category_enums import VehicleAliasTarget, VehicleType


class VehicleBrand(Base, TimestampMixin):
    __tablename__ = "vehicle_brands"
    __table_args__ = (UniqueConstraint("slug", name="uq_vehicle_brands_slug"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    country_origin: Mapped[str | None] = mapped_column(String(64), nullable=True)
    vehicle_type: Mapped[VehicleType] = mapped_column(
        SQLEnum(VehicleType, name="vehicle_type_enum"),
        nullable=False,
        default=VehicleType.car,
        index=True,
    )
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    models: Mapped[list[VehicleModel]] = relationship(
        "VehicleModel",
        back_populates="brand",
        lazy="select",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    aliases: Mapped[list[VehicleAlias]] = relationship(
        "VehicleAlias",
        back_populates="brand",
        lazy="select",
        foreign_keys="VehicleAlias.brand_id",
        passive_deletes=True,
    )


class VehicleModel(Base, TimestampMixin):
    __tablename__ = "vehicle_models"
    __table_args__ = (
        UniqueConstraint("brand_id", "slug", name="uq_vehicle_models_brand_slug"),
        Index("ix_vehicle_models_brand_slug", "brand_id", "slug"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    brand_id: Mapped[int] = mapped_column(
        ForeignKey("vehicle_brands.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(160), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    brand: Mapped[VehicleBrand] = relationship("VehicleBrand", back_populates="models")
    aliases: Mapped[list[VehicleAlias]] = relationship(
        "VehicleAlias",
        back_populates="model",
        lazy="select",
        foreign_keys="VehicleAlias.model_id",
        passive_deletes=True,
    )


class VehicleAlias(Base, TimestampMixin):
    __tablename__ = "vehicle_aliases"
    __table_args__ = (
        UniqueConstraint(
            "alias_compact",
            "locale",
            name="uq_vehicle_aliases_compact_locale",
        ),
        Index("ix_vehicle_aliases_normalized_locale", "alias_normalized", "locale"),
        Index("ix_vehicle_aliases_enabled", "is_enabled"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    alias: Mapped[str] = mapped_column(String(120), nullable=False)
    alias_normalized: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    alias_compact: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    target_type: Mapped[VehicleAliasTarget] = mapped_column(
        SQLEnum(VehicleAliasTarget, name="vehicle_alias_target_enum"),
        nullable=False,
    )
    brand_id: Mapped[int | None] = mapped_column(
        ForeignKey("vehicle_brands.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    model_id: Mapped[int | None] = mapped_column(
        ForeignKey("vehicle_models.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    locale: Mapped[str] = mapped_column(String(8), nullable=False, default=DEFAULT_LOCALE.value)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    brand: Mapped[VehicleBrand | None] = relationship(
        "VehicleBrand",
        back_populates="aliases",
        foreign_keys=[brand_id],
    )
    model: Mapped[VehicleModel | None] = relationship(
        "VehicleModel",
        back_populates="aliases",
        foreign_keys=[model_id],
    )
