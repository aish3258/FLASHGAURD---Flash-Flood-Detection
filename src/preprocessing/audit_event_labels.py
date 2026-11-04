
import pandas as pd

EVENT_FILE = "data/raw/sikkim/historical/flood_events.csv"
LABEL_FILE = "data/final/sikkim/features_with_labels.csv"

events = pd.read_csv(EVENT_FILE, low_memory=False)
df = pd.read_csv(LABEL_FILE, low_memory=False)

df["time"] = pd.to_datetime(df["time"])

print("\n===== DATASET SUMMARY =====")
print("Total rows:", len(df))
print("Positive rows:", (df["flood_event"] == 1).sum())
print("Negative rows:", (df["flood_event"] == 0).sum())

print("\n===== EVENT-BY-EVENT AUDIT =====")

for _, event in events.iterrows():
    event_id = str(event["event_id"])

    matched = df[
        (df["flood_event"] == 1)
        & (df["event_id"].astype(str) == event_id)
    ]

    print(f"\nEvent: {event_id}")
    print("Type:", event["event_type"])
    print("Reported location:", event["location_name"])
    print("Labeled samples:", len(matched))

    if matched.empty:
        print("No positive samples found.")
        continue

    print("Date range:",
          matched["time"].min().date(),
          "to",
          matched["time"].max().date())

    print("Latitude range:",
          matched["latitude"].min(),
          "to",
          matched["latitude"].max())

    print("Longitude range:",
          matched["longitude"].min(),
          "to",
          matched["longitude"].max())

print("\n===== S003 LABEL DETAILS =====")

s003 = df[
    (df["flood_event"] == 1)
    & (df["event_id"].astype(str) == "S003")
]

print(
    s003[
        ["time", "latitude", "longitude",
         "imerg_rainfall", "imd_rainfall",
         "soil_moisture"]
    ].sort_values(["time", "latitude", "longitude"])
    .to_string(index=False)
)

print("\nAudit complete.")
