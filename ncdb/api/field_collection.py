# api/field_collection.py
import logging
from .expression import Expression

logger = logging.getLogger(__name__)

class FieldCollection(Expression):
    def __init__(self):
        self._fields = []

    def add(self, field):
        self._fields.append(field)

    def fields(self):
        return [repr(f) for f in self._fields]


    # for debugging
    def print_table(self, t1=None, t2=None, n_cycles=None):
        import pandas as pd
        """
        Gathers and prints a scannable ascii alignment table of all fields 
        currently stored inside this collection across the timeline.
        """
        nodes_to_plot = self._as_node_list()
        dfs = []

        for node in nodes_to_plot:
            active_cycles = node.cycles
            if not active_cycles:
                continue
                
            if t1 is not None: active_cycles = [c for c in active_cycles if c >= t1]
            if t2 is not None: active_cycles = [c for c in active_cycles if c <= t2]
            if n_cycles is not None: active_cycles = active_cycles[-n_cycles:]

            if not active_cycles:
                continue

            # Determine column name matching Expression.plot's schema
            if hasattr(node, "obsspace") and node.obsspace and node.obsspace.dataset:
                ds_id = node.obsspace.dataset.id
                col_name = f"{node.name} [ds_{ds_id}]"
            else:
                col_name = node.name

            records = []
            for cycle in active_cycles:
                try:
                    val_obj = node.at(cycle)
                    records.append({"time": str(cycle), col_name: float(val_obj)})
                except Exception:
                    continue

            df = pd.DataFrame(records)
            if not df.empty:
                df = df.set_index("time")
                dfs.append(df)

        if not dfs:
            print("\n[TABLE] No valid data points found across this collection.")
            return

        # Outer join to inspect missing spaces vs overlaps clearly
        master_df = dfs[0]
        for next_df in dfs[1:]:
            master_df = master_df.join(next_df, how="outer")

        master_df = master_df.sort_index()

        print("\n" + "="*80)
        print(f" FIELD COLLECTION DATA SUMMARY ({len(nodes_to_plot)} fields)")
        print("="*80)
        # Use pandas built-in string formatter to output an aligned tabular grid
        print(master_df.to_string())
        print("="*80 + "\n")
