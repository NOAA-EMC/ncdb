from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from datetime import datetime
from .engine_interface import PlottingEngine
from ncdb.plotting.color_scales import ColorScaleManager
from ncdb.plotting.subsample_surface import subsample_surface_points

class PlotStrategy(ABC):
    @abstractmethod
    def render(self, engine: PlottingEngine, out_path: str) -> str:
        pass


class SpatialSurfaceMapStrategy(PlotStrategy):
    def __init__(self, plot_data: dict, max_points: int = 300_000):
        self.plot_data = plot_data
        self.max_points = max_points
        self.color_manager = ColorScaleManager()

    def _compute_marker_size(self, n_points: int) -> float:
        if n_points <= 0:
            return 100.0
        return max(5.0, 100.0 / (1 + np.log10(n_points)))

    def render(self, engine: PlottingEngine, out_path: str) -> str:
        lats, lons = self.plot_data["lats"], self.plot_data["lons"]
        values = self.plot_data["values"]
        var_name = self.plot_data["variable_name"]
        
        # 1. Pipeline optimization constraint mechanics
        lats, lons, values, _ = subsample_surface_points(lats, lons, values, max_points=self.max_points)
        
        # 2. Extract adaptive metrics and scale layouts
        marker_size = self._compute_marker_size(len(values))
        vmin, vmax, cmap = self.color_manager.resolve(values, var_name)
        units = self.plot_data.get("units", "Units")

        title = f"{self.plot_data['dataset_name']} - {self.plot_data['obs_space_name']}"
        engine.initialize(title=title, y_label=units)
        
        # 3. Stream pipeline properties out to active layout driver
        engine.draw_spatial_surface(lons, lats, values, cmap, vmin, vmax, marker_size)
        return engine.save(out_path)


class HistoryPlotStrategy(PlotStrategy):
    """
    Standardized Unified Time-Series Rendering Core.
    Handles legacy dictionary records and native Pandas DataFrame tracking blocks.
    """
    def __init__(self, data, val_col: str, std_col: str = None, title: str = "", y_label: str = "",
                 days: int = None, clamp_bottom: bool = True, use_moving_avg: bool = False, window_size: int = 120):
        self.val_col = val_col
        self.std_col = std_col
        self.title = title
        self.y_label = y_label
        self.clamp_bottom = clamp_bottom
        self.use_moving_avg = use_moving_avg
        self.window_size = window_size
        
        # 1. Normalize data payload structure immediately into Pandas Frame
        self.df = self._normalize_to_dataframe(data, days)

    def _normalize_to_dataframe(self, data, days: int = None) -> pd.DataFrame:
        if isinstance(data, pd.DataFrame):
            df = data.copy()
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)
        else:
            # Parse traditional array structural properties safely
            parsed_records = []
            for r in data:
                try:
                    dt_str = f"{r['date']}{r['cycle']:02d}"
                    dt = datetime.strptime(dt_str, "%Y%m%d%H")
                    if r.get(self.val_col) is None:
                        continue
                    rec = {"time": dt, self.val_col: r[self.val_col]}
                    if self.std_col and r.get(self.std_col) is not None:
                        rec[self.std_col] = r[self.std_col]
                    parsed_records.append(rec)
                except Exception:
                    continue
            if not parsed_records:
                return pd.DataFrame()
            df = pd.DataFrame(parsed_records).set_index("time")

        if days is not None and not df.empty:
            cutoff = df.index.max() - pd.Timedelta(days=days)
            df = df[df.index >= cutoff]
        return df.sort_index()

    def render(self, engine: PlottingEngine, out_path: str) -> str:
        if self.df.empty:
            return out_path

        engine.initialize(title=self.title, y_label=self.y_label)
        v_arr, d_arr = self.df[self.val_col], self.df.index

        # MODE 1: Explicit Companion Field Band (e.g., Mean ± StdDev)
        if self.std_col and self.std_col in self.df.columns:
            s_arr = self.df[self.std_col]
            lower = v_arr - s_arr
            upper = v_arr + s_arr
            if self.clamp_bottom:
                lower = lower.clip(lower=0)
            
            engine.draw_shaded_band(d_arr, lower, upper, "±1σ (Spatial)", '#3498db', 0.3)
            engine.draw_line(d_arr, v_arr, "Mean", '#2980b9')

        # MODE 2: Trailing Moving Historical Window Band
        elif self.use_moving_avg:
            roll = v_arr.rolling(window=self.window_size, min_periods=1)
            m_val, m_std = roll.mean(), roll.std()
            lower = m_val - m_std
            if self.clamp_bottom:
                lower = lower.clip(lower=0)

            engine.draw_line(d_arr, v_arr, "Actual", '#2980b9', alpha=0.3, linewidth=1.0)
            engine.draw_line(d_arr, m_val, "Moving Avg", '#e67e22')
            engine.draw_shaded_band(d_arr, lower, m_val + m_std, "MA ±1σ", '#e67e22', 0.15)

        # MODE 3: Clean Single Trendline (No Band Specified)
        else:
            engine.draw_line(d_arr, v_arr, "Value", '#2980b9')

        return engine.save(out_path)


class MultiSeriesHistoryStrategy(PlotStrategy):
    """Combines multiple independent metrics into a single comparison canvas."""
    def __init__(self, series_list: list, title: str, y_label: str):
        self.series_list = series_list
        self.title = title
        self.y_label = y_label

    def render(self, engine: PlottingEngine, out_path: str) -> str:
        engine.initialize(title=self.title, y_label=self.y_label)
        for s in self.series_list:
            df = s["df"]
            if df.empty:
                continue
            engine.draw_line(df.index, df[s["val_col"]], label=s["label"])
        return engine.save(out_path)
