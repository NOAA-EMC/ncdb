from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DataProduct:
    """
    A DataProduct is identified by the Asset ID assigned by the
    Workflow Engine.

    The DataProduct itself contains no scientific identity and no
    physical storage information.
    """

    asset_id: int
