import pandas as pd

file_path = "data/raw/sikkim/historical/flood_events.csv"

df = pd.read_csv(file_path)

print("\n===== EVENT DATA =====")
print(df)

print("\n===== COLUMNS =====")
print(df.columns.tolist())

print("\n===== EVENT TYPES =====")
print(df["event_type"].value_counts())

print("\n===== DATE RANGE =====")
print("Start:", df["start_date"].min())
print("End:", df["end_date"].max())

print("\n===== MISSING VALUES =====")
print(df.isnull().sum())