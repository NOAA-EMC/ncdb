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

JOHNS_DATA_DIR="/scratch4/NCEPDEV/global/John.Steffen/hpss_arch"
EXPERIMENTS = [
    "cp4.04-parallel-3dvar",
    "cp4.04-parallel-hybrid",
    "retrov17_01_realtime"
]

SCANNER = "marine_da"
DB_PATH = f"{DB_DIR}/marine-da.db"


'''
SCANNER = "obsforge"
DATA_ROOT="/lfs/h2/emc/da/noscrub/emc.da/obsForge/COMROOT/realtime"
DB_PATH = f"{DB_DIR}/emcda.db"
'''


def main():
    db = Database(DB_PATH)

    for experiment in EXPERIMENTS:
        DATA_ROOT = JOHNS_DATA_DIR + "/" + experiment
        db.scan(
            data_root=DATA_ROOT,
            n_cycles=-1,
            scanner=SCANNER
        )

    print("\n=== Datasets ===")
    for ds in db.datasets():
        print(f"- {ds}")

    # get all datasets named gdas:
    gdas_datasets = db.datasets("gdas")
    print("\n=== gdas Datasets ===")
    for ds in gdas_datasets:
        print(f"Dataset object: {ds} ID: {ds.id}")
        cycles = ds.cycles
        print(f"Available cycles for {ds}:")
        for c in cycles:
            print(c)

    gdas = gdas_datasets[0]

    obsspace_names = [o.name for o in gdas.obsspaces()]
    print(f"{len(obsspace_names)} obs spaces in {gdas}:")
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

    rads_adt_c2 = gdas.obsspace("rads_adt_c2")
    # rads_adt_c2_ombg_adt = rads_adt_c2.variable("/ombg/absoluteDynamicTopography")
    adt = rads_adt_c2.field("/ombg/absoluteDynamicTopography")
    adt_cycles = adt.cycles
    print(f"Available cycles for {adt}:")
    for c in adt_cycles:
        print(c)

    # t = datetime(2026, 4, 7, 6)
    # t = datetime(2026, 5, 1, 6)
    # t = datetime(2026, 5, 4, 12)
    t = temp.cycles[-1]
    print(f"Requesting data at time: {t}\n")

    # lon0  = lon[t]
    # lat0  = lat[t]
    temp0 = temp[t]

    # print("Data loaded:")
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

    temp_mean = temp.mean
    print(f"Attributes for {temp}:\n{temp.list_attributes()}")
    temp_std_dev = temp.std_dev
    plot_path = temp_mean.plot("jtemp_band.png", band = temp_std_dev)

    # Extract the first and last available cycles 
    available_cycles = temp_mean.cycles
    if not available_cycles:
        raise ValueError("No available cycles found for this field.")

    t1 = available_cycles[0]   # First available cycle
    t2 = available_cycles[-1]  # Last available cycle

    moving_avg_mean = temp_mean.moving_avg()
    moving_avg_mean.plot(
        out_file="jtemp_smoothed_history.png",
        band=temp_std_dev,
        t1=t1,
        t2=t2
    )

    nobs = temp.nobs
    nobs_std_dev = nobs.moving_std_dev()
    # c = FieldCollection()
    # c.add(nobs)
    # c.add(nobs_std_dev)
    # plot_path = c.plot("jnobs.png")
    plot_path = nobs.plot("jnobs_std_dev.png", band=nobs_std_dev)

    c = FieldCollection()
    c.add(temp.min)
    c.add(temp.max)
    c.add(temp.mean)
    c.add(moving_avg_mean)
    c.plot("jjjmulti.png")

    c = FieldCollection()
    for ds in gdas_datasets:
        sst = ds.obsspace("sst_viirs_n20_l3u")
        temp = sst.field("/ombg/seaSurfaceTemperature")
        c.add(temp.mean)
    # c.print_table()
    # for f in c._fields:
        # print("---->")
        # f.print_table()
    c.plot("jmulti.png")
    print(f"generated plot for {c.fields()}")

    # Force a wider window or alternative bounds to see if the timeline formatting layer is clipping vectors
    # c.plot("jjmulti.png", t1=datetime(2026, 4, 1)) 

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

    # restriction to ocean basin:
    sst = gdas.obsspace("sst_viirs_n20_l3u")
    temp = sst.field("/ObsValue/seaSurfaceTemperature")
    ocean_basin = sst.field("/Metadata/ocean_basin")
    temp_atlantic = temp.where(ocean_basin=2)
    temp_atlantic_mean = temp_atlantic.mean
    temp_atlantic_rmse = temp_atlantic.rmse
    temp_atlantic_mean.plot("file.png", band=temp_atlantic_rmse) 


'''


if __name__ == "__main__":
    main()
