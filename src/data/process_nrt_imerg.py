"""
NASA IMERG Near-Real-Time (NRT) Processing & Feature Extraction Module for FlashGuard-AI.

Extracts rainfall for the 64 Sikkim grid cells from downloaded NRT IMERG NetCDF granules,
calculates rolling antecedent rainfall (1-day, 3-day, 7-day) where valid timeseries are present,
and checks model feature readiness against the trained 8-feature XGBoost pipeline.

Strictly refuses to fabricate or impute missing operational IMD rainfall or SMAP soil moisture.
Preserves historical datasets and updates data/nrt/pipeline_status.json.
"""

from __future__ import annotations

import argparse
import datetime
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import xarray as xr

# ============================================================
# PATHS & CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
NRT_BASE_DIR = PROJECT_ROOT / "data" / "nrt"
NRT_RAW_DIR = NRT_BASE_DIR / "raw" / "imerg"
NRT_PROCESSED_DIR = NRT_BASE_DIR / "processed"
STATUS_FILE = NRT_BASE_DIR / "pipeline_status.json"

PROCESSED_CSV_TIMESERIES = NRT_PROCESSED_DIR / "sikkim_imerg_nrt_timeseries.csv"
PROCESSED_CSV_LATEST = NRT_PROCESSED_DIR / "sikkim_imerg_nrt_latest.csv"

# Target 64 Sikkim grid definition matching FlashGuard-AI's historical alignment
# Latitude: 27.25 to 27.95 (8 points)
# Longitude: 88.05 to 88.75 (8 points)
SIKKIM_LATS = [round(27.25 + i * 0.1, 2) for i in range(8)]
SIKKIM_LONS = [round(88.05 + i * 0.1, 2) for i in range(8)]

