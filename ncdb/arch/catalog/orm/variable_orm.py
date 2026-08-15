from sqlalchemy import Column, Integer, String

from .base import Base


class VariableORM(Base):
    __tablename__ = "variables"

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
