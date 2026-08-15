from pathlib import Path

from domain.catalog import Catalog


DB = Path(__file__).with_name("demo_catalog.db")

if DB.exists():
    DB.unlink()


catalog = Catalog(str(DB))


# ------------------------------------------------------------
# Variables
# ------------------------------------------------------------

sst = catalog.register_variable(
    "seaSurfaceTemperature",
    "Sea surface temperature",
)

salinity = catalog.register_variable(
    "salinity",
    "Sea water salinity",
)

wind = catalog.register_variable(
    "windSpeed",
    "Surface wind speed",
)


# ------------------------------------------------------------
# ObsSpaces
# ------------------------------------------------------------

pirata = catalog.register_obs_space(
    "pirata",
    "Measurements from PIRATA buoy instruments",
)

viirs = catalog.register_obs_space(
    "viirs_n21",
    "VIIRS satellite observations",
)

argo = catalog.register_obs_space(
    "argo",
    "Argo profiling float observations",
)


# ------------------------------------------------------------
# Scientific relationships
# ------------------------------------------------------------

catalog.associate(pirata, sst)
catalog.associate(pirata, salinity)

catalog.associate(viirs, sst)

catalog.associate(argo, sst)
catalog.associate(argo, salinity)


# ------------------------------------------------------------
# Display variables
# ------------------------------------------------------------

print("=== VARIABLES ===")

for variable in catalog.list_variables():
    print(variable)


# ------------------------------------------------------------
# Display ObsSpaces
# ------------------------------------------------------------

print("\n=== OBS SPACES ===")

for obs_space in catalog.list_obs_spaces():
    print(obs_space)


# ------------------------------------------------------------
# Variables measured by an ObsSpace
# ------------------------------------------------------------

print("\n=== PIRATA VARIABLES ===")

for variable in catalog.variables(pirata):
    print(variable)


print("\n=== VIIRS VARIABLES ===")

for variable in catalog.variables(viirs):
    print(variable)


# ------------------------------------------------------------
# ObsSpaces associated with a Variable
# ------------------------------------------------------------

print("\n=== SST OBS SPACES ===")

for obs_space in catalog.obs_spaces(sst):
    print(obs_space)


print("\n=== SALINITY OBS SPACES ===")

for obs_space in catalog.obs_spaces(salinity):
    print(obs_space)