# Expected 8 model features in exact order
REQUIRED_MODEL_FEATURES = [
    "latitude",
    "longitude",
    "imerg_rainfall",
    "rainfall_1day",
    "rainfall_3day",
    "rainfall_7day",
    "imd_rainfall",
    "soil_moisture",
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("process_nrt_imerg")


# ============================================================
# EXTRACT SIKKIM GRID FROM ONE NC4 FILE
# ============================================================

def extract_sikkim_grid_from_file(nc_file: Path) -> pd.DataFrame:
    """
    Open one verified IMERG NetCDF granule, extract the 64 Sikkim grid cells,
    and return a DataFrame with columns: [time, latitude, longitude, imerg_rainfall].
    """
    if not nc_file.exists():
        raise FileNotFoundError(f"Granule file not found: {nc_file}")

    with xr.open_dataset(nc_file) as ds:
        if "precipitation" not in ds.variables:
            raise ValueError(f"No 'precipitation' variable in {nc_file.name}")

        time_val = pd.to_datetime(ds["time"].values[0]).strftime("%Y-%m-%d")

        # Select the target lat/lon slice or interpolate nearest to Sikkim grid points
        precip_var = ds["precipitation"]

        # IMERG uses 'lat' and 'lon' coordinates
        records = []
        for lat in SIKKIM_LATS:
            for lon in SIKKIM_LONS:
                try:
                    val = float(
                        precip_var.sel(
                            lat=lat,
                            lon=lon,
                            method="nearest"
                        ).values.squeeze()
                    )
                except Exception as exc:
                    logger.warning(
                        "Error selecting lat=%.2f, lon=%.2f in %s: %s",
                        lat, lon, nc_file.name, exc
                    )
                    val = np.nan

                records.append({
                    "time": time_val,
                    "latitude": lat,
                    "longitude": lon,
                    "imerg_rainfall": round(val, 3) if not np.isnan(val) else np.nan,
                })

    df = pd.DataFrame(records)
    return df


# ============================================================
# PROCESS ALL NRT GRANULES & CALCULATE ROLLING ANTECEDENT
# ============================================================

def process_all_nrt_granules() -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Process all available NRT granules in data/nrt/raw/imerg/,
    compute rolling rainfall where timeseries exists,
    and return (timeseries_df, latest_day_df, summary_dict).
    """
    NRT_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    granule_files = sorted(NRT_RAW_DIR.glob("*.nc4"))

    if not granule_files:
        logger.warning("No .nc4 granules found in %s", NRT_RAW_DIR)
        return pd.DataFrame(), pd.DataFrame(), {
            "status": "NO_RAW_DATA",
            "message": f"No IMERG granules found in {NRT_RAW_DIR}",
        }

    logger.info("Found %d NRT granule(s) to process.", len(granule_files))

    daily_dfs: List[pd.DataFrame] = []
    processed_files: List[str] = []

    for gfile in granule_files:
        try:
            df_day = extract_sikkim_grid_from_file(gfile)
            daily_dfs.append(df_day)
            processed_files.append(gfile.name)
            logger.info("Extracted %d grid cells from %s", len(df_day), gfile.name)
        except Exception as exc:
            logger.error("Failed processing %s: %s", gfile.name, exc)

    if not daily_dfs:
        return pd.DataFrame(), pd.DataFrame(), {
            "status": "EXTRACTION_FAILED",
            "message": "Failed extracting data from available granules.",
        }

    combined = pd.concat(daily_dfs, ignore_index=True)
    combined["time"] = pd.to_datetime(combined["time"])

    # Remove duplicates if any
    combined = combined.drop_duplicates(subset=["time", "latitude", "longitude"])
    combined = combined.sort_values(["latitude", "longitude", "time"]).reset_index(drop=True)

    # Compute rolling antecedent rainfall with complete time windows
    combined["rainfall_1day"] = combined["imerg_rainfall"]

    combined["rainfall_3day"] = (
        combined.groupby(["latitude", "longitude"])["imerg_rainfall"]
        .transform(lambda x: x.rolling(window=3, min_periods=3).sum())
    )

    combined["rainfall_7day"] = (
        combined.groupby(["latitude", "longitude"])["imerg_rainfall"]
        .transform(lambda x: x.rolling(window=7, min_periods=7).sum())
    )

    # Save complete NRT timeseries
    combined.to_csv(PROCESSED_CSV_TIMESERIES, index=False)
    logger.info("Saved NRT timeseries (%d rows) to %s", len(combined), PROCESSED_CSV_TIMESERIES)

    # Extract latest observation date
    latest_date = combined["time"].max()
    latest_df = combined[combined["time"] == latest_date].copy().reset_index(drop=True)
    latest_df.to_csv(PROCESSED_CSV_LATEST, index=False)
    logger.info(
        "Saved latest observation (%s, %d cells) to %s",
        latest_date.strftime("%Y-%m-%d"),
        len(latest_df),
        PROCESSED_CSV_LATEST,
    )

    summary = {
        "status": "SUCCESS",
        "processed_granules": processed_files,
        "total_records": len(combined),
        "latest_observation_date": latest_date.strftime("%Y-%m-%d"),
        "latest_records_count": len(latest_df),
        "mean_sikkim_rainfall": float(latest_df["imerg_rainfall"].mean()),
        "max_sikkim_rainfall": float(latest_df["imerg_rainfall"].max()),
        "min_sikkim_rainfall": float(latest_df["imerg_rainfall"].min()),
    }

    # Update pipeline status JSON
    _record_processing_status(summary, latest_df)

    return combined, latest_df, summary


# ============================================================
# FEATURE COMPLETENESS & MODEL GATING
# ============================================================

def evaluate_model_readiness(latest_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Check if the 8 required model features exist and are genuine.
    Strictly forbids synthesizing or hallucinating missing IMD or SMAP inputs.
    """
    if latest_df.empty:
        return {
            "can_run_full_model": False,
            "reason": "No live observation records available.",
            "available_features": [],
            "missing_features": REQUIRED_MODEL_FEATURES,
        }

    available_features = [
        f for f in REQUIRED_MODEL_FEATURES
        if f in latest_df.columns and not latest_df[f].isna().all()
    ]
    missing_features = [
        f for f in REQUIRED_MODEL_FEATURES
        if f not in latest_df.columns or latest_df[f].isna().all()
    ]

    # IMD rainfall and SMAP soil moisture are not available in real-time
    has_imd = "imd_rainfall" in latest_df.columns and not latest_df["imd_rainfall"].isna().all()
    has_smap = "soil_moisture" in latest_df.columns and not latest_df["soil_moisture"].isna().all()
    has_7day = "rainfall_7day" in latest_df.columns and not latest_df["rainfall_7day"].isna().all()

    can_run = (len(missing_features) == 0) and has_imd and has_smap and has_7day

    return {
        "can_run_full_model": can_run,
        "available_features_count": len(available_features),
        "required_features_count": len(REQUIRED_MODEL_FEATURES),
        "available_features": available_features,
        "missing_features": missing_features,
        "reason": (
            "All 8 required features present."
            if can_run
            else "Operational IMD gridded rainfall and NASA SMAP soil moisture are not configured for real-time observation dates. FlashGuard-AI strictly avoids fabricating missing features."
        ),
    }


def _record_processing_status(summary: Dict[str, Any], latest_df: Optional[pd.DataFrame] = None) -> None:
    """Update pipeline_status.json with processing results."""
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    existing: Dict[str, Any] = {}

    if STATUS_FILE.exists():
        try:
            with open(STATUS_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = {}

    existing["last_processing_run"] = now_utc
    existing["processing_status"] = summary.get("status")
    existing["latest_observation_date"] = summary.get("latest_observation_date")
    existing["latest_nrt_stats"] = {
        "mean_imerg_rainfall_mm": summary.get("mean_sikkim_rainfall"),
        "max_imerg_rainfall_mm": summary.get("max_sikkim_rainfall"),
        "min_imerg_rainfall_mm": summary.get("min_sikkim_rainfall"),
        "cells_count": summary.get("latest_records_count"),
    }

    # Evaluate feature readiness
    target_df = latest_df if latest_df is not None else pd.DataFrame()
    readiness = evaluate_model_readiness(target_df)
    existing["model_readiness"] = readiness

    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)


# ============================================================
# CLI ENTRYPOINT
# ============================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Process downloaded NASA IMERG NRT granules into Sikkim grid features."
    )
    args = parser.parse_args()

    timeseries_df, latest_df, summary = process_all_nrt_granules()

    print("\n" + "=" * 60)
    print("FLASHGUARD-AI NRT PROCESSING SUMMARY")
    print("=" * 60)
    print(f"Status                  : {summary.get('status')}")
    print(f"Latest Observation Date : {summary.get('latest_observation_date')}")
    print(f"Total Sikkim Records    : {summary.get('total_records', 0)}")
    print(f"Latest Day Grid Cells   : {summary.get('latest_records_count', 0)}")
    if "mean_sikkim_rainfall" in summary:
        print(f"Sikkim Mean Rainfall    : {summary['mean_sikkim_rainfall']:.2f} mm/day")
        print(f"Sikkim Max Rainfall     : {summary['max_sikkim_rainfall']:.2f} mm/day")

    readiness = evaluate_model_readiness(latest_df)
    print("\n" + "-" * 60)
    print("MODEL FEATURE READINESS")
    print("-" * 60)
    print(f"Can Run Full Model : {readiness['can_run_full_model']}")
    print(f"Available Features : {', '.join(readiness['available_features'])}")
    print(f"Missing Features   : {', '.join(readiness['missing_features'])}")
    print(f"Gating Policy      : {readiness['reason']}")
    print("=" * 60 + "\n")

    return 0 if summary.get("status") == "SUCCESS" else 1


if __name__ == "__main__":
    sys.exit(main())
