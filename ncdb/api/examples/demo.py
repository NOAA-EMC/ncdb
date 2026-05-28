import logging
# logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)

import os
from datetime import datetime
from pathlib import Path

from ncdb.api import Database, FieldCollection


BASE_DIR = Path(__file__).parent
DB_DIR = BASE_DIR


from ncdb.scanners.marine_da_scanner import MarineDAScanner
SCANNER = MarineDAScanner
DATA_ROOT = "/scratch4/NCEPDEV/global/John.Steffen/hpss_arch/cp4.03-parallel-3dvar"
DATA_ROOT4 = "/scratch4/NCEPDEV/global/John.Steffen/hpss_arch/cp4.04-parallel-3dvar"
DB_PATH = f"{DB_DIR}/cp4.03-parqllel-3dvar.db"


'''
from ncdb.scanners.obsforge_scanner import ObsForgeScanner
SCANNER = ObsForgeScanner
DATA_ROOT="/lfs/h2/emc/da/noscrub/emc.da/obsForge/COMROOT/realtime"
DB_PATH = f"{DB_DIR}/emcda.db"
'''


def main():
    db = Database(DB_PATH)

    print("\n=== Datasets ===")
    print(db.datasets())

    db.scan(
        data_root=DATA_ROOT,
        n_cycles=-2,
        scanner_cls=SCANNER
    )

    db.scan(
        data_root=DATA_ROOT4,
        n_cycles=-2,
        scanner_cls=SCANNER
    )

    print("\n=== Datasets ===")
    print(db.datasets())

    # gdas = db.dataset("gdas")

    gdas_datasets = db.datasets("gdas")
    print("\n=== gdas Datasets ===")
    for ds in gdas_datasets:
        print(ds)
    gdas = gdas_datasets[0]

    print(f"\n=== loaded dataset {gdas} ===\n")

    obsspace_names = [o.name for o in gdas.obsspaces()]
    print(f"{len(obsspace_names)} obs spaces:")
    for name in sorted(obsspace_names):
        print(f"- {name}")

    sst = gdas.obsspace("sst_viirs_n20_l3u")
    print(f"Obs space: {sst.name}\n")

    variable_names = sst.list_variables()
    print(f"{len(variable_names)} variables for {sst.name}:\n")
    for name in sorted(variable_names):
        print(f"- {name}")

    lon  = sst.field("longitude")
    lat  = sst.field("latitude")
    temp = sst.field("/ObsValue/seaSurfaceTemperature")
    # ice = sst.field("ombg/seaIceFraction")

    cycles = gdas.cycles
    print(f"Available cycles for {gdas}:")
    for c in cycles:
        print(c)

    # t = datetime(2026, 4, 7, 6)
    # t = datetime(2026, 5, 1, 6)
    # t = datetime(2026, 5, 4, 12)
    t = cycles[-1]
    print(f"Requesting data at time: {t}\n")

    # lon0  = lon[t]
    # lat0  = lat[t]
    temp0 = temp[t]

    print("Data loaded:")
    # print(f"  lon shape:  {getattr(lon0.data, 'shape', 'unknown')}")
    # print(f"  lat shape:  {getattr(lat0.data, 'shape', 'unknown')}")
    print(f"  temp0 shape: {getattr(temp0.data, 'shape', 'unknown')}")
    lon0 = temp0.coords['longitude']
    lat0 = temp0.coords['latitude']
    print(f"  temp0 coordinates: {getattr(lon0, 'shape', 'unknown')}")
    print(f"  temp0 coordinates: {getattr(lat0, 'shape', 'unknown')}")

    plot_path = temp0.plot("jtemp0.png")
    print(f"Plot generated at {plot_path}")

    temp_max = temp.max
    temp_min = temp.min

    tmax = temp_max[t]
    tmin = temp_min[t]
    print(f"max temp at {t} = {tmax}")
    print(f"200 + min temp at {t} = {tmin + 200.0}")

    plot_path = temp_max.plot("jtemp_max.png")
    print(f"History plot generated at {plot_path}")

    nobs = temp.nobs
    plot_path = nobs.plot("jnobs.png")

    c = FieldCollection()
    c.add(temp.min)
    c.add(temp.max)
    c.plot("jmulti.png")

'''
    TODO:
    fields 
        lazy-evaluation;
        hold no data; encode computation graph
        are DB aware
        may trigger DB or netcdf read
    values
        in memory data

    # aggregation:
    temp = gdas.field("ObsValue/seaSurfaceTemperature", obsspaces="sst_*")

    # temporal selection may be useful for plotting, etc
    # historic plot:
    temp.between(t1, t2)
    max_temp = temp.max
    max_temp.plot("temp.png")

    # value at a given time:
    # triggers evaluation!
    # the field encodes the union; evaluation involves
    # a db query
    temp0 = temp[t]
    temp0.plot("temp0.png")

    temp1 = temp0.subset(lat=(0, 30), lon=(-80, -20))
    temp2 = temp1.where(temp1 > 300)

    # algebra:
    dt = temp0 - temp00
    max_dt = dt.max
'''


if __name__ == "__main__":
    main()
