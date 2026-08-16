from sqlalchemy import (
    Column,
    Integer,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from .base import Base


class FieldTimeORM(Base):
    __tablename__ = "field_times"

    id = Column(Integer, primary_key=True)

    field_id = Column(
        Integer,
        ForeignKey("fields.id"),
        nullable=False,
    )

    time = Column(
        DateTime,
        nullable=False,
    )

    data_product_id = Column(
        Integer,
        # ForeignKey("data_products.asset_id"),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "field_id",
            "time",
            name="uq_field_time",
        ),
    )
