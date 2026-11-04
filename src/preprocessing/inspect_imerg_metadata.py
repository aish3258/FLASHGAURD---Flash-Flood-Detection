
from pathlib import Path
import xarray as xr

ROOT = Path("data/raw/sikkim/gpm")

files = sorted(ROOT.rglob("*.nc4"))
if not files:
    files = sorted(ROOT.rglob("*.nc"))

if not files:
    raise FileNotFoundError(f"No NetCDF files found in {ROOT}")

with xr.open_dataset(files[0]) as ds:
    print("File:", files[0].name)
    print("\nDataset dimensions:")
    print(ds.sizes)

    print("\nVariables and metadata:")
    for name, var in ds.data_vars.items():
        print(f"\nVariable: {name}")
        print("Dimensions:", var.dims)
        print("Units:", var.attrs.get("units", "Not specified"))
        print("Long name:", var.attrs.get("long_name", "Not specified"))
        print("Standard name:", var.attrs.get("standard_name", "Not specified"))
