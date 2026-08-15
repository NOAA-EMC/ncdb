from sqlalchemy import Column, Integer
from .base import Base


class DataProductORM(Base):
    __tablename__ = "data_products"

    asset_id = Column(
        Integer,
        primary_key=True,
    )
