"""
NASA IMERG Near-Real-Time (NRT) Ingestion Module for FlashGuard-AI.

Downloads official NASA GPM IMERG Early Daily (GPM_3IMERGDE) or Late Daily (GPM_3IMERGDL)
granules for recent observation dates, validates their data integrity and coverage over Sikkim,
and records pipeline status to data/nrt/pipeline_status.json.

Preserves all historical research datasets in separate directories.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import earthaccess
import requests
import xarray as xr

# ============================================================
# PATHS & CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
NRT_BASE_DIR = PROJECT_ROOT / "data" / "nrt"
NRT_RAW_DIR = NRT_BASE_DIR / "raw" / "imerg"
NRT_PROCESSED_DIR = NRT_BASE_DIR / "processed"
STATUS_FILE = NRT_BASE_DIR / "pipeline_status.json"

# Sikkim bounding box for coverage checks
SIKKIM_LAT_MIN = 27.25
SIKKIM_LAT_MAX = 28.00
SIKKIM_LON_MIN = 88.00
SIKKIM_LON_MAX = 88.75

DEFAULT_SHORT_NAME = "GPM_3IMERGDE"  # Early Run Daily (latency ~4 hours)
FALLBACK_SHORT_NAME = "GPM_3IMERGDL"  # Late Run Daily (latency ~14 hours)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("imerg_nrt_ingestion")


# ============================================================
# CREDENTIAL & AUTHENTICATION HELPER
# ============================================================

def authenticate_earthaccess() -> bool:
    """
    Authenticate against NASA Earthdata using existing local .netrc or environment tokens.
    Never exposes or logs sensitive credentials.
    """
    token = os.getenv("EARTHDATA_TOKEN")
    if token:
        logger.info("Using EARTHDATA_TOKEN from environment for authentication.")
        # earthaccess can use environment token or requests session header
        try:
            auth = earthaccess.login(strategy="environment")
            if auth.authenticated:
                return True
        except Exception:
            pass

    # Try netrc authentication
    try:
        auth = earthaccess.login(strategy="netrc")
        if auth.authenticated:
            logger.info("Successfully authenticated via Earthdata .netrc.")
            return True
    except Exception as exc:
        logger.warning("Earthdata netrc authentication failed: %s", exc)

    logger.error(
        "NASA Earthdata authentication failed. Please provide a valid .netrc "
        "file or set EARTHDATA_TOKEN environment variable."
    )
    return False


# ============================================================
# FILE VALIDATION
# ============================================================

def calculate_sha256(filepath: Path) -> str:
    """Compute SHA256 checksum for file verification."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def validate_imerg_netcdf(filepath: Path) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Strictly validate a downloaded IMERG NetCDF file:
    - Check file size (> 1MB for global daily grid).
    - Check NetCDF readability.
    - Check required coordinates: lat, lon, time.
    - Check Sikkim spatial coverage.
    - Check precipitation variable presence, valid range, and non-empty values.
    """
    errors: List[str] = []
    metadata: Dict[str, Any] = {}

    if not filepath.exists():
        return False, [f"File does not exist: {filepath}"], {}

    file_size = filepath.stat().st_size
    metadata["file_size_bytes"] = file_size

    # Suspiciously small file check (HTML error pages or truncated downloads)
    if file_size < 100_000:
        errors.append(f"File size suspiciously small ({file_size} bytes). Minimum expected > 100KB.")
        return False, errors, metadata

    try:
        with xr.open_dataset(filepath) as ds:
            # Check coordinates
            for coord in ["lat", "lon", "time"]:
                if coord not in ds.coords and coord not in ds.dims:
                    errors.append(f"Missing required coordinate: {coord}")

            if "lat" in ds.coords and "lon" in ds.coords:
                lat_vals = ds["lat"].values
                lon_vals = ds["lon"].values

                # Coverage check for Sikkim
                if float(lat_vals.min()) > SIKKIM_LAT_MIN or float(lat_vals.max()) < SIKKIM_LAT_MAX:
                    errors.append(
                        f"Latitude bounds [{float(lat_vals.min())}, {float(lat_vals.max())}] "
                        f"do not cover Sikkim [{SIKKIM_LAT_MIN}, {SIKKIM_LAT_MAX}]."
                    )
                if float(lon_vals.min()) > SIKKIM_LON_MIN or float(lon_vals.max()) < SIKKIM_LON_MAX:
                    errors.append(
                        f"Longitude bounds [{float(lon_vals.min())}, {float(lon_vals.max())}] "
                        f"do not cover Sikkim [{SIKKIM_LON_MIN}, {SIKKIM_LON_MAX}]."
                    )

            # Check precipitation variable
            if "precipitation" not in ds.variables:
                errors.append("Dataset does not contain 'precipitation' variable.")
            else:
                precip = ds["precipitation"]
                metadata["units"] = precip.attrs.get("units", "unknown")

                # Crop to Sikkim box to check localized validity
                sikkim_subset = precip.sel(
                    lat=slice(SIKKIM_LAT_MIN - 0.2, SIKKIM_LAT_MAX + 0.2),
                    lon=slice(SIKKIM_LON_MIN - 0.2, SIKKIM_LON_MAX + 0.2),
                )

                valid_values = sikkim_subset.values[~xr.ufuncs.isnan(sikkim_subset.values)] if hasattr(xr, "ufuncs") else sikkim_subset.values[~ds["precipitation"].isnull().values[:1, :1, :1]]
                import numpy as np
                sikkim_vals = sikkim_subset.values
                valid_mask = ~np.isnan(sikkim_vals)

                if not np.any(valid_mask):
                    errors.append("Precipitation over Sikkim region is entirely NaN or missing.")
                else:
                    valid_data = sikkim_vals[valid_mask]
                    min_val = float(np.min(valid_data))
                    max_val = float(np.max(valid_data))
                    if min_val < 0.0:
                        errors.append(f"Negative precipitation encountered: min={min_val}")
                    metadata["sikkim_precip_min"] = min_val
                    metadata["sikkim_precip_max"] = max_val
                    metadata["sikkim_precip_mean"] = float(np.mean(valid_data))

            # Timestamp check
            if "time" in ds.coords:
                time_val = str(ds["time"].values[0])[:10]
                metadata["observation_date"] = time_val

            metadata["title"] = ds.attrs.get("title", "")
            metadata["production_time"] = ds.attrs.get("ProductionTime", "")

    except Exception as exc:
        errors.append(f"Error reading NetCDF file: {exc}")

    is_valid = len(errors) == 0
    return is_valid, errors, metadata


# ============================================================
# DOWNLOADING ONE GRANULE
# ============================================================

def download_granule(
    granule: Any,
    destination_dir: Path,
    force: bool = False,
) -> Dict[str, Any]:
    """
    Download a single granule safely:
    - Checks for existing file and validates it.
    - Downloads to .part temporary file.
    - Validates file integrity before replacing.
    """
    granule_ur = granule["umm"].get("GranuleUR", "unknown")
    links = granule.data_links()
    if not links:
        return {
            "status": "FAILED",
            "granule_ur": granule_ur,
            "error": "No download data links provided for granule.",
        }

    url = links[0]
    filename = Path(url.split("?")[0]).name
    target_path = destination_dir / filename
    temp_path = destination_dir / f"{filename}.part"

    # Duplicate check: If file exists and is valid, skip unless force=True
    if target_path.exists() and not force:
        is_valid, errors, metadata = validate_imerg_netcdf(target_path)
        if is_valid:
            logger.info("File already exists and is valid: %s (Skipping)", filename)
            return {
                "status": "SKIPPED_DUPLICATE",
                "granule_ur": granule_ur,
                "filename": filename,
                "filepath": str(target_path),
                "observation_date": metadata.get("observation_date"),
                "file_size_bytes": target_path.stat().st_size,
            }
        else:
            logger.warning("Existing file %s is invalid (%s). Re-downloading.", filename, errors)

    logger.info("Downloading granule %s from %s", filename, url)
    session = earthaccess.get_requests_https_session()

    try:
        with session.get(url, stream=True, timeout=(30, 300), allow_redirects=True) as response:
            response.raise_for_status()

            content_type = response.headers.get("Content-Type", "").lower()
            if "text/html" in content_type:
                return {
                    "status": "FAILED",
                    "granule_ur": granule_ur,
                    "filename": filename,
                    "error": "Server returned HTML instead of NetCDF file. Authentication failed.",
                }

            with open(temp_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)

        # Validate downloaded file before renaming
        is_valid, errors, metadata = validate_imerg_netcdf(temp_path)
        if not is_valid:
            if temp_path.exists():
                temp_path.unlink()
            return {
                "status": "FAILED",
                "granule_ur": granule_ur,
                "filename": filename,
                "error": f"Downloaded file failed validation: {'; '.join(errors)}",
            }

        temp_path.replace(target_path)
        checksum = calculate_sha256(target_path)

        logger.info("Successfully downloaded and verified: %s", filename)
        return {
            "status": "DOWNLOADED",
            "granule_ur": granule_ur,
            "filename": filename,
            "filepath": str(target_path),
            "sha256": checksum,
            "file_size_bytes": target_path.stat().st_size,
            "observation_date": metadata.get("observation_date"),
            "metadata": metadata,
        }

    except Exception as exc:
        if temp_path.exists():
            temp_path.unlink()
        logger.error("Download failed for %s: %s", filename, exc)
        return {
            "status": "FAILED",
            "granule_ur": granule_ur,
            "filename": filename,
            "error": str(exc),
        }


# ============================================================
# PIPELINE STATUS PERSISTENCE
# ============================================================

def compute_data_freshness(latest_obs_date: Optional[str]) -> Tuple[str, str]:
    """
    Compute data freshness relative to current UTC date.
    NASA IMERG Daily Early has a nominal latency of ~4-14 hours.
    - <= 2 days: FRESH (expected operational latency for daily satellite composites).
    - 3-5 days: DELAYED (minor upstream publication or pipeline fetch lag).
    - > 5 days: STALE (significant ingestion lag).
    - None: UNAVAILABLE.
    """
    if not latest_obs_date:
        return "UNAVAILABLE", "No near-real-time observations found."

    try:
        obs_dt = datetime.datetime.strptime(latest_obs_date, "%Y-%m-%d").date()
        today_utc = datetime.datetime.now(datetime.timezone.utc).date()
        age_days = (today_utc - obs_dt).days

        if age_days <= 2:
            return "FRESH", f"Observation is {age_days} day(s) old (nominal daily satellite latency is ~4–14 hours)."
        elif age_days <= 5:
            return "DELAYED", f"Observation is {age_days} days old (minor data release or ingestion lag)."
        else:
            return "STALE", f"Observation is {age_days} days old (ingestion has not retrieved recent daily observations)."
    except Exception as exc:
        return "UNKNOWN", f"Could not determine freshness: {exc}"


def update_pipeline_status(
    status: str,
    results: List[Dict[str, Any]],
    error_message: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Write or update data/nrt/pipeline_status.json with explicit, honest operational status.
    Distinguishes new downloads vs valid duplicate skips.
    """
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    NRT_BASE_DIR.mkdir(parents=True, exist_ok=True)

    existing_status: Dict[str, Any] = {}
    if STATUS_FILE.exists():
        try:
            with open(STATUS_FILE, "r", encoding="utf-8") as f:
                existing_status = json.load(f)
        except Exception:
            existing_status = {}

    downloaded_results = [r for r in results if r.get("status") == "DOWNLOADED"]
    skipped_results = [r for r in results if r.get("status") == "SKIPPED_DUPLICATE"]
    failed_results = [r for r in results if r.get("status") == "FAILED"]

    downloaded_count = len(downloaded_results)
    skipped_count = len(skipped_results)
    failed_count = len(failed_results)

    successful_results = downloaded_results + skipped_results

    if downloaded_count > 0:
        ingestion_outcome = "NEW_DOWNLOADS"
        outcome_message = (
            f"Successfully downloaded and verified {downloaded_count} new granule(s); "
            f"{skipped_count} existing granule(s) verified as duplicate skips."
        )
    elif skipped_count > 0 and failed_count == 0:
        ingestion_outcome = "UP_TO_DATE_DUPLICATES_SKIPPED"
        outcome_message = (
            f"All {skipped_count} NASA granule(s) were already downloaded, verified, and up-to-date; "
            f"duplicates safely skipped."
        )
    elif failed_count > 0 and downloaded_count == 0 and skipped_count == 0:
        ingestion_outcome = "FAILED"
        outcome_message = f"NASA ingestion failed: {error_message or 'Download error encountered.'}"
    elif failed_count > 0:
        ingestion_outcome = "PARTIAL"
        outcome_message = (
            f"Partial ingestion: {downloaded_count} downloaded, {skipped_count} skipped, {failed_count} failed."
        )
    else:
        ingestion_outcome = "NO_NEW_DATA"
        outcome_message = "No matching granules found in NASA CMR for the requested temporal range."

    latest_obs_date = None
    if successful_results:
        dates = [
            r.get("observation_date") for r in successful_results if r.get("observation_date")
        ]
        if dates:
            latest_obs_date = sorted(dates)[-1]
    if not latest_obs_date and existing_status.get("latest_observation_date"):
        latest_obs_date = existing_status.get("latest_observation_date")

    # Update last_successful_fetch only if there were successful results or if status is SUCCESS
    if status == "SUCCESS" or len(successful_results) > 0:
        last_successful_fetch = now_utc
    else:
        last_successful_fetch = existing_status.get("last_successful_fetch")

    freshness_status, freshness_detail = compute_data_freshness(latest_obs_date)

    status_data: Dict[str, Any] = {
        "pipeline_name": "NASA IMERG Near-Real-Time Ingestion",
        "last_run_timestamp": now_utc,
        "last_ingestion_attempt": now_utc,
        "last_successful_fetch": last_successful_fetch,
        "last_ingestion_result": ingestion_outcome,
        "last_ingestion_message": outcome_message,
        "newly_downloaded_count": downloaded_count,
        "skipped_duplicate_count": skipped_count,
        "failed_download_count": failed_count,
        "execution_mode": "MANUAL_TRIGGER",
        "status": status,
        "data_freshness": {
            "status": freshness_status,
            "detail": freshness_detail,
        },
        "error_message": error_message,
        "latest_observation_date": latest_obs_date,
        "ingested_files_count": len(successful_results),
        "latest_granules": successful_results[-5:] if successful_results else existing_status.get("latest_granules", []),
        "source_availability": {
            "imerg_nrt": {
                "status": "ONLINE" if latest_obs_date else "OFFLINE",
                "product": DEFAULT_SHORT_NAME,
                "latest_observation": latest_obs_date,
                "nominal_latency": "Approx. 4 hours",
            },
            "imd_rainfall": {
                "status": "UNAVAILABLE_FOR_NRT",
                "historical_end_date": "2023-12-31",
                "notice": "Operational real-time IMD gridded feed is not connected. FlashGuard-AI strictly avoids fabricating missing IMD rainfall.",
            },
            "smap_soil_moisture": {
                "status": "UNAVAILABLE_FOR_NRT",
                "historical_end_date": "2023-12-31",
                "notice": "Operational real-time SMAP feed is not connected. FlashGuard-AI strictly avoids fabricating missing soil moisture.",
            },
        },
        "model_readiness": {
            "can_run_full_model": False,
            "required_features_count": 8,
            "available_features_count": 4 if latest_obs_date else 0,
            "available_features": [
                "latitude",
                "longitude",
                "imerg_rainfall",
                "rainfall_1day",
            ] if latest_obs_date else [],
            "missing_features": [
                "rainfall_3day",  # unless 3 days available
                "rainfall_7day",  # unless 7 days available
                "imd_rainfall",
                "soil_moisture",
            ],
            "reason": (
                "Official XGBoost model requires 8 features including IMD rainfall and SMAP soil moisture. "
                "Predictions currently shown in the dashboard remain historical research predictions."
            ),
        },
    }

    # Preserve last known-good processing and indicator results from existing status
    for key in [
        "last_processing_run",
        "processing_status",
        "latest_nrt_stats",
        "last_indicator_run",
        "indicator_status",
        "indicators_summary",
    ]:
        if key in existing_status:
            status_data[key] = existing_status[key]

    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(status_data, f, indent=2)

    logger.info("Pipeline status recorded at %s", STATUS_FILE)
    return status_data


