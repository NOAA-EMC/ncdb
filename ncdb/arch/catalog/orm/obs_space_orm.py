from sqlalchemy import Column, Integer, String

from .base import Base


class ObsSpaceORM(Base):
    __tablename__ = "obs_spaces"

    id = Column(Integer, primary_key=True)

    name = Column(
        String,
        nullable=False,
        unique=True,
    )

    description = Column(
        String,
        nullable=True,
    )
