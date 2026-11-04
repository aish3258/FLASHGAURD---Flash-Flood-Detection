from pathlib import Path
import xarray as xr
import numpy as np


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SMAP_DIR = PROJECT_ROOT / "data" / "raw" / "sikkim" / "smap"

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "sikkim"
OUTPUT_FILE = OUTPUT_DIR / "smap_daily.nc"


# ============================================================
# FIND SMAP FILES
# ============================================================

files = sorted(SMAP_DIR.rglob("*.nc4"))

print(f"Found {len(files)} SMAP files.")

if len(files) == 0:
    raise FileNotFoundError(
        f"No .nc4 files found inside: {SMAP_DIR}"
    )


# ============================================================
# READ FILES
# ============================================================

am_data = []
pm_data = []

print("\nReading SMAP files...\n")


for i, file in enumerate(files, start=1):

    print(f"Reading {i}/{len(files)}: {file.name}")

    # --------------------------------------------------------
    # AM GROUP
    # --------------------------------------------------------

    am = xr.open_dataset(
        file,
        group="Soil_Moisture_Retrieval_Data_AM"
    )

    am_soil = am["soil_moisture"]

    am_lat = am["latitude"]
    am_lon = am["longitude"]

    # --------------------------------------------------------
    # PM GROUP
    # --------------------------------------------------------

    pm = xr.open_dataset(
        file,
        group="Soil_Moisture_Retrieval_Data_PM"
    )

    pm_soil = pm["soil_moisture_pm"]

    pm_lat = pm["latitude_pm"]
    pm_lon = pm["longitude_pm"]

    # --------------------------------------------------------
    # Convert invalid values to NaN
    # --------------------------------------------------------

    am_soil = am_soil.where(am_soil >= 0)

    pm_soil = pm_soil.where(pm_soil >= 0)

    # --------------------------------------------------------
    # Add time from filename
    # --------------------------------------------------------

    filename = file.name

    # Example:
    # SMAP_L3_SM_P_E_20210102_....

    date_string = filename.split("_")[5]

    date = np.datetime64(
        f"{date_string[:4]}-{date_string[4:6]}-{date_string[6:8]}"
    )

    # --------------------------------------------------------
    # Store data
    # --------------------------------------------------------

    am_data.append(
        xr.Dataset(
            {
                "soil_moisture_am": am_soil,
                "latitude_am": am_lat,
                "longitude_am": am_lon,
            }
        ).expand_dims(time=[date])
    )

    pm_data.append(
        xr.Dataset(
            {
                "soil_moisture_pm": pm_soil,
                "latitude_pm": pm_lat,
                "longitude_pm": pm_lon,
            }
        ).expand_dims(time=[date])
    )

    am.close()
    pm.close()


# ============================================================
# COMBINE ALL DATES
# ============================================================

print("\nCombining AM data...")

am_combined = xr.concat(
    am_data,
    dim="time"
)

print("Combining PM data...")

pm_combined = xr.concat(
    pm_data,
    dim="time"
)


# ============================================================
# COMBINE AM + PM
# ============================================================

combined = xr.merge(
    [
        am_combined,
        pm_combined
    ]
)


# ============================================================
# SORT BY DATE
# ============================================================

combined = combined.sortby("time")


# ============================================================
# DISPLAY INFORMATION
# ============================================================

print("\n===================================")
print("Combined SMAP dataset:")
print(combined)

print("\nDimensions:")
print(combined.dims)

print("\nVariables:")
print(list(combined.data_vars))

print("\n===================================")


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

print("\nSMAP processing completed!")

print("Saved to:")
print(OUTPUT_FILE)

print("===================================")