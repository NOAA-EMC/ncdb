from sqlalchemy import Column, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from .base import Base


class DatasetORM(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    root_dir = Column(String, nullable=False)

    cycles = relationship(
        "CycleORM",
        back_populates="dataset",
    )

    fields = relationship(
        "FieldORM",
        back_populates="dataset",
    )

    __table_args__ = (
        UniqueConstraint(
            "name",
            "root_dir",
            name="uq_dataset_name_root",
        ),
    )
