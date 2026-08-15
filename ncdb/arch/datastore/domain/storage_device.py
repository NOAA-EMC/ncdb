from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class StorageInfo:
    available: bool
    cost: float
    cost_unit: str = "relative"


class StorageDevice(ABC):
    """
    Abstract storage device.

    A device knows how to store and retrieve bytes at an address.
    It does not know anything about DataProducts or asset IDs.
    """

    device_type: str

    @abstractmethod
    def put(self, address: str, data: bytes) -> None:
        pass

    @abstractmethod
    def get(self, address: str) -> bytes:
        pass

    @abstractmethod
    def delete(self, address: str) -> None:
        pass

    @abstractmethod
    def metadata(self, address: str) -> dict[str, Any]:
        pass

    @abstractmethod
    def availability(self, address: str) -> StorageInfo:
        pass
