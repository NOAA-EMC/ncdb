#!/bin/bash
# ==============================================================================
# Script to install/update NCDB and Cartopy in a virtual environment on WCOSS2
# ==============================================================================

# Exit immediately if any command fails
set -e

# --- 1. Configuration ---
MONITOR_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="${MONITOR_DIR}/venv"
NCDB_REPO="git+https://github.com/givelberg/ncdb.git"

# Production GEOS install path found on WCOSS2
GEOS_PATH="/apps/prod/hpc-stack/intel-19.1.3.304/geos/3.8.1"

echo "=== Starting NCDB Installation Sequence ==="
echo "Target directory: ${MONITOR_DIR}"
echo "Virtual environment: ${VENV_DIR}"

# --- 2. Load WCOSS2 HPC Modules & Compiler Wrapper ---
echo "Loading required system modules..."
# Force Lmod to use the GNU environment (provides 'CC' compiler wrapper)
module purge
module load envvar/1.0
module load PrgEnv-gnu/8.3.3
module load gcc/12.1.0
module load python/3.8.6
module load geos
module load proj

# Verify compiler is accessible
if ! which CC &>/dev/null; then
    echo "ERROR: Compiler wrapper 'CC' not found. Ensure PrgEnv-gnu is loaded properly." >&2
    exit 1
fi

# --- 3. Export Compilation Paths for Cartopy ---
echo "Setting up GEOS paths..."
if [ ! -d "${GEOS_PATH}" ]; then
    echo "ERROR: GEOS installation path not found at ${GEOS_PATH}" >&2
    exit 1
fi

export CFLAGS="-I${GEOS_PATH}/include"
export CXXFLAGS="-I${GEOS_PATH}/include"
export LDFLAGS="-L${GEOS_PATH}/lib"
export PATH="${GEOS_PATH}/bin:${PATH}"

# --- 4. Prepare the Virtual Environment ---
if [ ! -d "${VENV_DIR}" ]; then
    echo "Creating a new virtual environment..."
    python -m venv "${VENV_DIR}"
fi

echo "Activating virtual environment..."
source "${VENV_DIR}/bin/activate"

# Upgrade pip inside the venv to ensure smooth wheel building
echo "Upgrading pip and packaging tools..."
pip install --upgrade pip setuptools wheel

# --- 5. Install NCDB and Dependencies ---
echo "Compiling Cartopy and installing NCDB..."
pip install --force-reinstall "${NCDB_REPO}"

echo "=== Installation Successful! ==="
echo "You can now run your monitor script."
