from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from .base import Base


class DataProductORM(Base):
    """
    A physically stored piece of data.

    A DataProduct describes the existence of stored data.
    Its scientific interpretation is modeled separately.
    """

    __tablename__ = "data_products"

    id = Column(Integer, primary_key=True)

    # name = Column(
        # String,
        # nullable=False,
    # )
# 
    # description = Column(
        # String,
        # nullable=True,
    # )

    storage_id = Column(
        Integer,
        ForeignKey("storages.id"),
        nullable=False,
    )

    storage = relationship(
        "StorageORM",
    )

    def __repr__(self):
        return (
            f"<DataProductORM("
            f"id={self.id}, "
            f"name='{self.name}')>"
        )
