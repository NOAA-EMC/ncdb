import os
import logging
import numpy as np

logger = logging.getLogger(__name__)

# --- HEADLESS ISOLATION MECHANICS FOR HPC COMPUTATION ---
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# --- FORCE EXCLUSIVE OFFLINE SHAPEFILE RESOURCE RECTIFICATION ---
import cartopy
BASE_PLOT_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_CARTOPY_DIR = os.path.join(BASE_PLOT_DIR, "cartopy_data")

if os.path.isdir(LOCAL_CARTOPY_DIR):
    cartopy.config['data_dir'] = LOCAL_CARTOPY_DIR
    cartopy.config['pre_existing_data_dir'] = LOCAL_CARTOPY_DIR
else:
    logger.warning(f"Offline Cartopy directory path missing: {LOCAL_CARTOPY_DIR}")

from .engine_interface import PlottingEngine

class MatplotlibEngine(PlottingEngine):
    def __init__(self):
        self.fig, self.ax = plt.subplots(figsize=(10, 4))

    def initialize(self, title: str, y_label: str = "") -> None:
        self.ax.set_title(title, fontsize=10, fontweight='bold', color='#333', pad=10)
        self.ax.set_ylabel(y_label, fontsize=9)
        self.ax.grid(True, which='major', linestyle='--', alpha=0.6)
        self.ax.grid(True, which='minor', linestyle=':', alpha=0.3)

    def draw_spatial_surface(self, lons, lats, values, cmap: str, vmin: float, vmax: float, marker_size: float) -> None:
        """Renders offline Robinson global projection base charts."""
        plt.close(self.fig)
        import cartopy.crs as ccrs
        import cartopy.feature as cfeature
        
        self.fig = plt.figure(figsize=(12, 6))
        self.ax = plt.axes(projection=ccrs.Robinson())
        self.ax.set_global()
        
        # Load local spatial visual attributes
        self.ax.coastlines(resolution='110m', linewidth=0.5)
        self.ax.add_feature(cfeature.LAND, facecolor='lightgray', zorder=0)
        self.ax.add_feature(cfeature.OCEAN, facecolor='white', zorder=0)
        self.ax.gridlines(draw_labels=False)

        sc = self.ax.scatter(
            lons, lats, c=values, s=marker_size, cmap=cmap, vmin=vmin, vmax=vmax,
            transform=ccrs.PlateCarree(), edgecolor='k', linewidth=0.2
        )
        cbar = plt.colorbar(sc, ax=self.ax, orientation='vertical', pad=0.02)
        self._cbar_ref = cbar

    def draw_line(self, x_data, y_data, label: str, color: str = None, alpha: float = 1.0, linewidth: float = 2.0, linestyle: str = "-") -> None:
        self.ax.plot(x_data, y_data, label=label, color=color, alpha=alpha, linewidth=linewidth, linestyle=linestyle)

    def draw_shaded_band(self, x_data, y_lower, y_upper, label: str, color: str, alpha: float) -> None:
        self.ax.fill_between(x_data, y_lower, y_upper, color=color, alpha=alpha, label=label)

    def save(self, out_path: str) -> str:
            # Dynamic axis limit protection logic
            if hasattr(self.ax, 'get_lines') and self.ax.get_lines():
                # Apply padding logic safely if time series axes exist
                self.fig.autofmt_xdate()
                self.ax.legend(loc='upper left', fontsize='small', frameon=True)
                self.ax.xaxis.set_major_locator(mdates.AutoDateLocator())
                self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
                
            # Coerce out_path to a string safely to prevent Path object iteration crashes
            out_path_str = str(out_path)
            dpi_val = 150 if 'surface' in out_path_str else 100

            plt.tight_layout()
            plt.savefig(out_path, dpi=dpi_val, bbox_inches='tight')
            plt.close(self.fig)
            return out_path_str


class PlotlyEngine(PlottingEngine):
    """HTML interactive delivery engine supporting edge views."""
    def __init__(self):
        import plotly.graph_objects as go
        self.go = go
        self.fig = go.Figure()
        self.title = ""

    def initialize(self, title: str, y_label: str = "") -> None:
        self.title = title
        self.fig.update_layout(title=title, yaxis_title=y_label, template="plotly_white", height=600)

    def draw_spatial_surface(self, lons, lats, values, cmap: str, vmin: float, vmax: float, marker_size: float) -> None:
        trace = self.go.Scattergeo(
            lat=lats, lon=lons, mode='markers',
            marker=dict(
                size=3, color=values, colorscale=cmap, cmin=vmin, cmax=vmax,
                showscale=True, line=dict(width=0.1, color='black')
            ),
            text=[f"{v:.2f}" for v in values],
            hovertemplate="<b>Lat:</b> %{lat}<br><b>Lon:</b> %{lon}<br><b>Val:</b> %{text}<extra></extra>"
        )
        self.fig.add_trace(trace)
        self.fig.update_layout(
            title=f"Interactive Viewer: {self.title}",
            geo=dict(
                projection_type='orthographic', showland=True, landcolor="lightgray",
                showocean=True, oceancolor="white", showcoastlines=True, coastlinecolor="gray"
            ),
            margin=dict(l=0, r=0, t=40, b=0)
        )

    def draw_line(self, x_data, y_data, label: str, color: str = None, alpha: float = 1.0, linewidth: float = 2.0, linestyle: str = "-") -> None:
        line_opt = dict(color=color, width=linewidth) if color else dict(width=linewidth)
        if linestyle == "--":
            line_opt["dash"] = "dash"
        self.fig.add_trace(self.go.Scatter(x=x_data, y=y_data, mode='lines', name=label, line=line_opt, opacity=alpha))

    def draw_shaded_band(self, x_data, y_lower, y_upper, label: str, color: str, alpha: float) -> None:
        # Replicate fill bounds for web presentation
        self.fig.add_trace(self.go.Scatter(x=x_data, y=y_upper, mode='lines', line=dict(width=0), showlegend=False))
        self.fig.add_trace(self.go.Scatter(x=x_data, y=y_lower, mode='lines', fill='tonexty', fillcolor=color, name=label, opacity=alpha))

    def save(self, out_path: str) -> str:
        self.fig.write_html(out_path)
        return out_path
