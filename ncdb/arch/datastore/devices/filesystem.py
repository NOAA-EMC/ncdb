from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..domain.storage_device import StorageDevice, StorageInfo


class FileSystemDevice(StorageDevice):
    """
    Storage device backed by a filesystem.

    address is interpreted relative to root.
    """

    device_type = "filesystem"

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, address: str) -> Path:
        path = (self.root / address).resolve()

        # Prevent escaping the device root.
        try:
            path.relative_to(self.root)
        except ValueError:
            raise ValueError(
                f"Address escapes filesystem device root: {address}"
            )

        return path

    def put(self, address: str, data: bytes) -> None:
        path = self._path(address)
        # print(f"FileSystemDevice.put: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def get(self, address: str) -> bytes:
        return self._path(address).read_bytes()

    def delete(self, address: str) -> None:
        path = self._path(address)

        if path.exists():
            path.unlink()

    def metadata(self, address: str) -> dict[str, Any]:
        path = self._path(address)

        if not path.exists():
            raise FileNotFoundError(path)

        stat = path.stat()

        return {
            "size": stat.st_size,
            "creation_time": datetime.fromtimestamp(
                stat.st_ctime,
                tz=timezone.utc,
            ),
            "modification_time": datetime.fromtimestamp(
                stat.st_mtime,
                tz=timezone.utc,
            ),
            "format": path.suffix.lstrip(".") or None,
        }

    def availability(self, address: str) -> StorageInfo:
        path = self._path(address)

        return StorageInfo(
            available=path.is_file(),
            cost=1.0,
            cost_unit="relative",
        )
