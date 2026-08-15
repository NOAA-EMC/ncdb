from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any

from ..domain.storage_device import StorageDevice, StorageInfo


class DatabaseDevice(StorageDevice):
    """
    Virtual storage device backed by SQLite.

    The address is an arbitrary string identifying the stored byte
    sequence.
    """

    device_type = "database"

    def __init__(self, database: str) -> None:
        self.database = database
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database)

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS data (
                    address TEXT PRIMARY KEY,
                    data BLOB NOT NULL,
                    created_at TEXT NOT NULL,
                    modified_at TEXT NOT NULL
                )
                """
            )

    def put(self, address: str, data: bytes) -> None:
        now = datetime.now(timezone.utc).isoformat()

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO data (
                    address,
                    data,
                    created_at,
                    modified_at
                )
                VALUES (?, ?, ?, ?)
                ON CONFLICT(address)
                DO UPDATE SET
                    data = excluded.data,
                    modified_at = excluded.modified_at
                """,
                (address, data, now, now),
            )

    def get(self, address: str) -> bytes:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT data
                FROM data
                WHERE address = ?
                """,
                (address,),
            ).fetchone()

        if row is None:
            raise KeyError(
                f"No data stored at database address '{address}'"
            )

        return bytes(row[0])

    def delete(self, address: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                DELETE FROM data
                WHERE address = ?
                """,
                (address,),
            )

    def metadata(self, address: str) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    length(data),
                    created_at,
                    modified_at
                FROM data
                WHERE address = ?
                """,
                (address,),
            ).fetchone()

        if row is None:
            raise KeyError(
                f"No data stored at database address '{address}'"
            )

        return {
            "size": row[0],
            "creation_time": row[1],
            "modification_time": row[2],
            "format": None,
        }

    def availability(self, address: str) -> StorageInfo:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT 1
                FROM data
                WHERE address = ?
                """,
                (address,),
            ).fetchone()

        return StorageInfo(
            available=row is not None,
            cost=2.0,
            cost_unit="relative",
        )
