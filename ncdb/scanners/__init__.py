import logging
logger = logging.getLogger(__name__)

# Import the actual implementation classes
from .marine_da_scanner import MarineDAScanner
from .obsforge_scanner import ObsForgeScanner
from .obsforge_marine_scanner import ObsForgeMarineScanner


# Define the central Registry Mapping
SCANNERS = {
    "marine_da": MarineDAScanner,
    # "obsforge": ObsForgeScanner,
    "obsforge_marine": ObsForgeMarineScanner,
}

def get_scanner_class(name: str):
    """
    Looks up a scanner class by its registered string name.
    """
    if name not in SCANNERS:
        raise KeyError(
            f"Scanner '{name}' is not registered. "
            f"Available options are: {list(SCANNERS.keys())}"
        )
    return SCANNERS[name]

def list_scanners() -> list[str]:
    """
    Returns a sorted list of all registered scanner names.
    """
    return sorted(list(SCANNERS.keys()))
