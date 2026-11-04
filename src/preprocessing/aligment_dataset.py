from pathlib import Path
import xarray as xr
import pandas as pd
import numpy as np


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "sikkim"

OUTPUT_DIR = PROJECT_ROOT / "data" / "final" / "sikkim"
OUTPUT_FILE = OUTPUT_DIR / "aligned_dataset.csv"


IMERG_FILE = PROCESSED_DIR / "imerg_daily.nc"
SMAP_FILE = PROCESSED_DIR / "smap_daily.nc"
IMD_FILE = PROCESSED_DIR / "imd_daily.nc"


# ============================================================
# COMMON PERIOD
# ============================================================

START_DATE = "2019-01-01"
END_DATE = "2023-12-31"


# ============================================================
# SIKKIM COMMON AREA
# ============================================================

LAT_MIN = 27.25
LAT_MAX = 28.00

LON_MIN = 88.00
LON_MAX = 88.75


# ============================================================
# LOAD DATA
# ============================================================

print("Loading datasets...")

imerg = xr.open_dataset(IMERG_FILE)
smap = xr.open_dataset(SMAP_FILE)
imd = xr.open_dataset(IMD_FILE)

print("IMERG loaded.")
print("SMAP loaded.")
print("IMD loaded.")


# ============================================================
# STANDARDIZE IMD NAMES
# ============================================================

imd = imd.rename({
    "TIME": "time",
    "LATITUDE": "latitude",
    "LONGITUDE": "longitude"
})


# ============================================================
# STANDARDIZE IMERG NAMES
# ============================================================

imerg = imerg.rename({
    "lat": "latitude",
    "lon": "longitude"
})


# ============================================================
# SELECT COMMON DATE RANGE
# ============================================================

print("\nSelecting common period...")

imerg = imerg.sel(
    time=slice(START_DATE, END_DATE)
)

smap = smap.sel(
    time=slice(START_DATE, END_DATE)
)

imd = imd.sel(
    time=slice(START_DATE, END_DATE)
)


# ============================================================
# SELECT COMMON SIKKIM AREA
# ============================================================

print("Selecting common Sikkim area...")

imerg = imerg.sel(
    latitude=slice(LAT_MIN, LAT_MAX),
    longitude=slice(LON_MIN, LON_MAX)
)

imd = imd.sel(
    latitude=slice(LAT_MIN, LAT_MAX),
    longitude=slice(LON_MIN, LON_MAX)
)


# ============================================================
# SMAP COORDINATES
# ============================================================

# SMAP uses y_global/x_global as dimensions.
# Actual geographic coordinates are stored in
# latitude_am / longitude_am and latitude_pm / longitude_pm.


print("\nPreparing SMAP coordinates...")


# Use AM geographic coordinates as the common SMAP grid.
smap_lat = smap["latitude_am"].isel(time=0)
smap_lon = smap["longitude_am"].isel(time=0)


# ============================================================
# ADD GEOGRAPHIC COORDINATES TO SMAP
# ============================================================

smap = smap.assign_coords(
    latitude=(
        ["y_global", "x_global"],
        smap_lat.values
    ),
    longitude=(
        ["y_global", "x_global"],
        smap_lon.values
    )
)


# ============================================================
# CONVERT SMAP TO LAT/LON GRID
# ============================================================

print("Preparing SMAP spatial grid...")

smap_am = smap["soil_moisture_am"]
smap_pm = smap["soil_moisture_pm"]


# ============================================================
# CREATE SMAP AVERAGE
# ============================================================

# Use AM when available.
# If AM is missing, use PM.

soil_moisture = smap_am.where(
    ~np.isnan(smap_am),
    smap_pm
)

soil_moisture.name = "soil_moisture"


# ============================================================
# CREATE COMMON GRID
# ============================================================

# We use the IMERG grid as the common grid because:
#
# - IMERG is our main rainfall source
# - It has finer spatial resolution than IMD
# - It is approximately 0.1 degree


print("\nCreating common spatial grid...")

common_lat = imerg["latitude"]
common_lon = imerg["longitude"]


# ============================================================
# SPATIAL MATCHING
# ============================================================

print("Matching IMD to IMERG grid...")

imd_aligned = imd["RAINFALL"].interp(
    latitude=common_lat,
    longitude=common_lon,
    method="nearest"
)


print("Matching SMAP to IMERG grid...")

# SMAP has 2D lat/lon coordinates.
# Use nearest-neighbour selection for each IMERG point.

smap_points = soil_moisture.stack(
    points=("y_global", "x_global")
)

