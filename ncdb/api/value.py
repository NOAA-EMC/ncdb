# api/value.py
import os
import pandas as pd
from ncdb.plotting.plot_generator import PlotGenerator

BASE_DATA_PRODUCTS_DIR = "/scratch3/NCEPDEV/da/Edward.Givelberg/monitoring/data_products/viewer"

class Value:
    def __init__(self, data, coords=None, metadata=None):
        self.data = data
        self.coords = coords or {}
        self.metadata = metadata or {}

    def _unwrap(self, other):
        if isinstance(other, Value):
            return other._as_scalar()
        return other

    def is_scalar(self):
        try:
            return self.data.shape == ()
        except AttributeError:
            return True

    def _as_scalar(self):
        if not self.is_scalar():
            raise TypeError("Operation requires scalar Value")
        return self.data

    def __str__(self):
        if self.is_scalar():
            return str(self.data)
        return f"Value(shape={getattr(self.data, 'shape', None)})"

    def __repr__(self):
        if self.is_scalar():
            return f"<Value {self.data}>"
        return f"<Value shape={getattr(self.data, 'shape', None)}>"

    def item(self):
        return self._as_scalar()

    def __float__(self):
        return float(self._as_scalar())

    def __int__(self):
        return int(self._as_scalar())

    def __bool__(self):
        raise TypeError("Truth value of Value is ambiguous")

    def __add__(self, other):
        return Value(
            data=self._as_scalar() + self._unwrap(other), 
            coords=self.coords, 
            metadata=self.metadata
        )

    def __radd__(self, other):
        return Value(
            data=self._unwrap(other) + self._as_scalar(), 
            coords=self.coords, 
            metadata=self.metadata
        )

    def __sub__(self, other):
        return Value(
            data=self._as_scalar() - self._unwrap(other), 
            coords=self.coords, 
            metadata=self.metadata
        )

    def __rsub__(self, other):
        return Value(
            data=self._unwrap(other) - self._as_scalar(), 
            coords=self.coords, 
            metadata=self.metadata
        )

    def __mul__(self, other):
        return Value(
            data=self._as_scalar() * self._unwrap(other), 
            coords=self.coords, 
            metadata=self.metadata
        )

    def __rmul__(self, other):
        return Value(
            data=self._unwrap(other) * self._as_scalar(), 
            coords=self.coords, 
            metadata=self.metadata
        )

    def __truediv__(self, other):
        return Value(
            data=self._as_scalar() / self._unwrap(other), 
            coords=self.coords, 
            metadata=self.metadata
        )

    def __rtruediv__(self, other):
        return Value(
            data=self._unwrap(other) / self._as_scalar(), 
            coords=self.coords, 
            metadata=self.metadata
        )

    def __lt__(self, other):
        return self._as_scalar() < self._unwrap(other)

    def __le__(self, other):
        return self._as_scalar() <= self._unwrap(other)

    def __gt__(self, other):
        return self._as_scalar() > self._unwrap(other)

    def __ge__(self, other):
        return self._as_scalar() >= self._unwrap(other)

    def __eq__(self, other):
        return self._as_scalar() == self._unwrap(other)

    def __ne__(self, other):
        return self._as_scalar() != self._unwrap(other)

    def to_dataframe(self) -> pd.DataFrame:
        """Converts coordinates and observation data into a standardized DataFrame."""
        if "latitude" not in self.coords or "longitude" not in self.coords:
            raise ValueError("Value has no latitude/longitude coordinates available for surface maps.")

        return pd.DataFrame({
            "latitude": self.coords["latitude"],
            "longitude": self.coords["longitude"],
            "obs_value": self.data
        })

    def plot(self, filename=None, interactive=False):
        if filename is None:
            dataset = self.metadata.get("dataset_name", "unknown")
            obs_space = self.metadata.get("obs_space_name", "unknown")

            output_dir = os.path.join(BASE_DATA_PRODUCTS_DIR, dataset)
            os.makedirs(output_dir, exist_ok=True)

            filename = f"{obs_space}.png" if not interactive else f"{obs_space}.html"
        else:
            output_dir = os.path.dirname(filename) or "."
            filename = os.path.basename(filename)

        plotter = PlotGenerator(output_dir)
        df = self.to_dataframe()

        var_name = self.metadata.get("variable_name")
        obs_space = self.metadata.get("obs_space_name", "")
        title = f"{obs_space} - {var_name}" if var_name and obs_space else (var_name or obs_space)

        if interactive:
            generated_file = plotter.generate_interactive_surface_map(
                df=df,
                lat_col="latitude",
                lon_col="longitude",
                value_col="obs_value",
                var_name=var_name,
                fname=filename,
                title=title
            )
        else:
            generated_file = plotter.generate_surface_map(
                df=df,
                lat_col="latitude",
                lon_col="longitude",
                value_col="obs_value",
                var_name=var_name,
                fname=filename,
                title=title
            )

        return os.path.join(output_dir, generated_file)
