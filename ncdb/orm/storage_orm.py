from sqlalchemy import (
    Column,
    Integer,
    String,
)

from .base import Base


class StorageORM(Base):
    """
    Physical storage location/type.

    A Storage identifies where data is physically stored.
    Examples: local filesystem, database, HPSS, object storage, etc.
    """

    __tablename__ = "storages"

    id = Column(Integer, primary_key=True)

    type = Column(
        String,
        nullable=False,
    )

    name = Column(
        String,
        nullable=False,
        unique=True,
    )

    description = Column(
        String,
        nullable=True,
    )

    def __repr__(self):
        return (
            f"<StorageORM("
            f"id={self.id}, "
            f"name='{self.name}', "
            f"type='{self.type}')>"
        )
