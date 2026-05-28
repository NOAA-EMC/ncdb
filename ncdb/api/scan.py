from dataclasses import dataclass, field

@dataclass
class ScanWarning:
    message: str
    dataset: str | None = None
    cycle: str | None = None
    file: str | None = None

@dataclass
class ScanError:
    message: str
    exception: str
    dataset: str | None = None
    cycle: str | None = None
    file: str | None = None

@dataclass
class ScanResult:
    datasets: list[str] = field(default_factory=list)

    cycles_scanned: list[str] = field(default_factory=list)

    files_scanned: int = 0
    files_failed: int = 0

    warnings: list[ScanWarning] = field(default_factory=list)
    errors: list[ScanError] = field(default_factory=list)

    success: bool = True
