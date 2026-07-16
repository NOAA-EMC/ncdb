# ncdb

`ncdb` stands for NetCDF Database (utilizing SQLite). It is a lightweight, pure-domain Python library designed to perform computations with datasets, which are collections of NetCDF files representing observation spaces (`obsspaces`). 

Instead of allowing metadata to remain scattered across erratic file names, directory tree layouts, and the internal headers of raw NetCDF files, `ncdb` utilizes a compact database file to index and hold all metadata associated with your datasets in a single, structured location. Adopting `ncdb` completely eliminates the need for maintaining massive collections of nested YAML files, which traditionally serve as highly inefficient, static, and partial databases. 

Customized **scanners** are provided to act as the architectural bridge, translating these chaotic real-world file layouts directly into the unified database representation. Beyond structural layout indexes, the library also computes and stores valuable derived data directly in the tracking database—such as the number of observations (`nobs`), maximums, minimums, and means for specified variables across your NetCDF files—enabling instant historical trend queries without repetitive disk I/O.

## Installation

### Option 1: Standard Installation (Local/Generic Systems)

1. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

2. Install ncdb directly from the repository:

```bash
pip install git+https://github.com/NOAA-EMC/ncdb.git
```

### Option 2: WCOSS2 Installation


1. Clone the repository to your WCOSS2 workspace:

```bash
git clone [https://github.com/NOAA-EMC/ncdb.git](https://github.com/NOAA-EMC/ncdb.git)
```

2. Source the installation script to load modules, compile dependencies, and activate the venv virtual environment:

```bash
source ncdb/ncdb/scripts/wcoss2_install_ncdb.sh
```

## Basic Usage

See the example in api/examples/demo.py

