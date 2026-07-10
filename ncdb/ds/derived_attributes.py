import logging
import numpy as np

logger = logging.getLogger(__name__)


def make_basin_metric(base_math_func, basin_id, mask_path="/MetaData/oceanBasin"):
    """
    Generates a brute-force metric function tied to a specific basin ID number.
    It intercepts execution, loads the mask variable from the file runtime, 
    slices the main data array down via NumPy, and runs the math primitive.
    """
    def basin_metric(nc_file, data_array):
        # Fetch the mapping array dynamically from the current file context wrapper
        basin_array = nc_file.get_variable(mask_path, filter_out_masked=False)
        if basin_array is None or basin_array.shape != data_array.shape:
            return np.nan
            
        # Brute-force slice the data array matching this exact condition
        sliced_data = data_array[basin_array == basin_id]
        if sliced_data.size == 0:
            return np.nan
            
        # Forward the isolated region slice to the math primitive function
        return base_math_func(sliced_data)
        
    return basin_metric


class DerivedAttributeRegistry:
    """Registry tracking explicit numeric attributes mapped to specific variables or groups."""

    def __init__(self):
        self._available_metrics = {}
        # Dictionary mapping group path prefixes to lists of string metric names
        self._group_assignments = {}  

    def register(self, name, func):
        self._available_metrics[name] = func

    def assign_metrics_to_group(self, path_prefix, metric_names):
        """Hardcodes exactly which metrics get computed for a specific path prefix/group hierarchy."""
        # Standardize matching boundaries by wrapping the key cleanly with slashes
        clean_prefix = "/" + path_prefix.strip("/") + "/"
        self._group_assignments[clean_prefix] = metric_names

    def compute_for_node(self, nc_file, node_path):
        """
        Computes assigned metrics if the node path belongs to a configured group hierarchy.
        If a node does not match any assignment patterns, returns an empty dict immediately
        without reading any raw NetCDF array variables from disk.
        """
        results = {}
        
        # 1. Clean path to ensure exact structural prefix bounds-matching
        clean_node_path = "/" + node_path.strip("/") + "/"
        
        # 2. Gatekeeper Check: Scan group assignments
        target_metrics = None
        for prefix, metrics in self._group_assignments.items():
            if clean_node_path.startswith(prefix):
                target_metrics = metrics
                break
                
        # If the node path does not belong to an assigned category, exit early with no IO overhead
        if not target_metrics:
            return results

        # 3. Read the variable data array safely from the file wrapper
        array = nc_file.get_variable(node_path)
        if array is None or (hasattr(array, "size") and array.size == 0):
            return results

        # 4. Loop over and execute the target metric suite
        for name in target_metrics:
            if name not in self._available_metrics:
                continue
                
            try:
                func = self._available_metrics[name]
                # Every registry metric accepts both the active file wrapper instance and data array
                val = func(nc_file, array)
                
                # Protect against database NULL insertion constraint errors
                if not np.isnan(val):
                    results[name] = float(val)
                else:
                    logger.debug(f"Metric {name} resulted in NaN for {node_path}, skipping.")
                    
            except Exception as e:
                logger.debug(f"Metric {name} failed for {node_path}: {e}")

        return results


    @classmethod
    def default(cls):
        registry = cls()
        
        # 1. Base mathematical calculation primitives (agnostic to masking states)
        math_ops = {
            "min": lambda x: np.ma.min(x) if hasattr(x, 'mask') else np.min(x),
            "max": lambda x: np.ma.max(x) if hasattr(x, 'mask') else np.max(x),
            "mean": lambda x: np.ma.mean(x) if hasattr(x, 'mask') else np.mean(x),
            "std_dev": lambda x: np.ma.std(x) if hasattr(x, 'mask') else np.std(x),
            "nobs": lambda x: int(x.count()) if hasattr(x, 'mask') else int(x.size),
            "nmissing": lambda x: int(x.size - x.count()) if hasattr(x, 'mask') else 0,
        }

        # 2. Register base flat metrics (wrapped to conform to the dual-parameter signature)
        for name, op in math_ops.items():
            registry.register(name, lambda f, x, base_op=op: base_op(x))

        # 3. Brute-force generate explicit regional permutations using named suffixes
        basin_map = {
            1: "Atlantic",
            2: "Pacific",
            3: "Indian",
            4: "Arctic",
            5: "Southern"
        }
        metrics_to_replicate = ["min", "max", "mean", "std_dev", "nobs", "nmissing"]
        
        # Compile a master suite list starting with standard flat calculations
        metrics_suite = list(math_ops.keys())

        for b_id, b_name in basin_map.items():
            for m_name in metrics_to_replicate:
                metric_key = f"{m_name}{b_name}"  # e.g., "minAtlantic", "std_devPacific", "meanSouthern"
                
                # Bind math operations inside the closure factory loop using the integer ID
                factory_func = make_basin_metric(math_ops[m_name], b_id)
                
                registry.register(metric_key, factory_func)
                metrics_suite.append(metric_key)

        # 4. HARDCODED GROUP ASSIGNMENTS
        registry.assign_metrics_to_group("/ObsValue", metrics_suite)
        registry.assign_metrics_to_group("/ombg", metrics_suite)

        return registry
