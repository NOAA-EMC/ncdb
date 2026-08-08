from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .base import Base
from .file_orm import FileORM


class DatasetFileORM(Base):
    __tablename__ = "dataset_files"

    id = Column(Integer, primary_key=True)

    dataset_field_id = Column(
        Integer,
        ForeignKey("dataset_fields.id"),
        nullable=False,
    )

    dataset_cycle_id = Column(
        Integer,
        ForeignKey("dataset_cycles.id"),
        nullable=False,
    )

    file_id = Column(
        Integer,
        ForeignKey("files.id"),
        nullable=False,
    )

    dataset_field = relationship(
        "FieldORM",
        back_populates="dataset_files",
    )

    dataset_cycle = relationship(
        "CycleORM",
        back_populates="dataset_files",
    )

    file = relationship(FileORM)

    __table_args__ = (
        UniqueConstraint(
            "dataset_field_id",
            "dataset_cycle_id",
            name="uq_dataset_cycle_field",
        ),
    )
