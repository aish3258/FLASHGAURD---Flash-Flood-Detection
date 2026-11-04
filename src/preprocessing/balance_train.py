import pandas as pd
from pathlib import Path

INPUT_FILE = "data/final/sikkim/train.csv"
OUTPUT_FILE = "data/final/sikkim/train_balanced.csv"

NEGATIVE_RATIO = 10
RANDOM_STATE = 42


# Load
df = pd.read_csv(INPUT_FILE, low_memory=False)

positive = df[df["flood_event"] == 1].copy()
negative = df[df["flood_event"] == 0].copy()

print("Original training data:")
print("Positive:", len(positive))
print("Negative:", len(negative))


# Select negatives
n_negative = min(
    len(negative),
    len(positive) * NEGATIVE_RATIO
)

negative_sample = negative.sample(
    n=n_negative,
    random_state=RANDOM_STATE
)


# Combine
train_balanced = pd.concat(
    [positive, negative_sample],
    ignore_index=True
)


# Shuffle
train_balanced = train_balanced.sample(
    frac=1,
    random_state=RANDOM_STATE
).reset_index(drop=True)


# Save
Path(OUTPUT_FILE).parent.mkdir(
    parents=True,
    exist_ok=True
)

train_balanced.to_csv(
    OUTPUT_FILE,
    index=False
)


# Summary
print("\n======================================")
print("BALANCED TRAINING DATA")
print("======================================")

print("Shape:", train_balanced.shape)

print("\nClass distribution:")
print(train_balanced["flood_event"].value_counts())

print("\nClass percentage:")
print(
    train_balanced["flood_event"]
    .value_counts(normalize=True) * 100
)

print("\nFlood events:")
print(
    train_balanced[
        train_balanced["flood_event"] == 1
    ]["event_id"].value_counts()
)