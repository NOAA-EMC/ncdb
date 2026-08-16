from pathlib import Path
from datetime import datetime

from catalog import Catalog

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
# Variables associated with an ObsSpace
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

# ============================================================
# Fields
# ============================================================

# ------------------------------------------------------------
# Register fields
# ------------------------------------------------------------

temperature = catalog.register_field(
    "temperature",
    "Sea surface temperature field",
)

longitude = catalog.register_field(
    "longitude",
    "Longitude coordinate",
)

latitude = catalog.register_field(
    "latitude",
    "Latitude coordinate",
)

receipt_date = catalog.register_field(
    "receiptDate",
    "Observation receipt date",
)

# ------------------------------------------------------------
# Associate fields with ObsSpaces
#
# Not every field has to correspond to a Variable.
# ------------------------------------------------------------

catalog.associate_field(
    pirata,
    temperature,
    variable=sst,
)

catalog.associate_field(
    pirata,
    longitude,
)

catalog.associate_field(
    pirata,
    latitude,
)

catalog.associate_field(
    pirata,
    receipt_date,
)

# ------------------------------------------------------------
# Display fields belonging to an ObsSpace
# ------------------------------------------------------------

print("\n=== PIRATA FIELDS ===")

for field in catalog.fields(pirata):
    print(field)

# ------------------------------------------------------------
# Add field instances at particular times
#
# data_product_id is currently just an ID from the DataStore.
# We are not yet creating the DataProducts here.
# ------------------------------------------------------------

t1 = datetime(2026, 8, 15, 0, 0)
t2 = datetime(2026, 8, 15, 6, 0)
t3 = datetime(2026, 8, 15, 12, 0)

catalog.register_field_time(
    temperature,
    t1,
    data_product_id=101,
)

catalog.register_field_time(
    temperature,
    t2,
    data_product_id=102,
)

catalog.register_field_time(
    temperature,
    t3,
    data_product_id=103,
)

catalog.register_field_time(
    longitude,
    t1,
    data_product_id=201,
)

catalog.register_field_time(
    longitude,
    t2,
    data_product_id=202,
)

catalog.register_field_time(
    latitude,
    t1,
    data_product_id=301,
)

# ------------------------------------------------------------
# Display field/time associations
# ------------------------------------------------------------

print("\n=== TEMPERATURE FIELD INSTANCES ===")

for field_time in catalog.times(temperature):
    print(field_time)

print("\n=== LONGITUDE FIELD INSTANCES ===")

for field_time in catalog.times(longitude):
    print(field_time)

print(
    "\n=== TEMPERATURE DATA PRODUCT ==="
)

print(
    catalog.data_product(
        temperature,
        t2,
    )
)
