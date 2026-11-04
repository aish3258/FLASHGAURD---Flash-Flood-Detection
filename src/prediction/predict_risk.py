
from pathlib import Path

import joblib
import pandas as pd
from xgboost import XGBClassifier


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODEL_PATH = (
    PROJECT_ROOT
    / "data"
    / "final"
    / "sikkim"
    / "xgboost_flood_model.json"
)

IMPUTER_PATH = (
    PROJECT_ROOT
    / "data"
    / "final"
    / "sikkim"
    / "xgboost_imputer.joblib"
)


# ============================================================
# FEATURES — MUST MATCH TRAINING ORDER
# ============================================================

FEATURES = [
    "latitude",
    "longitude",
    "imerg_rainfall",
    "rainfall_1day",
    "rainfall_3day",
    "rainfall_7day",
    "imd_rainfall",
    "soil_moisture",
]


# ============================================================
# LOAD TRAINED MODEL AND IMPUTER
# ============================================================

def load_pipeline():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model not found: {MODEL_PATH}\n"
            "Run src/models/train_xgboost.py first."
        )

    if not IMPUTER_PATH.exists():
        raise FileNotFoundError(
            f"Imputer not found: {IMPUTER_PATH}\n"
            "Update and rerun the training script first."
        )

    model = XGBClassifier()
    model.load_model(str(MODEL_PATH))

    imputer = joblib.load(IMPUTER_PATH)

    return model, imputer


# ============================================================
# PREDICT RISK FOR GRID CELLS
# ============================================================

def predict_risk(data: pd.DataFrame) -> pd.DataFrame:
    """
    Accepts a DataFrame containing the eight model features.
    Returns the original rows with a flood probability estimate.
    """

    missing_features = [
        feature for feature in FEATURES
        if feature not in data.columns
    ]

    if missing_features:
        raise ValueError(
            f"Missing required features: {missing_features}"
        )

    if data.empty:
        raise ValueError("Input data is empty.")

    # Keep the same feature order as during training.
    X = data[FEATURES].copy()

    # Convert invalid strings to missing values.
    for column in FEATURES:
        X[column] = pd.to_numeric(
            X[column], errors="coerce"
        )

    # Reject rows with no usable value for any feature.
    invalid_rows = X.isna().all(axis=1)

    if invalid_rows.any():
        raise ValueError(
            "At least one row contains no usable feature values."
        )

    # Apply the fitted training-time imputer.
    model, imputer = load_pipeline()

    X_imputed = pd.DataFrame(
        imputer.transform(X),
        columns=FEATURES,
        index=X.index,
    )

    # Estimate positive-class probability.
    probabilities = model.predict_proba(X_imputed)[:, 1]

    results = data.copy()
    results["flood_probability"] = probabilities

    # These are illustrative display bands, NOT calibrated
    # warning thresholds or validated operational alert levels.
    results["risk_band"] = pd.cut(
        results["flood_probability"],
        bins=[-0.001, 0.30, 0.60, 1.0],
        labels=["Low", "Moderate", "High"],
        include_lowest=True,
    ).astype(str)

    return results


# ============================================================
# QUICK TEST
# ============================================================

if __name__ == "__main__":
    dataset_path = (
        PROJECT_ROOT
        / "data"
        / "final"
        / "sikkim"
        / "test.csv"
    )

    test_data = pd.read_csv(dataset_path)

    results = predict_risk(test_data)

    columns_to_show = [
        "time",
        "latitude",
        "longitude",
        "flood_probability",
        "risk_band",
    ]

    print("\nTop 10 estimated-risk grid cells:")
    print(
        results.sort_values(
            "flood_probability",
            ascending=False,
        )[columns_to_show].head(10).to_string(index=False)
    )

    output_path = (
        PROJECT_ROOT
        / "data"
        / "final"
        / "sikkim"
        / "test_predictions.csv"
    )

    results.to_csv(output_path, index=False)

    print(f"\nPredictions saved to: {output_path}")
