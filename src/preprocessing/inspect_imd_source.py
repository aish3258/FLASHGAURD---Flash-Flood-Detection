
from pathlib import Path
import xarray as xr
import numpy as np

ROOT = Path("data/raw/sikkim/imd")

files = sorted(ROOT.rglob("*.nc"))

if not files:
    files = sorted(ROOT.rglob("*.nc4"))

if not files:
    raise FileNotFoundError(
        f"No .nc or .nc4 files found under {ROOT}"
    )

print("IMD source files found:", len(files))

for file in files:
    print("\n" + "=" * 70)
    print("FILE:", file)

    with xr.open_dataset(file) as ds:
        print("\nDataset dimensions:")
        print(ds.sizes)

        print("\nDataset variables:")
        print(list(ds.data_vars))

        var_name = next(
            (name for name in ds.data_vars
             if name.upper() == "RAINFALL"),
            None,
        )

        if var_name is None:
            print("No RAINFALL variable found.")
            continue

        rain = ds[var_name]

        print("\nRainfall metadata:")
        print("Dimensions:", rain.dims)
        print("Shape:", rain.shape)
        print("Attributes:", rain.attrs)

        values = np.asarray(rain.values, dtype=float)
        valid = values[np.isfinite(values)]

        if valid.size:
            print("\nRainfall statistics:")
            print("Valid count:", valid.size)
            print("Minimum:", np.min(valid))
            print("50th percentile:", np.percentile(valid, 50))
            print("95th percentile:", np.percentile(valid, 95))
            print("99th percentile:", np.percentile(valid, 99))
            print("Maximum:", np.max(valid))

        print("\nTime coordinate:")
        for name in ds.coords:
            if name.upper() in ("TIME", "LATITUDE", "LONGITUDE"):
                coord = ds[name]
                print(
                    name,
                    "size =", coord.size,
                    "first =", coord.values[0],
                    "last =", coord.values[-1],
                )

print("\nInspection complete.")
