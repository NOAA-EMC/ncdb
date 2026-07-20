# api/expression.py
import os
import pandas as pd
import logging
from ncdb.plotting.plot_generator import PlotGenerator

logger = logging.getLogger(__name__)

class Expression:
    """Base class handling timeline history evaluation and time-series line plotting."""

    def plot(self, out_file, t1=None, t2=None, n_cycles=None, title="", y_label="", band=None):
        """
        Centralized plot manager that builds an outer-joined master dataframe 
        across cycles, pairs values with their respective band fields if provided,
        and routes to the simplified plotting backend.
        """
        nodes_to_plot = self._as_node_list()
        dfs = []

        # 1. Harvest and build DataFrames for primary timeline metrics
        for node in nodes_to_plot:
            active_cycles = node.cycles
            if not active_cycles:
                continue
                
            if t1 is not None: active_cycles = [c for c in active_cycles if c >= t1]
            if t2 is not None: active_cycles = [c for c in active_cycles if c <= t2]
            if n_cycles is not None: active_cycles = active_cycles[-n_cycles:]

            if not active_cycles:
                continue

            ds_id = node.obsspace.dataset.id
            col_name = f"{node.name} [ds_{ds_id}]"

            records = []
            for cycle in active_cycles:
                try:
                    val_obj = node.at(cycle)
                    # records.append({"time": cycle, node.name: float(val_obj)})
                    records.append({"time": cycle, col_name: float(val_obj)})
                except Exception as e:
                    logger.debug(f"Skipping cycle {cycle} for {node.name}: {e}")
                    continue

            df = pd.DataFrame(records)
            if not df.empty:
                df = df.set_index("time")
                dfs.append(df)

        if not dfs:
            raise ValueError("No valid data points available for history plotting.")

        # Join all separate series timelines into a uniform timeline index
        master_df = dfs[0]
        for next_df in dfs[1:]:
            master_df = master_df.join(next_df, how="outer")

        # 2. Harvest and join the optional variance node data if specified
        band_col_name = None
        if band is not None:
            band_cycles = band.cycles
            if t1 is not None: band_cycles = [c for c in band_cycles if c >= t1]
            if t2 is not None: band_cycles = [c for c in band_cycles if c <= t2]
            if n_cycles is not None: band_cycles = band_cycles[-n_cycles:]

            band_records = []
            for cycle in band_cycles:
                try:
                    band_val = band.at(cycle)
                    band_records.append({"time": cycle, f"{band.name}_size": float(band_val)})
                except Exception as e:
                    logger.debug(f"Skipping band cycle {cycle} for {band.name}: {e}")
                    continue

            band_df = pd.DataFrame(band_records)
            if not band_df.empty:
                band_df = band_df.set_index("time")
                master_df = master_df.join(band_df, how="outer")
                band_col_name = f"{band.name}_size"

        # Bring the 'time' index back into a explicit data column
        master_df = master_df.reset_index(names="time")

        # 3. Categorize column inputs into standard lines vs banded layouts
        single_val_cols = []
        banded_val_cols = []

        for node in nodes_to_plot:
            ds_id = node.obsspace.dataset.id
            col_name = f"{node.name} [ds_{ds_id}]"

            if col_name in master_df.columns:
                if band_col_name and band_col_name in master_df.columns:
                    # Map to the (value_column, band_size_column) structure 
                    banded_val_cols.append((col_name, band_col_name))
                else:
                    single_val_cols.append(col_name)

            # if node.name in master_df.columns:
                # if band_col_name and band_col_name in master_df.columns:
                    # # Map to the (value_column, band_size_column) structure 
                    # banded_val_cols.append((node.name, band_col_name))
                # else:
                    # single_val_cols.append(node.name)

        output_dir = os.path.dirname(out_file) or "."
        filename = os.path.basename(out_file)

        plotter = PlotGenerator(output_dir)
        
        plotter.generate_history_plot(
            df=master_df,
            time_col="time",
            single_val_cols=single_val_cols if single_val_cols else None,
            banded_val_cols=banded_val_cols if banded_val_cols else None,
            title=title or getattr(self, "name", ""),
            y_label=y_label,
            fname=filename
        )

        return out_file

    def _as_node_list(self):
        """Flattens single nodes or composite fields into an iterable tracking list."""
        if hasattr(self, "_fields"):
            return self._fields
        return [self]
