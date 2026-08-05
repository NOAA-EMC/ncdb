from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, List

from asset_type import AssetType
from transformation import Transformation

if TYPE_CHECKING:
    from workflow import Workflow

logger = logging.getLogger(__name__)

# Clean, static registry: (category, stream_id, bufr_format)
# NO hardcoded cycle dates!
B2I_CONVERTER_REGISTRY = [
    # Profiles
    ("profile", "argo", "subpfl"),
    ("profile", "glider", "subpfl"),
    ("profile", "bathy", "bathy"),
    ("profile", "tesac", "tesac"),
    ("profile", "xbtctd", "xbtctd"),
    ("profile", "taotriton_temp", "mbuoyb"),
    ("profile", "taotriton_saln", "mbuoyb"),
    ("profile", "pirata_temp", "mbuoyb"),
    ("profile", "pirata_saln", "mbuoyb"),
    ("profile", "rama_temp", "mbuoyb"),
    ("profile", "rama_saln", "mbuoyb"),
    
    # Surface
    ("surface", "ndbc", "mbuoyb"),
    ("surface", "trkob", "trkob"),
    ("surface", "dbuoyb_drifter", "dbuoyb"),
]


def register_all_b2i_converters(
    workflow: Workflow,
    obsforge_dir: str | Path = "/scratch3/NCEPDEV/da/Edward.Givelberg/obsForge",
    platform_module: str = "ursa.intel",
    ocean_basin_path: str = "/scratch3/NCEPDEV/da/common/validation/RECCAP2_region_masks_all_v20221025.nc",
    output_base_dir: str | Path | None = None
) -> List[str]:
    """Registers asset types and transformations for BUFR-to-IODA converters."""
    obsforge_dir = Path(obsforge_dir).resolve()
    script_dir = obsforge_dir / "utils" / "b2i"
    modulefiles_dir = obsforge_dir / "modulefiles" / "obsforge"

    if output_base_dir is None:
        output_dir = Path.cwd() / "ioda_data"
    else:
        output_dir = Path(output_base_dir).resolve()

    registered_transformations = []

    for category, stream_id, bufr_format in B2I_CONVERTER_REGISTRY:
        trans_name = f"b2i_{stream_id}"
        script_filename = f"bufr2ioda_insitu_{category}_{stream_id}.py"
        script_path = script_dir / script_filename

        # Standardized BUFR input asset type name based on format (e.g. bufr_mbuoyb, bufr_subpfl)
        bufr_asset_type_name = f"bufr_{bufr_format}"
        ioda_asset_type_name = f"ioda_{stream_id}"

        # Register Asset Types using domain objects
        in_type = workflow.register_asset_type(
            AssetType(
                name=bufr_asset_type_name,
                description=f"Raw BUFR input in {bufr_format} format"
            )
        )
        out_type = workflow.register_asset_type(
            AssetType(
                name=ioda_asset_type_name,
                description=f"IODA NetCDF output for {stream_id}"
            )
        )

        # Register Transformation using Transformation domain object
        workflow.register_transformation(
            Transformation(
                name=trans_name,
                handler="adapter:run_b2i_converter",
                input_asset_types=[in_type],
                output_asset_types=[out_type],
                parameters={
                    "script_path": str(script_path),
                    "modulefiles_dir": str(modulefiles_dir),
                    "platform_module": platform_module,
                    "ocean_basin": ocean_basin_path,
                    "data_format": bufr_format,
                    "data_type": stream_id,
                    "output_asset_type": ioda_asset_type_name,
                    "output_dir": str(output_dir)
                }
            )
        )

        logger.info(f"Registered transformation '{trans_name}' [{bufr_asset_type_name} -> {ioda_asset_type_name}]")
        registered_transformations.append(trans_name)

    return registered_transformations
