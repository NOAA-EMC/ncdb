from abc import ABC, abstractmethod

class PlottingEngine(ABC):
    @abstractmethod
    def initialize(self, title: str, y_label: str = "") -> None:
        """Set up basic figure metadata, axes, and grids."""
        pass

    @abstractmethod
    def draw_spatial_surface(self, lons, lats, values, cmap: str, vmin: float, vmax: float, marker_size: float) -> None:
        """Render high-quality geographic point footprints."""
        pass

    @abstractmethod
    def draw_line(self, x_data, y_data, label: str, color: str = None, alpha: float = 1.0, linewidth: float = 2.0, linestyle: str = "-") -> None:
        """Render individual continuous data projections."""
        pass

    @abstractmethod
    def draw_shaded_band(self, x_data, y_lower, y_upper, label: str, color: str, alpha: float) -> None:
        """Overlay background statistical variance fields."""
        pass

    @abstractmethod
    def save(self, out_path: str) -> str:
        """Export artifacts safely to disk locations."""
        pass
