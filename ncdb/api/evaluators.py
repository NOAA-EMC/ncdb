import logging
import operator
from abc import ABC, abstractmethod
from datetime import datetime
import os
import numpy as np
from .value import Value

logger = logging.getLogger(__name__)

class BaseEvaluator(ABC):
    @abstractmethod
    def at(self, time: datetime) -> Value:
        pass

    @property
    @abstractmethod
    def cycles(self) -> list:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass


# =====================================================================
# THE SINGLE TRUE LEAF (Base NetCDF Variable Consumer)
# =====================================================================

class BaseVariableEvaluator(BaseEvaluator):
    def __init__(self, field_obj, variable_path, repo):
        self._field = field_obj
        self._variable_path = variable_path
        self._repo = repo

    @property
    def name(self) -> str:
        return os.path.basename(self._variable_path) if self._variable_path else "variable"

    @property
    def cycles(self):
        from ncdb.ds.services.field_data_service import FieldDataService
        return FieldDataService(self._repo.session).get_cycles(self._field)

    def at(self, time: datetime) -> Value:
        ds_file = self._repo.load_file_for_field_and_cycle(self._field, time.date(), time.hour)
        if ds_file is None or ds_file.netcdf_file is None:
            raise ValueError(f"No data for time {time}")
        
        data = ds_file.get_variable(self._variable_path)
        lat = ds_file.get_variable("/MetaData/latitude")
        lon = ds_file.get_variable("/MetaData/longitude")
        
        coords = {}
        if lat is not None and lon is not None:
            coords = {"latitude": lat, "longitude": lon}
        return Value(data=data, coords=coords)


# =====================================================================
# EXPRESSION NODES (Composite Operators)
# =====================================================================

class DerivedAttributeEvaluator(BaseEvaluator):
    def __init__(self, target_field, derived_name):
        # Instead of raw DB configurations, it holds a reference to its child variable node
        self.target = target_field
        self._derived_name = derived_name

    @property
    def name(self) -> str:
        return f"{self.target.name}.{self._derived_name}"

    @property
    def cycles(self):
        return self.target.cycles

    def at(self, time: datetime) -> Value:
        # Ask the child node for its core structural data to run the DB lookup
        leaf_eval = self.target._evaluator
        ds_file = leaf_eval._repo.load_file_for_field_and_cycle(
            leaf_eval._field, time.date(), time.hour
        )
        if ds_file is None or ds_file.netcdf_file is None:
            raise ValueError(f"No data for time {time}")
            
        nc_file = ds_file.netcdf_file
        nc_file.from_orm_derived_attributes(leaf_eval._repo.session)
        values = nc_file.derived_values.get(leaf_eval._variable_path, {})
        value = values.get(self._derived_name)
        
        if value is None:
            raise ValueError(f"Derived attribute '{self._derived_name}' not found.")
            
        return Value(data=value, coords={}, metadata={"derived": self._derived_name})


class PointwiseOpEvaluator(BaseEvaluator):
    def __init__(self, left, right, op_func, op_symbol):
        self.left = left
        self.right = right
        self.op_func = op_func
        self.op_symbol = op_symbol

    @property
    def name(self) -> str:
        right_name = self.right.name if hasattr(self.right, "name") else str(self.right)
        return f"({self.left.name} {self.op_symbol} {right_name})"

    @property
    def cycles(self):
        if hasattr(self.right, "cycles"):
            return sorted(list(set(self.left.cycles).intersection(set(self.right.cycles))))
        return self.left.cycles

    def at(self, time: datetime) -> Value:
        val_left = self.left.at(time)
        val_right = self.right.at(time) if hasattr(self.right, "at") else self.right
        return self.op_func(val_left, val_right)


class MovingAverageEvaluator(BaseEvaluator):
    def __init__(self, target_field):
        self.target = target_field

    @property
    def name(self) -> str:
        return f"moving_avg({self.target.name})"

    @property
    def cycles(self):
        return self.target.cycles

    def at(self, time: datetime) -> Value:
        timeline = self.cycles
        if not timeline:
            raise ValueError("Target timeline history is empty.")
            
        t1 = timeline[0]
        if time < t1:
            raise ValueError(f"Requested time {time} precedes timeline root boundary.")

        active_steps = [c for c in timeline if t1 <= c <= time]
        accumulated_data = None
        count = 0
        
        for step_time in active_steps:
            try:
                target_val = self.target.at(step_time)
                if accumulated_data is None:
                    accumulated_data = target_val
                else:
                    accumulated_data = accumulated_data + target_val
                count += 1
            except Exception:
                continue

        if accumulated_data is None or count == 0:
            raise ValueError(f"No historical datapoints could be averaged at {time}")
            
        return accumulated_data / count


class MovingStandardDeviationEvaluator(BaseEvaluator):
    def __init__(self, target_field):
        self.target = target_field

    @property
    def name(self) -> str:
        return f"moving_std_dev({self.target.name})"

    @property
    def cycles(self):
        return self.target.cycles

    def at(self, time: datetime) -> Value:
        timeline = self.cycles
        if not timeline:
            raise ValueError("Target timeline history is empty.")
            
        t1 = timeline[0]
        if time < t1:
            raise ValueError(f"Requested time {time} precedes timeline root boundary.")

        active_steps = [c for c in timeline if t1 <= c <= time]
        
        # 1. First Pass: Compute the Mean over the current valid history segment
        accumulated_data = None
        count = 0
        valid_steps = []
        
        for step_time in active_steps:
            try:
                target_val = self.target.at(step_time)
                valid_steps.append(target_val)
                if accumulated_data is None:
                    accumulated_data = target_val
                else:
                    accumulated_data = accumulated_data + target_val
                count += 1
            except Exception:
                continue

        if count == 0:
            raise ValueError(f"No historical datapoints available for std dev at {time}")
            
        mean_val = accumulated_data / count

        # 2. Second Pass: Accumulate squared differences from the mean (Pointwise)
        variance_accum = None
        for target_val in valid_steps:
            diff = target_val - mean_val
            sq_diff = diff * diff  # Employs your custom pointwise math operators
            
            if variance_accum is None:
                variance_accum = sq_diff
            else:
                variance_accum = variance_accum + sq_diff

        # 3. Compute final sample/population standard deviation package
        variance_val = variance_accum / count
        
        # Unpack the raw data structure inside Value to execute the square root
        std_dev_data = np.sqrt(variance_val.data)
        
        return Value(data=std_dev_data, coords=variance_val.coords, metadata=variance_val.metadata)
