import os
from .engines import MatplotlibEngine, PlotlyEngine

def get_engine(out_file: str, engine_override: str = None) -> "PlottingEngine":
    if engine_override:
        if engine_override.lower() == "plotly": return PlotlyEngine()
        return MatplotlibEngine()
    
    # Auto-fallback based strictly on extension layout string
    if out_file.endswith(".html"):
        return PlotlyEngine()
    return MatplotlibEngine()
