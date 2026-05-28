import numpy as np
from netCDF4 import Dataset

from datetime import datetime

from ncdb.api import Database
from ncdb.scanners.marine_da_scanner import MarineDAScanner



def create_test_file(path):

    nc = Dataset(path, "w")

    #
    # dimensions
    #
    nc.createDimension("nlocs", 3)

    #
    # groups
    #
    obs = nc.createGroup("ObsValue")
    meta = nc.createGroup("MetaData")

    #
    # variables
    #
    temp = obs.createVariable(
        "seaSurfaceTemperature",
        "f4",
        ("nlocs",)
    )

    lat = meta.createVariable(
        "latitude",
        "f4",
        ("nlocs",)
    )

    lon = meta.createVariable(
        "longitude",
        "f4",
        ("nlocs",)
    )

    #
    # data
    #
    temp[:] = np.array([300.0, 301.0, 302.0])

    lat[:] = np.array([10.0, 20.0, 30.0])

    lon[:] = np.array([100.0, 110.0, 120.0])

    nc.close()


def test_end_to_end_scan(tmp_path):

    #
    # synthetic archive
    #
    data_root = tmp_path / "archive"

    cycle_dir = (
        data_root /
        "gdas.20260501" /
        "00"
    )

    cycle_dir.mkdir(parents=True)

    nc_path = cycle_dir / "sst.nc"

    create_test_file(nc_path)

    #
    # database
    #
    db_path = tmp_path / "test.db"

    db = Database(str(db_path))

    #
    # scan
    #
    report = db.scan(
        data_root=str(data_root),
        n_cycles=None,
        scanner_cls=MarineDAScanner
    )

    assert report["status"] == "success"
    assert report["datasets_discovered"] == 1
    assert report["cycles_scanned"] == 1

    #
    # dataset access
    #
    datasets = db.datasets("gdas")

    assert len(datasets) == 1

    gdas = datasets[0]

    #
    # obsspace access
    #
    obsspaces = gdas.obsspaces()

    assert len(obsspaces) == 1

    sst = gdas.obsspace("sst")

    #
    # field access
    #
    temp = sst.field(
        "/ObsValue/seaSurfaceTemperature"
    )

    #
    # cycle access
    #
    cycles = gdas.cycles

    assert len(cycles) == 1

    t = cycles[0]

    #
    # value load
    #
    value = temp[t]

    assert value.data.shape == (3,)

    #
    # coordinates
    #
    assert "latitude" in value.coords
    assert "longitude" in value.coords

    #
    # actual values
    #
    assert float(value.data[0]) == 300.0
