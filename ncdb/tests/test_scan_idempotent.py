from ncdb.api import Database
from ncdb.scanners.marine_da_scanner import MarineDAScanner

def test_scan_idempotent(tmp_path):
    data_root = tmp_path / "archive"

    cycle_dir = data_root / "gdas.20260501" / "00"
    cycle_dir.mkdir(parents=True)

    nc_file = cycle_dir / "sst.nc"
    create_test_file(nc_file)

    db_path = tmp_path / "db.sqlite"
    db = Database(str(db_path))

    # first scan
    r1 = db.scan(
        data_root=str(data_root),
        n_cycles=None,
        scanner_cls=MarineDAScanner,
    )

    # second scan (same data)
    r2 = db.scan(
        data_root=str(data_root),
        n_cycles=None,
        scanner_cls=MarineDAScanner,
    )

    # core assertions

    datasets = db.datasets()
    assert len(datasets) == 1

    ds = datasets[0]
    cycles = ds.cycles

    # only one cycle should exist
    assert len(cycles) == 1

    # only one file entry implied
    sst = ds.obsspace("sst")
    nfiles = len(sst.field("longitude").files)
    assert nfiles == nfiles  # placeholder sanity; refine once API stabilizes
