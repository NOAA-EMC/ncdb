from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


# ----------------------------------------------------------------------
# Asset Catalog
# ----------------------------------------------------------------------

# class AssetSourceORM(Base):
    # __tablename__ = "asset_source"
# 
    # id = Column(Integer, primary_key=True)
    # name = Column(String, nullable=False, unique=True)
    # handler = Column(String, nullable=False)
    # parameters = Column(Text)
# 

class AssetTypeORM(Base):
    __tablename__ = "asset_type"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)

    assets = relationship("AssetORM", back_populates="asset_type")


class AssetORM(Base):
    __tablename__ = "asset"

    id = Column(Integer, primary_key=True)

    asset_type_id = Column(
        Integer,
        ForeignKey("asset_type.id"),
        nullable=False,
    )

    uri = Column(String, nullable=False, unique=True)

    state = Column(String, nullable=False, default="AVAILABLE")

    fingerprint = Column(String)

    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    asset_type = relationship("AssetTypeORM", back_populates="assets")


# ----------------------------------------------------------------------
# Workflow Definition
# ----------------------------------------------------------------------

class TransformationORM(Base):
    __tablename__ = "transformation"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    handler = Column(String, nullable=False)
    parameters = Column(Text)

    # Relationships to junction tables
    inputs = relationship("TransformationInputORM", back_populates="transformation", cascade="all, delete-orphan")
    outputs = relationship("TransformationOutputORM", back_populates="transformation", cascade="all, delete-orphan")


class TransformationInputORM(Base):
    __tablename__ = "transformation_input"

    transformation_id = Column(
        Integer,
        ForeignKey("transformation.id"),
        primary_key=True,
    )

    asset_type_id = Column(
        Integer,
        ForeignKey("asset_type.id"),
        primary_key=True,
    )

    transformation = relationship("TransformationORM", back_populates="inputs")
    asset_type = relationship("AssetTypeORM")


class TransformationOutputORM(Base):
    __tablename__ = "transformation_output"

    transformation_id = Column(
        Integer,
        ForeignKey("transformation.id"),
        primary_key=True,
    )

    asset_type_id = Column(
        Integer,
        ForeignKey("asset_type.id"),
        primary_key=True,
    )

    transformation = relationship("TransformationORM", back_populates="outputs")
    asset_type = relationship("AssetTypeORM")


# ----------------------------------------------------------------------
# Workflow Execution
# ----------------------------------------------------------------------

class JobORM(Base):
    __tablename__ = "job"

    id = Column(Integer, primary_key=True)
    transformation_id = Column(Integer, ForeignKey("transformation.id"), nullable=False)
    state = Column(String, nullable=False, default="PENDING")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    error_log = Column(Text)

    transformation = relationship("TransformationORM")
    job_input_assets = relationship("JobInputAssetORM", back_populates="job", cascade="all, delete-orphan")
    job_output_assets = relationship("JobOutputAssetORM", back_populates="job", cascade="all, delete-orphan")


class JobInputAssetORM(Base):
    __tablename__ = "job_input_asset"

    job_id = Column(Integer, ForeignKey("job.id"), primary_key=True)
    asset_id = Column(Integer, ForeignKey("asset.id"), primary_key=True)

    job = relationship("JobORM", back_populates="job_input_assets")
    asset = relationship("AssetORM")


class JobOutputAssetORM(Base):
    __tablename__ = "job_output_asset"

    job_id = Column(Integer, ForeignKey("job.id"), primary_key=True)
    asset_id = Column(Integer, ForeignKey("asset.id"), primary_key=True)

    job = relationship("JobORM", back_populates="job_output_assets")
    asset = relationship("AssetORM")
