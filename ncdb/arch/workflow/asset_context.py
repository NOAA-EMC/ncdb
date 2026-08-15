from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class AssetContext:
    """Wraps context/facts discovered about an asset during identification."""

    data: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        return self.data.get(key, default)

    def __getitem__(self, key: str) -> Any:
        return self.data[key]

    def __contains__(self, key: str) -> bool:
        return key in self.data
