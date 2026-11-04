
from pathlib import Path

import pandas as pd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

NRT_INPUT = (
    PROJECT_ROOT
    / "data"
    / "nrt"
    / "processed"
    / "sikkim_imerg_nrt_latest.csv"
)

HISTORICAL_INPUT = (
    PROJECT_ROOT
    / "data"
    / "final"
    / "sikkim"
    / "features_dataset.csv"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "nrt"
    / "processed"
    / "sikkim_rainfall_indicators.csv"
)


RAIN_COLUMNS = [
    "rainfall_1day",
    "rainfall_3day",
    "rainfall_7day",
]


def build_rainfall_indicators():
    """Generate rainfall indicators, not flood probabilities."""

    if not NRT_INPUT.exists():
        raise FileNotFoundError(
            f"NRT input not found: {NRT_INPUT}"
        )

    if not HISTORICAL_INPUT.exists():
        raise FileNotFoundError(
            f"Historical input not found: {HISTORICAL_INPUT}"
        )

    nrt = pd.read_csv(NRT_INPUT)
    historical = pd.read_csv(HISTORICAL_INPUT)

    if nrt.empty:
        raise ValueError("NRT dataset is empty.")

    required_nrt = [
        "time",
        "latitude",
        "longitude",
        *RAIN_COLUMNS,
    ]

    missing = [
        column for column in required_nrt
        if column not in nrt.columns
    ]

    if missing:
        raise ValueError(
            f"NRT dataset is missing columns: {missing}"
        )

    # Convert observations to usable numeric values.
    for column in RAIN_COLUMNS:
        nrt[column] = pd.to_numeric(
            nrt[column], errors="coerce"
        )
        historical[column] = pd.to_numeric(
            historical[column], errors="coerce"
        )

    # Ensure 1-day rainfall is complete and non-null
    if nrt["rainfall_1day"].isna().any():
        raise ValueError(
            "NRT 1-day rainfall contains missing or invalid values."
        )

    for col in RAIN_COLUMNS:
        valid_vals = nrt[col].dropna()
        if (valid_vals < 0).any():
            raise ValueError(
                f"Negative rainfall values were found in {col}."
            )

    # Historical reference thresholds.
    # These are statistical comparison levels, NOT
    # validated flood-warning thresholds.
    thresholds = {}

    for column in RAIN_COLUMNS:
        values = historical[column].dropna()

        if values.empty:
            raise ValueError(
                f"No historical values for {column}"
            )

        thresholds[column] = {
            "p75": float(values.quantile(0.75)),
            "p90": float(values.quantile(0.90)),
            "p95": float(values.quantile(0.95)),
        }

    # Compare each live observation against its historical
    # rainfall distribution.
    for column in RAIN_COLUMNS:
        nrt[f"{column}_historical_p75"] = (
            thresholds[column]["p75"]
        )
        nrt[f"{column}_historical_p90"] = (
            thresholds[column]["p90"]
        )
        nrt[f"{column}_historical_p95"] = (
            thresholds[column]["p95"]
        )

        if nrt[column].notna().any():
            band_series = pd.cut(
                nrt[column],
                bins=[
                    float("-inf"),
                    thresholds[column]["p75"],
                    thresholds[column]["p90"],
                    thresholds[column]["p95"],
                    float("inf"),
                ],
                labels=[
                    "At or below historical P75",
                    "Above P75 to P90",
                    "Above P90 to P95",
                    "Above historical P95",
                ],
                include_lowest=True,
            )
            nrt[f"{column}_percentile_band"] = band_series.astype(str).replace({"nan": "Incomplete window (< 7 days)"})
        else:
            nrt[f"{column}_percentile_band"] = "Incomplete window (< 7 days)"

    # A simple descriptive indicator, not a trained model.
    daily_p90 = thresholds["rainfall_1day"]["p90"]
    daily_p95 = thresholds["rainfall_1day"]["p95"]
    three_day_p90 = thresholds["rainfall_3day"]["p90"]
    three_day_p95 = thresholds["rainfall_3day"]["p95"]

    def describe_row(row):
        daily = row["rainfall_1day"]
        three_day = row["rainfall_3day"]

        if daily >= daily_p95 or three_day >= three_day_p95:
            return "Very high rainfall relative to history"

        if daily >= daily_p90 or three_day >= three_day_p90:
            return "Elevated rainfall relative to history"

        return "No P90 rainfall exceedance"

    nrt["rainfall_indicator"] = nrt.apply(
        describe_row, axis=1
    )

    nrt["indicator_type"] = (
        "Historical rainfall comparison; not flood probability"
    )

    nrt["imd_rainfall_available"] = False
    nrt["soil_moisture_available"] = False
    nrt["full_model_ready"] = False

    OUTPUT_PATH.parent.mkdir(
        parents=True, exist_ok=True
    )
    nrt.to_csv(OUTPUT_PATH, index=False)

    # Update pipeline_status.json
    status_file = PROJECT_ROOT / "data" / "nrt" / "pipeline_status.json"
    if status_file.exists():
        try:
            import datetime
            import json
            with open(status_file, "r", encoding="utf-8") as f:
                pstatus = json.load(f)
            counts = nrt["rainfall_indicator"].value_counts().to_dict()
            pstatus["last_indicator_run"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            pstatus["indicator_status"] = "SUCCESS"
            pstatus["indicators_summary"] = {
                "total_monitored_cells": len(nrt),
                "very_high_cells": int(counts.get("Very high rainfall relative to history", 0)),
                "elevated_cells": int(counts.get("Elevated rainfall relative to history", 0)),
                "no_exceedance_cells": int(counts.get("No P90 rainfall exceedance", 0)),
            }
            with open(status_file, "w", encoding="utf-8") as f:
                json.dump(pstatus, f, indent=2)
        except Exception as exc:
            print(f"Warning: Could not update pipeline status with indicator metadata: {exc}")

    print("NRT rainfall indicators generated successfully.")
    print(f"Grid cells: {len(nrt)}")
    print(f"Output: {OUTPUT_PATH}")
    print("\nIndicator counts:")
    print(nrt["rainfall_indicator"].value_counts().to_string())

    print("\nHistorical comparison thresholds:")
    for column, values in thresholds.items():
        print(f"{column}: {values}")


if __name__ == "__main__":
    build_rainfall_indicators()
