import os
import logging
from typing import Optional, List, Union, Tuple
import pandas as pd
import numpy as np

# --- HEADLESS ISOLATION MECHANICS FOR HPC COMPUTATION ---
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import NullLocator

# --- FORCE EXCLUSIVE OFFLINE SHAPEFILE RESOURCE RECTIFICATION ---
import cartopy
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# --- LOCAL MODULE IMPORTS ---
from .subsample_surface import subsample_surface_points
from .color_scales import ColorScaleManager

logger = logging.getLogger(__name__)

BASE_PLOT_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_CARTOPY_DIR = os.path.join(BASE_PLOT_DIR, "cartopy_data")

if os.path.isdir(LOCAL_CARTOPY_DIR):
    cartopy.config['data_dir'] = LOCAL_CARTOPY_DIR
    cartopy.config['pre_existing_data_dir'] = LOCAL_CARTOPY_DIR
else:
    logger.warning(f"Offline Cartopy directory path missing: {LOCAL_CARTOPY_DIR}")


class PlotGenerator:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.color_manager = ColorScaleManager()

    def generate_history_plot(
        self, 
        df: pd.DataFrame, 
        time_col: str,
        single_val_cols: Optional[Union[str, List[str]]] = None, 
        banded_val_cols: Optional[List[Tuple[str, str]]] = None,
        title: str = "",
        y_label: str = "", 
        fname: str = "history.png"
    ) -> str:
        """
        Plots historical time series directly using Matplotlib.
         Supports standard lines via `single_val_cols`.
         Supports lines enveloped by shaded variance bands via `banded_val_cols`.
        """
        plot_df = df.sort_values(by=time_col)
        x_data = plot_df[time_col].values

        fig, ax = plt.subplots(figsize=(10, 4))
        
        # Setup visual metadata
        if title:
            ax.set_title(title, fontsize=10, fontweight='bold', color='#333', pad=10)
        if y_label:
            ax.set_ylabel(y_label, fontsize=9)
        else:
            ax.yaxis.label.set_visible(False)
            
        ax.grid(True, which='major', linestyle='--', alpha=0.6)
        ax.grid(True, which='minor', linestyle=':', alpha=0.3)

        # 1. Render standard single lines
        if single_val_cols:
            cols = [single_val_cols] if isinstance(single_val_cols, str) else single_val_cols
            for col in cols:
                ax.plot(
                    x_data, plot_df[col].values, label=col, linewidth=2.0, marker='o', markersize=4.0,
                    markeredgecolor='#1e293b', markeredgewidth=0.8, zorder=3
                )
        # 2. Render lines with associated variance bands
        if banded_val_cols:
            for val_col, band_col in banded_val_cols:
                y_data = plot_df[val_col].values
                band_size = plot_df[band_col].values
                
                y_lower = y_data - band_size
                y_upper = y_data + band_size
                
                # Draw the center line
                line_ref = ax.plot(
                    x_data, y_data, label=val_col, linewidth=2.0, marker='o', markersize=4.0,
                    markeredgecolor='#1e293b', markeredgewidth=0.8, zorder=3
                )
                line_color = line_ref[0].get_color()
                
                # --- FLEXIBLE SUFFIX MATCHING ENGINE ---
                # Determine what the band actually represents (std_dev, rmse, etc.)
                if "std_dev" in band_col:
                    band_label_type = "std_dev"
                elif "rmse" in band_col:
                    band_label_type = "rmse"
                else:
                    # Fallback to the raw column name or stripped base if unknown
                    band_label_type = band_col
                
                # Construct clean legend text (e.g., "seaSurfaceTemperature.meanIndian std_dev")
                clean_band_label = f"{val_col} {band_label_type}"
                
                # Draw the corresponding shaded band matching the line's color natively
                ax.fill_between(
                    x_data, y_lower, y_upper, color=line_color, alpha=0.15, 
                    label=clean_band_label, zorder=2
                )

        # 3. Adaptive X-axis for forecast cycles
        try:
            plot_df[time_col] = pd.to_datetime(plot_df[time_col])
            x = plot_df[time_col]

            n = len(x)

            # Decide how many cycles to skip between labels.
            # Aim for roughly 8-12 labels.
            if n <= 12:
                stride = 1
            elif n <= 24:
                stride = 2
            elif n <= 48:
                stride = 4
            elif n <= 96:
                stride = 8
            else:
                stride = max(1, n // 10)

            tick_locations = []
            tick_labels = []

            previous_day = None

            for i, t in enumerate(x):

                # skip unlabeled ticks
                if i % stride != 0:
                    continue

                tick_locations.append(t)

                day = t.date()

                # First label or new day -> print the date
                if previous_day is None or day != previous_day:
                    tick_labels.append(t.strftime("%m-%d-%y"))
                else:
                    # Same day -> print forecast cycle
                    tick_labels.append(t.strftime("%H"))

                previous_day = day

            ax.set_xticks(tick_locations)
            ax.set_xticklabels(tick_labels)

            ax.tick_params(
                axis="x",
                labelsize=8,
                labelcolor="#475569",
                pad=6
            )

            # No rotation needed
            plt.setp(ax.get_xticklabels(), rotation=0, ha="center")

        except Exception as tick_err:
            logger.warning(f"Adaptive tick mapping bypassed safely: {tick_err}")

        # Show legend if there's more than one element on the chart
        has_legend = (single_val_cols and len(cols) > 0) or (banded_val_cols and len(banded_val_cols) > 0)
        if has_legend:
            ax.legend(loc='upper left', fontsize='small', frameon=True)

        out_path = os.path.join(self.output_dir, fname)
        plt.tight_layout()
        plt.savefig(out_path, dpi=100, bbox_inches='tight')
        plt.close(fig)
        
        return fname


    def old_generate_history_plot(
        self, 
        df: pd.DataFrame, 
        time_col: str,
        val_cols: Union[str, List[str]], 
        std_col: Optional[str] = None, 
        title: str = "",
        y_label: str = "", 
        fname: str = "history.png", 
        days: Optional[int] = None, 
        clamp_bottom: bool = True,
        use_moving_avg: bool = False, 
        window_size: int = 120
    ) -> str:
        """
        Plots single or multiple historical time series directly using Matplotlib.
        """
        plot_df = df.copy()
        plot_df[time_col] = pd.to_datetime(plot_df[time_col])
        plot_df = plot_df.sort_values(by=time_col)

        if days is not None:
            cutoff_date = plot_df[time_col].max() - pd.Timedelta(days=days)
            plot_df = plot_df[plot_df[time_col] >= cutoff_date]

        if plot_df.empty:
            raise ValueError(f"No historical data found matching the constraints (days filter={days}).")

        columns_to_plot = [val_cols] if isinstance(val_cols, str) else val_cols

        fig, ax = plt.subplots(figsize=(10, 4))
        
        if title:
            ax.set_title(title, fontsize=10, fontweight='bold', color='#333', pad=10)
        if y_label:
            ax.set_ylabel(y_label, fontsize=9)
        else:
            ax.yaxis.label.set_visible(False)
            
        ax.grid(True, which='major', linestyle='--', alpha=0.6)
        ax.grid(True, which='minor', linestyle=':', alpha=0.3)

        x_data = plot_df[time_col].values

        for col in columns_to_plot:
            y_data = plot_df[col].copy()

            if clamp_bottom:
                y_data = np.clip(y_data, a_min=0, a_max=None)

            if use_moving_avg and len(y_data) >= window_size:
                y_data = y_data.rolling(window=window_size, min_periods=1).mean()

            ax.plot(
                x_data, y_data, label=col, linewidth=2.0, marker='o', markersize=4.0,
                markeredgecolor='#1e293b', markeredgewidth=0.8, zorder=3
            )

        if std_col and len(columns_to_plot) == 1 and std_col in plot_df.columns:
            base_y = plot_df[columns_to_plot[0]].values
            std_y = plot_df[std_col].values
            
            y_lower = base_y - std_y
            y_upper = base_y + std_y
            
            if clamp_bottom:
                y_lower = np.clip(y_lower, a_min=0, a_max=None)
                y_upper = np.clip(y_upper, a_min=0, a_max=None)

            ax.fill_between(x_data, y_lower, y_upper, alpha=0.2, label=f"Variance ({std_col})", zorder=2)

        try:
            locator = mdates.AutoDateLocator(minticks=4, maxticks=8)
            formatter = mdates.AutoDateFormatter(locator)
            
            formatter.scaled[mdates.MICROSECOND] = '%H:%M:%S.%f'
            formatter.scaled[mdates.SECOND]      = '%H:%M:%S'
            formatter.scaled[mdates.MINUTE]      = '%H:%M'
            formatter.scaled[mdates.HOUR]        = '%Y-%m-%d %H:%M'
            formatter.scaled[mdates.DAY]         = '%Y-%m-%d'
            formatter.scaled[mdates.MONTH]       = '%Y-%m'
            formatter.scaled[mdates.YEAR]        = '%Y'

            ax.xaxis.set_minor_locator(NullLocator())
            ax.xaxis.set_major_locator(locator)
            ax.xaxis.set_major_formatter(formatter)
            ax.tick_params(axis='x', which='major', labelsize=8, labelcolor='#475569', pad=6)
            plt.setp(ax.get_xticklabels(), rotation=15, ha='right')
        except Exception as tick_err:
            logger.warning(f"Adaptive tick mapping bypassed safely: {tick_err}")

        if len(columns_to_plot) > 1 or std_col:
            ax.legend(loc='upper left', fontsize='small', frameon=True)

        out_path = os.path.join(self.output_dir, fname)
        plt.tight_layout()
        plt.savefig(out_path, dpi=100, bbox_inches='tight')
        plt.close(fig)
        
        return fname

    def generate_surface_map(
        self, 
        df: pd.DataFrame, 
        lat_col: str, 
        lon_col: str, 
        value_col: str, 
        var_name: Optional[str] = None,
        fname: str = "surface_map.png", 
        title: str = "",
        marker_size: float = 3.0,
        max_points: int = 300_000
    ) -> str:
        """Static offline global Robinson chart using Matplotlib + Cartopy."""
        # Extract raw arrays from DataFrame
        lats = df[lat_col].values
        lons = df[lon_col].values
        values = df[value_col].values

        lats, lons, values, _ = subsample_surface_points(lats, lons, values, max_points=max_points)

        vmin, vmax, cmap = self.color_manager.resolve(values, var_name=var_name)

        fig = plt.figure(figsize=(12, 6))
        ax = plt.axes(projection=ccrs.Robinson())
        ax.set_global()
        
        ax.coastlines(resolution='110m', linewidth=0.5)
        ax.add_feature(cfeature.LAND, facecolor='lightgray', zorder=0)
        ax.add_feature(cfeature.OCEAN, facecolor='white', zorder=0)
        ax.gridlines(draw_labels=False)

        if title:
            ax.set_title(title, fontsize=10, fontweight='bold', color='#333', pad=10)

        sc = ax.scatter(
            lons, lats, c=values, s=marker_size, cmap=cmap, vmin=vmin, vmax=vmax,
            transform=ccrs.PlateCarree(), edgecolor='k', linewidth=0.2, zorder=3
        )
        
        plt.colorbar(sc, ax=ax, orientation='vertical', pad=0.02)

        out_path = os.path.join(self.output_dir, fname)
        plt.tight_layout()
        plt.savefig(out_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        return fname

    def generate_interactive_surface_map(
        self, 
        df: pd.DataFrame, 
        lat_col: str, 
        lon_col: str, 
        value_col: str, 
        var_name: Optional[str] = None,
        fname: str = "surface_map.html", 
        title: str = "",
        max_points: int = 300_000
    ) -> str:
        """Interactive global chart using Plotly directly, saving to HTML."""
        lats = df[lat_col].values
        lons = df[lon_col].values
        values = df[value_col].values

        lats, lons, values, _ = subsample_surface_points(lats, lons, values, max_points=max_points)

        vmin, vmax, cmap = self.color_manager.resolve(values, var_name=var_name)

        import plotly.graph_objects as go

        fig = go.Figure()

        trace = go.Scattergeo(
            lat=lats, 
            lon=lons, 
            mode='markers',
            marker=dict(
                size=4, 
                color=values, 
                colorscale=cmap if isinstance(cmap, str) else "Viridis", 
                cmin=vmin,
                cmax=vmax,
                showscale=True, 
                line=dict(width=0.1, color='black')
            ),
            text=[f"{v:.2f}" for v in values],
            hovertemplate="<b>Lat:</b> %{lat}<br><b>Lon:</b> %{lon}<br><b>Val:</b> %{text}<extra></extra>"
        )
        
        fig.add_trace(trace)
        
        fig.update_layout(
            title=title if title else "Interactive Surface Map",
            template="plotly_white",
            height=600,
            geo=dict(
                projection_type='orthographic', 
                showland=True, 
                landcolor="lightgray",
                showocean=True, 
                oceancolor="white", 
                showcoastlines=True, 
                coastlinecolor="gray"
            ),
            margin=dict(l=0, r=0, t=40, b=0)
        )

        out_path = os.path.join(self.output_dir, fname)
        fig.write_html(out_path)
        
        return fname
