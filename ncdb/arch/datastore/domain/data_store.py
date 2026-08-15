from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from .data_product import DataProduct
from .storage_device import StorageDevice

from ..orm.base import Base
from ..orm.data_product_orm import DataProductORM
from ..orm.data_location_orm import DataLocationORM
from ..orm.storage_device_orm import StorageDeviceORM


@dataclass(frozen=True)
class DataLocation:
    asset_id: int
    device: str
    address: str


class DataStore:
    """
    Persistent registry of DataProducts and their physical locations.

    The DataStore registry is separate from the storage devices
    themselves.
    """

    def __init__(self, database: str = "datastore.db") -> None:
        self.engine = create_engine(
            f"sqlite:///{database}",
            future=True,
        )

        Base.metadata.create_all(self.engine)

        self._devices: dict[str, StorageDevice] = {}

    def register_device(
        self,
        name: str,
        device: StorageDevice,
    ) -> None:
        if name in self._devices:
            raise ValueError(
                f"Device already registered: {name}"
            )

        with Session(self.engine) as session:
            existing = session.scalar(
                select(StorageDeviceORM).where(
                    StorageDeviceORM.name == name
                )
            )

            if existing is None:
                session.add(
                    StorageDeviceORM(
                        name=name,
                        device_type=device.device_type,
                    )
                )
                session.commit()

        self._devices[name] = device

    def register(
        self,
        product: DataProduct,
        device: str,
        address: str,
        data: bytes,
    ) -> None:
        if device not in self._devices:
            raise ValueError(
                f"Unknown storage device: {device}"
            )

        storage_device = self._devices[device]

        # First store the bytes.
        #TODO: need to handle failure !!!
        storage_device.put(address, data)

        # Then record the DataProduct and its location.
        with Session(self.engine) as session:
            product_row = session.get(
                DataProductORM,
                product.asset_id,
            )

            if product_row is None:
                product_row = DataProductORM(
                    asset_id=product.asset_id
                )
                session.add(product_row)

            device_row = session.scalar(
                select(StorageDeviceORM).where(
                    StorageDeviceORM.name == device
                )
            )

            if device_row is None:
                raise RuntimeError(
                    f"Device '{device}' is not registered"
                )

            existing = session.scalar(
                select(DataLocationORM).where(
                    DataLocationORM.asset_id == product.asset_id,
                    DataLocationORM.device_id == device_row.id,
                    DataLocationORM.address == address,
                )
            )

            if existing is None:
                session.add(
                    DataLocationORM(
                        asset_id=product.asset_id,
                        device_id=device_row.id,
                        address=address,
                    )
                )

            session.commit()

    def locations(
        self,
        asset_id: int,
    ) -> list[DataLocation]:
        with Session(self.engine) as session:
            rows = session.execute(
                select(
                    DataLocationORM,
                    StorageDeviceORM,
                )
                .join(
                    StorageDeviceORM,
                    DataLocationORM.device_id
                    == StorageDeviceORM.id,
                )
                .where(
                    DataLocationORM.asset_id == asset_id
                )
            ).all()

            return [
                DataLocation(
                    asset_id=row.DataLocationORM.asset_id,
                    device=row.StorageDeviceORM.name,
                    address=row.DataLocationORM.address,
                )
                for row in rows
            ]

    def availability(
        self,
        asset_id: int,
    ) -> list[dict[str, Any]]:
        result = []

        for location in self.locations(asset_id):
            device = self._devices[location.device]

            info = device.availability(location.address)

            result.append(
                {
                    "asset_id": asset_id,
                    "device": location.device,
                    "address": location.address,
                    "available": info.available,
                    "cost": info.cost,
                    "cost_unit": info.cost_unit,
                }
            )

        return result

    def metadata(
        self,
        asset_id: int,
    ) -> list[dict[str, Any]]:
        result = []

        for location in self.locations(asset_id):
            device = self._devices[location.device]

            metadata = device.metadata(location.address)

            result.append(
                {
                    "asset_id": asset_id,
                    "device": location.device,
                    "address": location.address,
                    **metadata,
                }
            )

        return result

    def get(self, asset_id: int) -> bytes:
        locations = self.locations(asset_id)

        if not locations:
            raise KeyError(
                f"No DataProduct registered for asset_id={asset_id}"
            )

        for location in locations:
            device = self._devices[location.device]

            if device.availability(
                location.address
            ).available:
                return device.get(location.address)

        raise RuntimeError(
            f"DataProduct {asset_id} is unavailable"
        )

    def delete(self, asset_id: int) -> None:
        locations = self.locations(asset_id)

        for location in locations:
            device = self._devices[location.device]
            device.delete(location.address)

        with Session(self.engine) as session:
            session.query(DataLocationORM).filter(
                DataLocationORM.asset_id == asset_id
            ).delete()

            session.query(DataProductORM).filter(
                DataProductORM.asset_id == asset_id
            ).delete()

            session.commit()

    def list_products(self) -> list[int]:
        with Session(self.engine) as session:
            return list(
                session.scalars(
                    select(DataProductORM.asset_id)
                    .order_by(DataProductORM.asset_id)
                )
            )
