import os
from typing import Optional, List, Union
import pandas as pd

from .engines import MatplotlibEngine, PlotlyEngine
from .strategies import SpatialSurfaceMapStrategy, HistoryPlotStrategy, MultiSeriesHistoryStrategy

class PlotGenerator:
    """
    High-level Orchestrator using a Bridge Pattern to separate
    What to plot (Strategies) from How to plot it (Engines).
    """
    def __init__(self, output_dir: str):
        self.output_dir = output_dir

    def _get_engine(self, interactive: bool = False):
        return PlotlyEngine() if interactive else MatplotlibEngine()

    def generate_surface_map(self, plot_path: str, plot_data: dict, interactive: bool = False):
        engine = self._get_engine(interactive=interactive)
        strategy = SpatialSurfaceMapStrategy(plot_data)
        strategy.render(engine, plot_path)

    def generate_history_plot(self, title: str, data: list, val_key: str, std_key: Optional[str],
                              fname: str, y_label: str, days: Optional[int] = None, clamp_bottom: bool = True):
        out_path = os.path.join(self.output_dir, fname)
        engine = self._get_engine(interactive=False)
        strategy = HistoryPlotStrategy(
            data, val_col=val_key, std_col=std_key, title=title,
            y_label=y_label, days=days, clamp_bottom=clamp_bottom, use_moving_avg=False
        )
        strategy.render(engine, out_path)
        return fname

    def generate_history_plot_with_moving_avg(self, plot_path: str, data: list, title: str, val_key: str,
                                              std_key: Optional[str], y_label: str, days: Optional[int] = None, clamp_bottom: bool = True):
        engine = self._get_engine(interactive=False)
        strategy = HistoryPlotStrategy(
            data, val_col=val_key, std_col=std_key, title=title,
            y_label=y_label, days=days, clamp_bottom=clamp_bottom, use_moving_avg=True, window_size=120
        )
        strategy.render(engine, plot_path)

    def generate_history_plot_pd(self, df: pd.DataFrame, val_col: str, std_col: Optional[str], title: str,
                                 y_label: str, out_path: str, days: Optional[int] = None, clamp_bottom: bool = True,
                                 use_moving_avg: bool = True, window_size: int = 120):
        engine = self._get_engine(interactive=False)
        strategy = HistoryPlotStrategy(
            df, val_col=val_col, std_col=std_col, title=title, y_label=y_label,
            days=days, clamp_bottom=clamp_bottom, use_moving_avg=use_moving_avg, window_size=window_size
        )
        strategy.render(engine, out_path)
        return os.path.basename(out_path)

    def generate_multi_history_plot_pd(self, series: List[dict], title: str, y_label: str, out_path: str) -> str:
        engine = self._get_engine(interactive=False)
        strategy = MultiSeriesHistoryStrategy(series, title, y_label)
        return strategy.render(engine, out_path)
