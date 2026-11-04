from pathlib import Path
import xarray as xr


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

IMD_DIR = PROJECT_ROOT / "data" / "raw" / "sikkim" / "imd"

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "sikkim"
OUTPUT_FILE = OUTPUT_DIR / "imd_daily.nc"


# ============================================================
# SIKKIM BOUNDING BOX
# ============================================================

# Approximate Sikkim region
LAT_MIN = 27.08
LAT_MAX = 28.14

LON_MIN = 88.00
LON_MAX = 88.93


# ============================================================
# FIND IMD FILES
# ============================================================

files = sorted(IMD_DIR.rglob("*.nc"))

print(f"Found {len(files)} IMD files.")

if len(files) == 0:
    raise FileNotFoundError(
        f"No .nc files found inside: {IMD_DIR}"
    )


# ============================================================
# READ AND EXTRACT SIKKIM
# ============================================================

datasets = []

print("\nReading IMD files...\n")

for i, file in enumerate(files, start=1):

    print(f"Reading {i}/{len(files)}: {file.name}")

    ds = xr.open_dataset(file)

    # --------------------------------------------------------
    # Extract Sikkim region
    # --------------------------------------------------------

    sikkim = ds["RAINFALL"].sel(
        LATITUDE=slice(LAT_MIN, LAT_MAX),
        LONGITUDE=slice(LON_MIN, LON_MAX)
    )

    datasets.append(sikkim)

    ds.close()


# ============================================================
# COMBINE ALL YEARS
# ============================================================

print("\nCombining IMD rainfall data...")

combined = xr.concat(
    datasets,
    dim="TIME"
)


# ============================================================
# SORT BY DATE
# ============================================================

combined = combined.sortby("TIME")


# ============================================================
# DISPLAY INFORMATION
# ============================================================

print("\n===================================")
print("Combined IMD Sikkim dataset:")
print(combined)

print("\nDimensions:")
print(combined.dims)

print("\nShape:")
print(combined.shape)

print("\nLatitude:")
print(combined.LATITUDE.values)

print("\nLongitude:")
print(combined.LONGITUDE.values)

print("\nMinimum rainfall:")
print(float(combined.min().values))

print("\nMaximum rainfall:")
print(float(combined.max().values))

print("===================================")


# ============================================================
# SAVE
# ============================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

combined.to_netcdf(
    OUTPUT_FILE
)

print("\nIMD processing completed!")

print("Saved to:")
print(OUTPUT_FILE)

print("===================================")