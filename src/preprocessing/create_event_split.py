import pandas as pd
from pathlib import Path

INPUT_FILE = "data/final/sikkim/flood_training_dataset.csv"

TRAIN_FILE = "data/final/sikkim/train.csv"
TEST_FILE = "data/final/sikkim/test.csv"

# ------------------------------------------------------------
# We will test on S003 and train on S001.
# Then later we can reverse this and test S001.
# ------------------------------------------------------------

TEST_EVENT = "S003"

# Keep a small buffer around the test event out of training.
BUFFER_DAYS = 3


# ------------------------------------------------------------
# LOAD
# ------------------------------------------------------------

df = pd.read_csv(INPUT_FILE, low_memory=False)

df["time"] = pd.to_datetime(df["time"])


# ------------------------------------------------------------
# GET TEST EVENT DATES
# ------------------------------------------------------------

test_event_rows = df[
    df["event_id"] == TEST_EVENT
]

if len(test_event_rows) == 0:
    raise ValueError(
        f"No samples found for event {TEST_EVENT}"
    )


test_start = test_event_rows["time"].min()
test_end = test_event_rows["time"].max()

print("Test event:", TEST_EVENT)
print("Test event period:", test_start, "→", test_end)


# ------------------------------------------------------------
# TEST SET
# ------------------------------------------------------------

test_mask = (
    (df["event_id"] == TEST_EVENT)
)


test = df[test_mask].copy()


# ------------------------------------------------------------
# REMOVE TEST EVENT + BUFFER FROM TRAINING
# ------------------------------------------------------------

buffer_start = (
    test_start -
    pd.Timedelta(days=BUFFER_DAYS)
)

buffer_end = (
    test_end +
    pd.Timedelta(days=BUFFER_DAYS)
)


train_mask = ~(
    (df["time"] >= buffer_start)
    &
    (df["time"] <= buffer_end)
)


train = df[train_mask].copy()


# ------------------------------------------------------------
# IMPORTANT:
# The test set needs negative samples too.
# ------------------------------------------------------------

test_positive = test[
    test["flood_event"] == 1
].copy()

test_negative_pool = df[
    (df["flood_event"] == 0)
    &
    (df["time"] >= buffer_start)
    &
    (df["time"] <= buffer_end)
].copy()


# Use up to 10 negatives per positive
n_negative = min(
    len(test_negative_pool),
    len(test_positive) * 10
)

test_negative = test_negative_pool.sample(
    n=n_negative,
    random_state=42
)


test = pd.concat(
    [
        test_positive,
        test_negative
    ],
    ignore_index=True
)

test = test.sample(
    frac=1,
    random_state=42
).reset_index(drop=True)


# ------------------------------------------------------------
# SAVE
# ------------------------------------------------------------

Path(TRAIN_FILE).parent.mkdir(
    parents=True,
    exist_ok=True
)

train.to_csv(
    TRAIN_FILE,
    index=False
)

test.to_csv(
    TEST_FILE,
    index=False
)


# ------------------------------------------------------------
# SUMMARY
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("EVENT-AWARE SPLIT COMPLETE")
print("=" * 60)

print("\nTRAIN:")
print("Shape:", train.shape)
print(train["flood_event"].value_counts())

print("\nTEST:")
print("Shape:", test.shape)
print(test["flood_event"].value_counts())

print("\nTest events:")
print(test[test["flood_event"] == 1]["event_id"].value_counts())

print("\nSaved:")
print(TRAIN_FILE)
print(TEST_FILE)