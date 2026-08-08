from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .base import Base


class FieldORM(Base):
    __tablename__ = "dataset_fields"

    id = Column(Integer, primary_key=True)

    dataset_id = Column(
        Integer,
        ForeignKey("datasets.id"),
        nullable=False,
    )

    obs_space_id = Column(
        Integer,
        ForeignKey("obs_spaces.id"),
        nullable=False,
    )

    dataset = relationship(
        "DatasetORM",
        back_populates="fields",
    )

    obs_space = relationship(
        "ObsSpaceORM",
    )

    dataset_files = relationship(
        "DatasetFileORM",
        back_populates="dataset_field",
    )

    __table_args__ = (
        UniqueConstraint(
            "dataset_id",
            "obs_space_id",
            name="uq_dataset_obs_space",
        ),
    )
