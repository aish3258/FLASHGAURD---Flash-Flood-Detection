import pandas as pd
from pathlib import Path

# ============================================================
# PATHS
# ============================================================

INPUT_FILE = "data/final/sikkim/flood_training_dataset.csv"

OUTPUT_FILE = "data/final/sikkim/balanced_training_dataset.csv"


# ============================================================
# SETTINGS
# ============================================================

# Number of negative samples to keep for every positive sample
NEGATIVE_RATIO = 10

RANDOM_STATE = 42


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 60)
print("LOADING TRAINING DATA")
print("=" * 60)

df = pd.read_csv(
    INPUT_FILE,
    low_memory=False
)

df["time"] = pd.to_datetime(df["time"])

print("Original shape:", df.shape)


# ============================================================
# SEPARATE POSITIVE / NEGATIVE SAMPLES
# ============================================================

positive = df[df["flood_event"] == 1].copy()

negative = df[df["flood_event"] == 0].copy()

print("\nOriginal classes:")
print("Flood:", len(positive))
print("Non-flood:", len(negative))


# ============================================================
# DETERMINE NUMBER OF NEGATIVE SAMPLES
# ============================================================

n_positive = len(positive)

n_negative = min(
    n_positive * NEGATIVE_RATIO,
    len(negative)
)

print(
    f"\nSelecting {n_negative} "
    f"negative samples for {n_positive} positive samples."
)


# ============================================================
# SAMPLE NEGATIVE DATA
# ============================================================

negative_sample = negative.sample(
    n=n_negative,
    random_state=RANDOM_STATE
)


# ============================================================
# COMBINE
# ============================================================

balanced = pd.concat(
    [
        positive,
        negative_sample
    ],
    ignore_index=True
)


# ============================================================
# SHUFFLE
# ============================================================

balanced = balanced.sample(
    frac=1,
    random_state=RANDOM_STATE
).reset_index(drop=True)


# ============================================================
# SAVE
# ============================================================

Path(OUTPUT_FILE).parent.mkdir(
    parents=True,
    exist_ok=True
)

balanced.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# SUMMARY
# ============================================================

print("\n" + "=" * 60)
print("BALANCED DATASET CREATED")
print("=" * 60)

print("\nOutput:")
print(OUTPUT_FILE)

print("\nShape:")
print(balanced.shape)

print("\nClass distribution:")
print(
    balanced["flood_event"].value_counts()
)

print("\nClass percentage:")
print(
    balanced["flood_event"]
    .value_counts(normalize=True)
    .mul(100)
)

print("\nEvent distribution among flood samples:")

print(
    balanced[
        balanced["flood_event"] == 1
    ]
    .groupby("event_id")
    .size()
)

print("\nDate range:")
print(
    balanced["time"].min(),
    "→",
    balanced["time"].max()
)

print("\nDone.")