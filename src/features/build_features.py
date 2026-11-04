from pathlib import Path
import pandas as pd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "final"
    / "sikkim"
    / "aligned_dataset.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "final"
    / "sikkim"
)

OUTPUT_FILE = OUTPUT_DIR / "features_dataset.csv"


# ============================================================
# LOAD DATA
# ============================================================

print("Loading aligned dataset...")

df = pd.read_csv(INPUT_FILE)

df["time"] = pd.to_datetime(df["time"])

print(f"Rows loaded: {len(df):,}")


# ============================================================
# SORT DATA
# ============================================================

df = df.sort_values(
    ["latitude", "longitude", "time"]
).reset_index(drop=True)


# ============================================================
# RAINFALL FEATURES
# ============================================================

print("\nCreating rainfall features...")


# Rainfall of the current day
df["rainfall_1day"] = (
    df.groupby(["latitude", "longitude"])["imerg_rainfall"]
    .transform(
        lambda x: x.rolling(
            window=1,
            min_periods=1
        ).sum()
    )
)


# Previous 3 days + current day
df["rainfall_3day"] = (
    df.groupby(["latitude", "longitude"])["imerg_rainfall"]
    .transform(
        lambda x: x.rolling(
            window=3,
            min_periods=1
        ).sum()
    )
)


# Previous 7 days + current day
df["rainfall_7day"] = (
    df.groupby(["latitude", "longitude"])["imerg_rainfall"]
    .transform(
        lambda x: x.rolling(
            window=7,
            min_periods=1
        ).sum()
    )
)


# ============================================================
# KEEP REQUIRED FEATURES
# ============================================================

df = df[
    [
        "time",
        "latitude",
        "longitude",
        "imerg_rainfall",
        "rainfall_1day",
        "rainfall_3day",
        "rainfall_7day",
        "imd_rainfall",
        "soil_moisture"
    ]
]


# ============================================================
# DISPLAY
# ============================================================

print("\n==========================================")
print("FEATURE DATASET")
print("==========================================")

print("\nShape:")
print(df.shape)

print("\nColumns:")
print(df.columns.tolist())

print("\nFirst 10 rows:")
print(df.head(10))

print("\nMissing values:")
print(df.isna().sum())


# ============================================================
# SAVE
# ============================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

df.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\n==========================================")
print("Feature engineering completed!")
print("==========================================")

print(f"Saved to:\n{OUTPUT_FILE}")