smap_lat_points = smap["latitude"].stack(
    points=("y_global", "x_global")
)

smap_lon_points = smap["longitude"].stack(
    points=("y_global", "x_global")
)


# ============================================================
# BUILD SMAP DATAFRAME
# ============================================================

print("Converting SMAP coordinates...")

smap_df = pd.DataFrame({
    "latitude": smap_lat_points.values,
    "longitude": smap_lon_points.values,
})

smap_df = smap_df.dropna(
    subset=["latitude", "longitude"]
).reset_index(drop=True)


# ============================================================
# TEMPORAL ALIGNMENT
# ============================================================

print("Aligning dates...")

imerg_dates = pd.DatetimeIndex(
    imerg.time.values
)

smap_dates = pd.DatetimeIndex(
    smap.time.values
)

imd_dates = pd.DatetimeIndex(
    imd.time.values
)


common_dates = (
    imerg_dates
    .intersection(smap_dates)
    .intersection(imd_dates)
)

print(
    f"Common dates available: {len(common_dates)}"
)


# ============================================================
# PREPARE OUTPUT
# ============================================================

rows = []


# ============================================================
# PROCESS EACH DATE
# ============================================================

print("\nCreating aligned dataset...")

for i, date in enumerate(common_dates):

    if i % 100 == 0:

        print(
            f"Processing {i + 1}/{len(common_dates)}..."
        )

    # --------------------------------------------------------
    # IMERG
    # --------------------------------------------------------

    rain = imerg["precipitation"].sel(
        time=date
    )

    rain_df = rain.to_dataframe(
        name="imerg_rainfall"
    ).reset_index()


    # --------------------------------------------------------
    # IMD
    # --------------------------------------------------------

    imd_rain = imd_aligned.sel(
        time=date
    )

    imd_df = imd_rain.to_dataframe(
        name="imd_rainfall"
    ).reset_index()


    # --------------------------------------------------------
    # Merge IMERG + IMD spatially
    # --------------------------------------------------------

    merged = pd.merge(
        rain_df,
        imd_df,
        on=["latitude", "longitude"],
        how="left"
    )


    # --------------------------------------------------------
    # SMAP for this date
    # --------------------------------------------------------

    sm = soil_moisture.sel(
        time=date
    )

    sm_values = sm.values.flatten()


    # --------------------------------------------------------
    # Find nearest SMAP point
    # --------------------------------------------------------

    lat_values = merged["latitude"].values
    lon_values = merged["longitude"].values

    smap_lat_values = smap_df["latitude"].values
    smap_lon_values = smap_df["longitude"].values


    nearest_values = []


    for lat, lon in zip(
        lat_values,
        lon_values
    ):

        distance = (
            (smap_lat_values - lat) ** 2
            +
            (smap_lon_values - lon) ** 2
        )

        index = np.nanargmin(distance)

        nearest_values.append(
            sm_values[index]
        )


    merged["soil_moisture"] = nearest_values

    merged["time"] = date

    rows.append(merged)


# ============================================================
# COMBINE ALL DATES
# ============================================================

print("\nCombining all dates...")

final_df = pd.concat(
    rows,
    ignore_index=True
)


# ============================================================
# CLEAN DATA
# ============================================================

final_df = final_df[
    [
        "time",
        "latitude",
        "longitude",
        "imerg_rainfall",
        "imd_rainfall",
        "soil_moisture"
    ]
]


# Remove impossible / missing rainfall rows
final_df = final_df.dropna(
    subset=["imerg_rainfall"]
)


# ============================================================
# SORT
# ============================================================

final_df = final_df.sort_values(
    ["time", "latitude", "longitude"]
).reset_index(drop=True)


# ============================================================
# DISPLAY
# ============================================================

print("\n==========================================")
print("FINAL ALIGNED DATASET")
print("==========================================")

print("\nShape:")
print(final_df.shape)

print("\nColumns:")
print(final_df.columns.tolist())

print("\nFirst 10 rows:")
print(final_df.head(10))

print("\nMissing values:")
print(final_df.isna().sum())


# ============================================================
# SAVE
# ============================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

final_df.to_csv(
    OUTPUT_FILE,
    index=False
)


print("\n==========================================")
print("SUCCESS!")
print("==========================================")

print(
    f"Saved to:\n{OUTPUT_FILE}"
)

print(
    f"\nTotal rows: {len(final_df):,}"
)


# ============================================================
# CLOSE
# ============================================================

imerg.close()
smap.close()
imd.close()