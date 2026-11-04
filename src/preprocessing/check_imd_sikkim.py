
from pathlib import Path
import xarray as xr
import numpy as np
import pandas as pd

ROOT = Path("data/raw/sikkim/imd")

EVENTS = {
    "S001": ("2019-06-13", "2019-06-19"),
    "S003": ("2020-06-23", "2020-07-03"),
}

# Broad regional box for inspection, not an event footprint.
LAT_MIN, LAT_MAX = 27.0, 28.2
LON_MIN, LON_MAX = 87.5, 89.2

for event_id, (start, end) in EVENTS.items():
    year = pd.Timestamp(start).year
    files = list(ROOT.rglob(f"RF25_ind{year}_rfp25.nc"))

    if not files:
        print(f"No IMD file found for {year}")
        continue

    print(f"\n{'=' * 65}")
    print(f"{event_id} | Original IMD data | {year}")
    print(f"{'=' * 65}")

    with xr.open_dataset(files[0]) as ds:
        rain = ds["RAINFALL"]

        region = rain.where(
            (ds["LATITUDE"] >= LAT_MIN)
            & (ds["LATITUDE"] <= LAT_MAX)
            & (ds["LONGITUDE"] >= LON_MIN)
            & (ds["LONGITUDE"] <= LON_MAX),
            drop=True,
        )

        region = region.sel(
            TIME=slice(start, end)
        )

        values = np.asarray(region.values, dtype=float)
        valid = values[np.isfinite(values)]

        print("Regional shape:", region.shape)
        print("Valid values:", valid.size)

        if valid.size:
            print("Regional minimum:", np.min(valid))
            print("Regional median:", np.median(valid))
            print("Regional 95th percentile:",
                  np.percentile(valid, 95))
            print("Regional maximum:", np.max(valid))

        print("\nDaily regional statistics:")
        for date in region["TIME"].values:
            daily = region.sel(TIME=date).values
            valid_day = daily[np.isfinite(daily)]

            if valid_day.size == 0:
                continue

            print(
                pd.Timestamp(date).date(),
                "| mean =", round(float(valid_day.mean()), 2),
                "| max =", round(float(valid_day.max()), 2),
            )

print("\nSikkim IMD check complete.")
