from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)

from .base import Base


class DataLocationORM(Base):
    __tablename__ = "data_product_locations"

    id = Column(
        Integer,
        primary_key=True,
    )

    asset_id = Column(
        Integer,
        ForeignKey("data_products.asset_id"),
        nullable=False,
        index=True,
    )

    device_id = Column(
        Integer,
        ForeignKey("storage_devices.id"),
        nullable=False,
        index=True,
    )

    address = Column(
        String,
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "asset_id",
            "device_id",
            "address",
            name="uq_data_product_location",
        ),
    )
