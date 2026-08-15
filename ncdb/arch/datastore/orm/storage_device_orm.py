from sqlalchemy import Column, Integer, String, UniqueConstraint

from .base import Base


class StorageDeviceORM(Base):
    __tablename__ = "storage_devices"

    id = Column(
        Integer,
        primary_key=True,
    )

    name = Column(
        String,
        nullable=False,
        unique=True,
    )

    device_type = Column(
        String,
        nullable=False,
    )
