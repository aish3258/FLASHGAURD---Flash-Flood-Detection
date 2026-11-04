import pandas as pd
import numpy as np

INPUT_FILE = "data/final/sikkim/features_with_labels.csv"
OUTPUT_FILE = "data/final/sikkim/ml_dataset.csv"

# ---------------------------------------------------------
# LOAD
# ---------------------------------------------------------

df = pd.read_csv(INPUT_FILE)

df["time"] = pd.to_datetime(df["time"])

# Make sure rows are ordered correctly
df = df.sort_values(
    ["latitude", "longitude", "time"]
).reset_index(drop=True)


# ---------------------------------------------------------
# RAINFALL FEATURES
# ---------------------------------------------------------

print("Creating rainfall features...")


# IMERG cumulative rainfall
df["imerg_rainfall_3day"] = (
    df.groupby(["latitude", "longitude"])["imerg_rainfall"]
      .transform(lambda x: x.rolling(3, min_periods=1).sum())
)

df["imerg_rainfall_7day"] = (
    df.groupby(["latitude", "longitude"])["imerg_rainfall"]
      .transform(lambda x: x.rolling(7, min_periods=1).sum())
)


# IMD cumulative rainfall
df["imd_rainfall_3day"] = (
    df.groupby(["latitude", "longitude"])["imd_rainfall"]
      .transform(lambda x: x.rolling(3, min_periods=1).sum())
)

df["imd_rainfall_7day"] = (
    df.groupby(["latitude", "longitude"])["imd_rainfall"]
      .transform(lambda x: x.rolling(7, min_periods=1).sum())
)


# ---------------------------------------------------------
# RAINFALL INTENSITY FEATURES
# ---------------------------------------------------------

df["imerg_rainfall_change"] = (
    df.groupby(["latitude", "longitude"])["imerg_rainfall"]
      .diff()
)

df["imd_rainfall_change"] = (
    df.groupby(["latitude", "longitude"])["imd_rainfall"]
      .diff()
)


# ---------------------------------------------------------
# DATE FEATURES
# ---------------------------------------------------------

df["month"] = df["time"].dt.month
df["day_of_year"] = df["time"].dt.dayofyear


# ---------------------------------------------------------
# SMAP MISSING VALUE INDICATOR
# ---------------------------------------------------------

# IMPORTANT:
# We do NOT replace missing SMAP with zero.

df["smap_missing"] = df["soil_moisture"].isna().astype(int)


# ---------------------------------------------------------
# SAVE
# ---------------------------------------------------------

df.to_csv(OUTPUT_FILE, index=False)

print("\n======================================")
print("FEATURE ENGINEERING COMPLETE")
print("======================================")

print("\nShape:")
print(df.shape)

print("\nColumns:")
print(df.columns.tolist())

print("\nMissing values:")
print(df.isnull().sum())

print("\nFlood labels:")
print(df["flood_event"].value_counts())

print("\nSaved to:")
print(OUTPUT_FILE)