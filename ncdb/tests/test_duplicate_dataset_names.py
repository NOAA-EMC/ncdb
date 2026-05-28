import numpy as np

from netCDF4 import Dataset

from ncdb.api import Database
from ncdb.scanners.marine_da_scanner import MarineDAScanner


def create_test_file(path, value):

    nc = Dataset(path, "w")

    nc.createDimension("nlocs", 1)

    obs = nc.createGroup("ObsValue")
    meta = nc.createGroup("MetaData")

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

    temp[:] = np.array([value])

    lat[:] = np.array([10.0])

    lon[:] = np.array([100.0])

    nc.close()


def build_archive(root, dataset_name, value):

    cycle_dir = (
        root /
        f"{dataset_name}.20260501" /
        "00"
    )

    cycle_dir.mkdir(parents=True)

    create_test_file(
        cycle_dir / "sst.nc",
        value
    )


def test_duplicate_dataset_names(tmp_path):

    #
    # two different roots
    #
    root1 = tmp_path / "archive1"
    root2 = tmp_path / "archive2"

    #
    # same dataset name
    #
    build_archive(root1, "gdas", 300.0)
    build_archive(root2, "gdas", 999.0)

    #
    # db
    #
    db_path = tmp_path / "test.db"

    db = Database(str(db_path))

    #
    # scan both roots
    #
    db.scan(
        data_root=str(root1),
        n_cycles=None,
        scanner_cls=MarineDAScanner
    )

    db.scan(
        data_root=str(root2),
        n_cycles=None,
        scanner_cls=MarineDAScanner
    )

    #
    # verify two datasets exist
    #
    datasets = db.datasets("gdas")

    assert len(datasets) == 2

    #
    # verify roots differ
    #
    roots = sorted(
        d.root_dir
        for d in datasets
    )

    assert roots == sorted([
        str(root1),
        str(root2),
    ])

    #
    # verify data separation
    #
    values = []

    for ds in datasets:

        sst = ds.obsspace("sst")

        temp = sst.field(
            "/ObsValue/seaSurfaceTemperature"
        )

        t = ds.cycles[0]

        value = float(temp[t].data[0])

        values.append(value)

    assert sorted(values) == [300.0, 999.0]
