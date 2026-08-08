from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .base import Base


class CycleORM(Base):
    __tablename__ = "dataset_cycles"

    id = Column(Integer, primary_key=True)

    dataset_id = Column(
        Integer,
        ForeignKey("datasets.id"),
        nullable=False,
    )

    cycle_date = Column(Date, nullable=False)
    cycle_hour = Column(String, nullable=False)

    dataset = relationship(
        "DatasetORM",
        back_populates="cycles",
    )

    dataset_files = relationship(
        "DatasetFileORM",
        back_populates="dataset_cycle",
    )

    __table_args__ = (
        UniqueConstraint(
            "dataset_id",
            "cycle_date",
            "cycle_hour",
            name="uq_dataset_cycle",
        ),
    )
