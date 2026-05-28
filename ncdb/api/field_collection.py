import os
# import pandas as pd

from ncdb.ds.services.field_data_service import FieldDataService
from ncdb.plotting.plot_generator import PlotGenerator

from .field import Field


class FieldCollection:
    def __init__(self):
        self._fields = []

    def add(self, field):
        self._fields.append(field)

    def plot(self, out_file, t1=None, t2=None, n_cycles=None):

        if not self._fields:
            raise ValueError("FieldCollection is empty")

        session = self._fields[0]._repo.session
        service = FieldDataService(session)

        series = []

        for field in self._fields:

            if field._derived_name is None:
                raise ValueError(
                    "FieldCollection.plot() requires derived fields"
                )

            df = service.get_variable_derived_data(
                field._field,
                field._variable_path
            )

            # print(df.columns)
            # print(df.head())

            if df.empty:
                continue

            # --- filtering ---
            if n_cycles is not None:
                df = df.tail(n_cycles)

            elif t1 is not None or t2 is not None:
                if t1 is not None:
                    df = df[df["time"] >= t1]
                if t2 is not None:
                    df = df[df["time"] <= t2]

            label = (
                f"{field._variable_path}."
                f"{field._derived_name}"
            )

            # df = df.copy()
            # df["time"] = pd.to_datetime(df["cycle_date"]) + \
                # pd.to_timedelta(df["cycle_hour"], unit="h")

            series.append({
                "df": df,
                "val_col": field._derived_name,
                "label": label
            })

        if not series:
            raise ValueError("No data available for plotting")

        plotter = PlotGenerator(
            os.path.dirname(out_file) or "."
        )

        plotter.generate_multi_history_plot_pd(
            series=series,
            title="FieldCollection",
            y_label="Value",
            out_path=out_file
        )

        return out_file
