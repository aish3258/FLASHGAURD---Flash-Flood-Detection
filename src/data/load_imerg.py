from pathlib import Path
import xarray as xr


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

GPM_DIR = PROJECT_ROOT / "data" / "raw" / "sikkim" / "gpm"

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "sikkim"
OUTPUT_FILE = OUTPUT_DIR / "imerg_daily.nc"


# ============================================================
# FIND IMERG FILES
# ============================================================

files = sorted(GPM_DIR.rglob("*.nc4"))

print(f"Found {len(files)} IMERG files.")

if len(files) == 0:
    raise FileNotFoundError(
        f"No .nc4 files found inside: {GPM_DIR}"
    )


# Show first few files
print("\nFirst few files:")

for file in files[:5]:
    print(file)


# ============================================================
# OPEN IMERG FILES
# ============================================================

print("\nOpening IMERG files...")

datasets = []

for i, file in enumerate(files, start=1):

    print(f"Reading {i}/{len(files)}: {file.name}")

    ds = xr.open_dataset(
        file,
        engine="netcdf4"
    )

    datasets.append(ds)


# ============================================================
# COMBINE ALL DAILY DATASETS
# ============================================================

print("\nCombining datasets...")

combined = xr.concat(
    datasets,
    dim="time"
)


# ============================================================
# KEEP ONLY PRECIPITATION
# ============================================================

rainfall = combined["precipitation"]


print("\nCombined rainfall dataset:")
print(rainfall)


# ============================================================
# BASIC INFORMATION
# ============================================================

print("\nDimensions:")
print(rainfall.dims)

print("\nShape:")
print(rainfall.shape)

print("\nMinimum rainfall:")
print(float(rainfall.min().values))

print("\nMaximum rainfall:")
print(float(rainfall.max().values))


# ============================================================
# SAVE PROCESSED DATA
# ============================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

rainfall.to_netcdf(OUTPUT_FILE)

print("\n===================================")
print("IMERG processing completed!")
print("Saved to:")
print(OUTPUT_FILE)
print("===================================")