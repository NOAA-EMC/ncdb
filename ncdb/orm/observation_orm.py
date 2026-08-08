from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .base import Base


# ObsSpaceORM will be defined here

class VariableORM(Base):
    """
    Logical variable belonging to an ObsSpace.

    This represents the scientific/logical identity of a variable,
    independent of how it is physically stored.
    """

    __tablename__ = "variables"

    id = Column(Integer, primary_key=True)

    obs_space_id = Column(
        Integer,
        ForeignKey("obs_spaces.id"),
        nullable=False,
    )

    name = Column(
        String,
        nullable=False,
    )

    description = Column(
        String,
        nullable=True,
    )

    obs_space = relationship(
        "ObsSpaceORM",
    )

    data_product_variables = relationship(
        "DataProductVariableORM",
        back_populates="variable",
    )

    __table_args__ = (
        UniqueConstraint(
            "obs_space_id",
            "name",
            name="uq_variable_obs_space_name",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<VariableORM("
            f"id={self.id}, "
            f"name='{self.name}', "
            f"obs_space_id={self.obs_space_id})>"
        )


class DataProductORM(Base):
    """
    Logical data product.

    A data product represents a collection of data for one or more
    logical variables.  Its physical representation is deliberately
    separate from the product itself.
    """

    __tablename__ = "data_products"

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

    type = Column(
        String,
        nullable=False,
    )

    variables = relationship(
        "DataProductVariableORM",
        back_populates="data_product",
    )

    def __repr__(self) -> str:
        return (
            f"<DataProductORM("
            f"id={self.id}, "
            f"name='{self.name}', "
            f"type='{self.type}')>"
        )


class DataProductVariableORM(Base):
    """
    Associates a logical Variable with a DataProduct.

    storage_name is representation-specific metadata.  For a NetCDF
    product it may, for example, contain the NetCDF variable path.
    """

    __tablename__ = "data_product_variables"

    data_product_id = Column(
        Integer,
        ForeignKey("data_products.id"),
        primary_key=True,
    )

    variable_id = Column(
        Integer,
        ForeignKey("variables.id"),
        primary_key=True,
    )

    storage_name = Column(
        String,
        nullable=True,
    )

    data_product = relationship(
        "DataProductORM",
        back_populates="variables",
    )

    variable = relationship(
        "VariableORM",
        back_populates="data_product_variables",
    )
