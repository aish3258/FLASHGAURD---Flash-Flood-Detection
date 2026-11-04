import pandas as pd
from pathlib import Path

# ============================================================
# PATHS
# ============================================================

EVENT_FILE = "data/raw/sikkim/historical/flood_events.csv"

FEATURE_FILE = "data/final/sikkim/features_dataset.csv"

OUTPUT_FILE = "data/final/sikkim/features_with_labels.csv"


# ============================================================
# CONFIGURATION
# ============================================================

# Approximate spatial radius in degrees.
# ~0.15° is roughly 15–17 km in Sikkim.
SPATIAL_RADIUS = 0.15

# Include one day before and after the documented event.
TIME_BUFFER_DAYS = 1


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 60)
print("LOADING DATA")
print("=" * 60)

df = pd.read_csv(FEATURE_FILE, low_memory=False)

events = pd.read_csv(EVENT_FILE, low_memory=False)

df["time"] = pd.to_datetime(df["time"])

events["start_date"] = pd.to_datetime(events["start_date"])
events["end_date"] = pd.to_datetime(events["end_date"])

print("Feature dataset shape:", df.shape)
print("Historical events:", len(events))


# ============================================================
# CLEAN COORDINATES
# ============================================================

df["latitude"] = pd.to_numeric(
    df["latitude"],
    errors="coerce"
)

df["longitude"] = pd.to_numeric(
    df["longitude"],
    errors="coerce"
)

events["latitude"] = pd.to_numeric(
    events["latitude"],
    errors="coerce"
)

events["longitude"] = pd.to_numeric(
    events["longitude"],
    errors="coerce"
)


# ============================================================
# INITIALIZE LABELS
# ============================================================

df["flood_event"] = 0

df["event_id"] = ""


# ============================================================
# FALLBACK LOCATIONS
# ============================================================
#
# S001 and S004 don't have coordinates in the event CSV.
#
# These are approximate regional locations and should NOT
# be interpreted as exact flood boundaries.
#
# We keep them only so the demonstration dataset can include
# those documented events.
# ============================================================

fallback_locations = {

    # Upper Teesta / North Sikkim
    "S001": (27.95, 88.65),

    # South Lhonak / Teesta Valley
    "S004": (27.93, 88.37),
}


# ============================================================
# PROCESS EVENTS
# ============================================================

print("\n" + "=" * 60)
print("CREATING SPATIAL + TEMPORAL EVENT LABELS")
print("=" * 60)


for _, event in events.iterrows():

    event_id = str(event["event_id"])

    event_type = str(event["event_type"])

    start_date = event["start_date"]

    end_date = event["end_date"]


    # --------------------------------------------------------
    # Coordinates
    # --------------------------------------------------------

    event_lat = event["latitude"]

    event_lon = event["longitude"]


    if pd.isna(event_lat) or pd.isna(event_lon):

        if event_id in fallback_locations:

            event_lat, event_lon = fallback_locations[event_id]

            print(
                f"\n{event_id}: using approximate coordinates "
                f"({event_lat}, {event_lon})"
            )

        else:

            print(
                f"\n{event_id}: skipped - "
                f"no coordinates available"
            )

            continue


    # --------------------------------------------------------
    # Expand event time window
    # --------------------------------------------------------

    buffered_start = (
        start_date -
        pd.Timedelta(days=TIME_BUFFER_DAYS)
    )

    buffered_end = (
        end_date +
        pd.Timedelta(days=TIME_BUFFER_DAYS)
    )


    # --------------------------------------------------------
    # Temporal mask
    # --------------------------------------------------------

    time_mask = (

        (df["time"] >= buffered_start)

        &

        (df["time"] <= buffered_end)

    )


    # --------------------------------------------------------
    # Spatial mask
    # --------------------------------------------------------

    spatial_mask = (

        (
            abs(df["latitude"] - event_lat)
            <= SPATIAL_RADIUS
        )

        &

        (
            abs(df["longitude"] - event_lon)
            <= SPATIAL_RADIUS
        )

    )


    # --------------------------------------------------------
    # Combined mask
    # --------------------------------------------------------

    event_mask = time_mask & spatial_mask


    matched = event_mask.sum()


    print(
        f"\n{event_id}"
    )

    print(
        f"  Type: {event_type}"
    )

    print(
        f"  Location: {event['location_name']}"
    )

    print(
        f"  Original dates: "
        f"{start_date.date()} → {end_date.date()}"
    )

    print(
        f"  Label window: "
        f"{buffered_start.date()} → "
        f"{buffered_end.date()}"
    )

    print(
        f"  Matched samples: {matched}"
    )


    # --------------------------------------------------------
    # Apply labels
    # --------------------------------------------------------

    df.loc[event_mask, "flood_event"] = 1

    df.loc[event_mask, "event_id"] = event_id


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
# FINAL SUMMARY
# ============================================================

print("\n" + "=" * 60)
print("LABELING COMPLETE")
print("=" * 60)

print("\nOutput:")
print(OUTPUT_FILE)

print("\nShape:")
print(df.shape)

print("\nFlood-event distribution:")
print(
    df["flood_event"].value_counts()
)

print("\nFlood-event percentage:")
print(
    df["flood_event"]
    .value_counts(normalize=True)
    .mul(100)
)

print("\nPositive samples by event:")

positive_events = (
    df[df["flood_event"] == 1]
    .groupby("event_id")
    .size()
)

print(positive_events)

print("\nDone.")