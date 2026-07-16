#!/bin/bash
# ==============================================================================
# Script to install/update NCDB and Cartopy in a virtual environment on WCOSS2
# ==============================================================================

# Exit immediately if any command fails
set -e

# --- 1. Configuration ---
INSTALL_DIR="$(pwd)"
VENV_DIR="${INSTALL_DIR}/venv"
NCDB_REPO="git+https://github.com/NOAA-EMC/ncdb.git"

# Production GEOS install path found on WCOSS2
GEOS_PATH="/apps/prod/hpc-stack/intel-19.1.3.304/geos/3.8.1"

echo "=== Starting NCDB Installation Sequence ==="
echo "Target directory: ${INSTALL_DIR}"
echo "Virtual environment: ${VENV_DIR}"

# --- 2. Load WCOSS2 Intel compiler & modules ---
echo "Loading required system modules..."
module purge
module load envvar/1.0

# 1. Load the compiler first (satisfies dependencies for python/3.12.0)
module load intel/19.1.3.304

# 2. Load the modern python version and geographical libraries
module load python/3.12.0
module load geos/3.8.1
module load proj/7.1.0

# Explicitly tell Python's build system to use the Intel compiler wrappers
export CC=cc
export CXX=CC

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
