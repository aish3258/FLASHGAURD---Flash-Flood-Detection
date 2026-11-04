
import pandas as pd

FILE = "data/final/sikkim/features_with_labels.csv"

df = pd.read_csv(FILE, low_memory=False)
df["time"] = pd.to_datetime(df["time"])

# Only inspect the two candidate rainfall-flash-flood events.
events = {
    "S001": {
        "start": "2019-06-13",
        "end": "2019-06-21",
    },
    "S003": {
        "start": "2020-06-23",
        "end": "2020-07-03",
    },
}

for event_id, dates in events.items():
    print(f"\n{'=' * 60}")
    print(f"EVENT: {event_id}")
    print(f"{'=' * 60}")

    start = pd.Timestamp(dates["start"])
    end = pd.Timestamp(dates["end"])

    period = df[
        df["time"].between(start, end)
    ].copy()

    if period.empty:
        print("No records found for this period.")
        continue

    daily = (
        period.groupby("time")
        .agg(
            imerg_mean=("imerg_rainfall", "mean"),
            imerg_max=("imerg_rainfall", "max"),
            imd_mean=("imd_rainfall", "mean"),
            imd_max=("imd_rainfall", "max"),
            rainfall_3day_mean=("rainfall_3day", "mean"),
            rainfall_7day_mean=("rainfall_7day", "mean"),
            soil_moisture_missing=(
                "soil_moisture",
                lambda s: s.isna().mean() * 100,
            ),
        )
        .reset_index()
    )

    print(
        daily.round(2).to_string(index=False)
    )

    print("\nRainfall correlation:")
    print(
        period[
            ["imerg_rainfall", "imd_rainfall"]
        ].corr().round(3)
    )

print("\nRainfall audit complete.")
