
from pathlib import Path
import xarray as xr
import numpy as np
import pandas as pd

ROOT = Path("data/raw/sikkim/gpm")

EVENTS = {
    "S001": ("2019-06-13", "2019-06-19"),
    "S003": ("2020-06-23", "2020-07-03"),
}

LAT_MIN, LAT_MAX = 27.0, 28.2
LON_MIN, LON_MAX = 87.5, 89.2

files = sorted(ROOT.rglob("*.nc4"))

if not files:
    files = sorted(ROOT.rglob("*.nc"))

if not files:
    raise FileNotFoundError(
        f"No NetCDF files found under {ROOT}"
    )

print("IMERG source files found:", len(files))

for event_id, (start, end) in EVENTS.items():
    print(f"\n{'=' * 65}")
    print(f"{event_id} | Original IMERG data")
    print(f"{'=' * 65}")

    daily_values = {}

    for file in files:
        try:
            with xr.open_dataset(file) as ds:
                var_name = next(
                    (name for name in ds.data_vars
                     if "precipitation" in name.lower()),
                    None,
                )

                if var_name is None:
                    continue

                da = ds[var_name]

                # Identify coordinate names.
                lat_name = next(
                    (n for n in da.coords
                     if n.lower() in ("lat", "latitude")),
                    None,
                )
                lon_name = next(
                    (n for n in da.coords
                     if n.lower() in ("lon", "longitude")),
                    None,
                )
                time_name = next(
                    (n for n in da.coords
                     if n.lower() in ("time",)),
                    None,
                )

                if not all([lat_name, lon_name, time_name]):
                    continue

                lat = ds[lat_name]
                lon = ds[lon_name]

                region = da.where(
                    (lat >= LAT_MIN) & (lat <= LAT_MAX)
                    & (lon >= LON_MIN) & (lon <= LON_MAX),
                    drop=True,
                )

                region = region.sel(
                    {time_name: slice(start, end)}
                )

                if region.size == 0:
                    continue

                # Daily IMERG files may contain one or more
                # time steps. Aggregate the time steps per day.
                for timestamp in region[time_name].values:
                    day = pd.Timestamp(timestamp).normalize()
                    if not (
                        pd.Timestamp(start)
                        <= day
                        <= pd.Timestamp(end)
                    ):
                        continue

                    day_data = region.sel(
                        {time_name: timestamp}
                    ).values.astype(float).ravel()

                    day_data = day_data[np.isfinite(day_data)]

                    if day_data.size == 0:
                        continue

                    daily_values.setdefault(day, []).extend(
                        day_data.tolist()
                    )

        except Exception as exc:
            print("Could not read:", file.name, "|", exc)

    if not daily_values:
        print("No regional values found. Check file structure.")
        continue

    for day in sorted(daily_values):
        values = np.asarray(daily_values[day], dtype=float)

        print(
            day.date(),
            "| mean =", round(float(values.mean()), 2),
            "| max =", round(float(values.max()), 2),
            "| grid values =", values.size,
        )

print("\nIMERG regional check complete.")
