from __future__ import annotations

import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Tuple, TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from workflow import Job, AssetType

logger = logging.getLogger(__name__)


def run_b2i_converter(job: Job) -> Tuple[List[str], AssetType]:
    """Decoupled adapter for NOAA BUFR-to-IODA converters.
    
    Loads machine modulefiles (via Lmod inside a subshell) to satisfy all C++ and Python
    dependencies (e.g. pyiodaconv, Intel MKL, eccodes) before executing the converter script.
    
    Args:
        job: Job domain object containing input assets, parameters, and metadata.

    Returns:
        Tuple[List[str], AssetType]: (List containing output NetCDF URIs, output AssetType domain object)
    """
    input_uris = job.input_asset_uris
    parameters = job.parameters

    if not input_uris:
        raise ValueError(f"[Adapter] Job #{job.id} has no input URIs.")

    input_path = Path(input_uris[0]).resolve()
    script_path_str = parameters.get("script_path")
    if not script_path_str:
        raise ValueError("[Adapter] Parameter 'script_path' is required.")

    script_path = Path(script_path_str).resolve()
    if not script_path.exists():
        raise FileNotFoundError(f"[Adapter] Converter script not found: {script_path}")

    # Determine output directory
    output_dir_str = parameters.get("output_dir")
    if output_dir_str:
        output_dir = Path(output_dir_str).resolve()
    else:
        output_dir = (input_path.parent.parent / "ioda_data").resolve()

    output_dir.mkdir(parents=True, exist_ok=True)

    # Extract cycle_datetime dynamically from filename (e.g. '2025061900-gdas...')
    filename = input_path.name
    cycle_dt = parameters.get("cycle_datetime")
    if not cycle_dt and "-" in filename:
        cycle_dt = filename.split("-")[0]
    if not cycle_dt or not cycle_dt.isdigit():
        cycle_dt = "2021063006"  # Safe default fallback

    yaml_config = {
        "data_format": parameters.get("data_format", "subpfl"),
        "subsets": parameters.get("subsets", "SUBPFL"),
        "source": parameters.get("source", "NCEP data tank"),
        "data_type": parameters.get("data_type", "argo"),
        "cycle_type": parameters.get("cycle_type", "gdas"),
        "cycle_datetime": str(cycle_dt),
        "dump_directory": str(input_path.parent),
        "ioda_directory": str(output_dir),
        "ocean_basin": parameters.get("ocean_basin", ""),
        "data_description": parameters.get("data_description", "In situ profile observation"),
        "data_provider": parameters.get("data_provider", "U.S. NOAA"),
    }

    # Write temporary runtime configuration file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp_file:
        yaml.dump(yaml_config, tmp_file, default_flow_style=False)
        config_path = tmp_file.name

    try:
        # 3. Resolve Module and PYTHONPATH Directories
        modulefiles_dir = parameters.get(
            "modulefiles_dir", 
            "/scratch3/NCEPDEV/da/Edward.Givelberg/obsForge/modulefiles/obsforge"
        )
        platform_module = parameters.get("platform_module", "ursa.intel")

        # Include BOTH the parent python3.11 directory AND site-packages
        obsforge_root = Path(modulefiles_dir).parent.parent
        py_build_lib = obsforge_root / "build" / "lib" / "python3.11"
        py_build_site = py_build_lib / "site-packages"
        script_dir = script_path.parent

        # 4. Construct Lmod execution subshell command
        bash_command = (
            f"source /etc/profile.d/modules.sh 2>/dev/null || true; "
            f"module use {modulefiles_dir}; "
            f"module load {platform_module}; "
            f"export PYTHONPATH={script_dir}:{py_build_lib}:{py_build_site}:$PYTHONPATH; "
            f"{sys.executable} {script_path} -c {config_path}"
        )

        logger.info(f"[Adapter] Executing converter for Job #{job.id} via shell...\n  Cmd: {bash_command}")

        # Execute command inside a login bash subshell so Lmod functions properly
        res = subprocess.run(
            ["/bin/bash", "-c", bash_command],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if res.returncode != 0:
            error_msg = (
                f"Converter process failed for Job #{job.id} with code {res.returncode}:\n"
                f"--- STDOUT ---\n{res.stdout}\n"
                f"--- STDERR ---\n{res.stderr}"
            )
            logger.error(f"[Adapter] {error_msg}")
            raise RuntimeError(error_msg)

        logger.info(f"[Adapter] Job #{job.id} converter execution finished successfully.")

        # 5. Resolve output NetCDF asset
        nc_files = list(output_dir.glob("*.nc"))
        if nc_files:
            latest_file = str(max(nc_files, key=os.path.getmtime).resolve())
            output_uris = [latest_file]
        else:
            output_uris = [str((output_dir / f"{input_path.stem}.nc").resolve())]

        # Directly pass the AssetType domain object defined on the Transformation blueprint
        output_asset_type = job.transformation.output_asset_types[0]
        return output_uris, output_asset_type

    finally:
        # Clean up temporary YAML file
        if os.path.exists(config_path):
            os.remove(config_path)
