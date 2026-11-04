import pandas as pd
from pathlib import Path

# ============================================================
# PATHS
# ============================================================

INPUT_FILE = "data/final/sikkim/features_with_labels.csv"

OUTPUT_FILE = "data/final/sikkim/flood_training_dataset.csv"


# ============================================================
# EVENTS USED FOR RAINFALL FLASH-FLOOD MODEL
# ============================================================

# Confirmed / suitable rainfall-triggered flash-flood events
VALID_EVENTS = [
    "S001",
    "S003"
]


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 60)
print("LOADING LABELED DATA")
print("=" * 60)

df = pd.read_csv(
    INPUT_FILE,
    low_memory=False
)

print("Input shape:", df.shape)


# ============================================================
# CREATE CLEAN TARGET
# ============================================================

# Start everything as non-flood
df["flood_event"] = 0


# Mark only selected rainfall flash-flood events
df.loc[
    df["event_id"].isin(VALID_EVENTS),
    "flood_event"
] = 1


# ============================================================
# REMOVE OTHER HAZARD EVENT LABELS
# ============================================================

# S002 = cloudburst + landslide
# S004 = GLOF + flash flood
#
# They are not used as positive examples for our
# rainfall-triggered flash-flood model.


# ============================================================
# SAVE
# ============================================================

Path(OUTPUT_FILE).parent.mkdir(
    parents=True,
    exist_ok=True
)

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# SUMMARY
# ============================================================

print("\n" + "=" * 60)
print("TRAINING DATASET CREATED")
print("=" * 60)

print("\nOutput:")
print(OUTPUT_FILE)

print("\nShape:")
print(df.shape)

print("\nTarget distribution:")

print(
    df["flood_event"].value_counts()
)

print("\nTarget percentage:")

print(
    df["flood_event"]
    .value_counts(normalize=True)
    .mul(100)
)

print("\nPositive samples by event:")

print(
    df[df["flood_event"] == 1]
    .groupby("event_id")
    .size()
)

print("\nUnique event IDs used:")

print(
    df[df["flood_event"] == 1]["event_id"]
    .unique()
)

print("\nDone.")