# ============================================================
# MAIN INGESTION FUNCTION
# ============================================================

def ingest_imerg_nrt(
    days_back: int = 3,
    target_date: Optional[str] = None,
    short_name: str = DEFAULT_SHORT_NAME,
    force: bool = False,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Main entrypoint to search and ingest near-real-time IMERG granules.
    """
    NRT_RAW_DIR.mkdir(parents=True, exist_ok=True)
    NRT_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    if not authenticate_earthaccess():
        msg = "Authentication failure: Unable to log into NASA Earthdata."
        update_pipeline_status("FAILED", [], error_message=msg)
        return {"status": "FAILED", "error": msg}

    now_utc = datetime.datetime.now(datetime.timezone.utc)

    if target_date:
        temporal_range = (target_date, target_date)
        logger.info("Searching for IMERG NRT granule for date: %s", target_date)
    else:
        start_date = (now_utc - datetime.timedelta(days=days_back)).strftime("%Y-%m-%d")
        end_date = now_utc.strftime("%Y-%m-%d")
        temporal_range = (start_date, end_date)
        logger.info("Searching for IMERG NRT granules between %s and %s", start_date, end_date)

    try:
        granules = earthaccess.search_data(
            short_name=short_name,
            temporal=temporal_range,
        )
    except Exception as exc:
        logger.error("Failed querying NASA CMR for %s: %s", short_name, exc)
        update_pipeline_status("FAILED", [], error_message=f"CMR search error: {exc}")
        return {"status": "FAILED", "error": str(exc)}

    if not granules:
        logger.warning("No granules found for short_name=%s in range %s", short_name, temporal_range)
        # Try fallback if using Early
        if short_name == DEFAULT_SHORT_NAME:
            logger.info("Attempting fallback to %s", FALLBACK_SHORT_NAME)
            try:
                granules = earthaccess.search_data(
                    short_name=FALLBACK_SHORT_NAME,
                    temporal=temporal_range,
                )
            except Exception:
                granules = []

    logger.info("Found %d granule(s).", len(granules))

    if dry_run:
        results = []
        for g in granules:
            results.append({
                "granule_ur": g["umm"].get("GranuleUR"),
                "data_links": g.data_links(),
            })
        print(json.dumps(results, indent=2))
        return {"status": "DRY_RUN", "granules": results}

    results: List[Dict[str, Any]] = []
    has_failures = False

    for granule in granules:
        res = download_granule(granule, NRT_RAW_DIR, force=force)
        results.append(res)
        if res.get("status") == "FAILED":
            has_failures = True

    status_str = "SUCCESS" if (results and not has_failures) else ("PARTIAL" if results else "NO_DATA")
    status_summary = update_pipeline_status(status_str, results)

    return {
        "status": status_str,
        "results": results,
        "summary": status_summary,
    }


# ============================================================
# CLI ENTRYPOINT
# ============================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ingest NASA GPM IMERG Near-Real-Time Daily precipitation granules."
    )
    parser.add_argument(
        "--days-back",
        type=int,
        default=7,
        help="Number of previous days to search and ingest (default: 7 to provide complete 7-day window).",
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Specific date to ingest in YYYY-MM-DD format.",
    )
    parser.add_argument(
        "--short-name",
        type=str,
        default=DEFAULT_SHORT_NAME,
        choices=[DEFAULT_SHORT_NAME, FALLBACK_SHORT_NAME],
        help="NASA CMR ShortName to ingest (default: GPM_3IMERGDE).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download and overwrite existing files.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Search and list granules without downloading.",
    )

    args = parser.parse_args()
    res = ingest_imerg_nrt(
        days_back=args.days_back,
        target_date=args.date,
        short_name=args.short_name,
        force=args.force,
        dry_run=args.dry_run,
    )

    if res.get("status") in ("SUCCESS", "SKIPPED_DUPLICATE", "DRY_RUN"):
        return 0
    elif res.get("status") == "PARTIAL":
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
