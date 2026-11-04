import pandas as pd
import numpy as np
from pathlib import Path
import joblib

from xgboost import XGBClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    average_precision_score
)


# ============================================================
# PATHS
# ============================================================

TRAIN_FILE = "data/final/sikkim/train_balanced.csv"
TEST_FILE = "data/final/sikkim/test.csv"

MODEL_FILE = "data/final/sikkim/xgboost_flood_model.json"


# ============================================================
# FEATURES
# ============================================================

FEATURES = [
    "latitude",
    "longitude",
    "imerg_rainfall",
    "rainfall_1day",
    "rainfall_3day",
    "rainfall_7day",
    "imd_rainfall",
    "soil_moisture"
]

TARGET = "flood_event"


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 60)
print("LOADING DATA")
print("=" * 60)

train = pd.read_csv(
    TRAIN_FILE,
    low_memory=False
)

test = pd.read_csv(
    TEST_FILE,
    low_memory=False
)

print("Train shape:", train.shape)
print("Test shape:", test.shape)

# ============================================================
# PREPARE X / y
# ============================================================

X_train = train[FEATURES].copy()
y_train = train[TARGET].copy()

X_test = test[FEATURES].copy()
y_test = test[TARGET].copy()


# ============================================================
# HANDLE MISSING VALUES
# ============================================================

print("\nMissing values before imputation:")

print(
    X_train.isnull().sum()
)

imputer = SimpleImputer(
    strategy="median"
)

X_train = pd.DataFrame(
    imputer.fit_transform(X_train),
    columns=FEATURES
)

X_test = pd.DataFrame(
    imputer.transform(X_test),
    columns=FEATURES
)


print(
    "\nMissing values after imputation:",
    X_train.isnull().sum().sum()
)


# ============================================================
# CLASS WEIGHT
# ============================================================

positive = (y_train == 1).sum()
negative = (y_train == 0).sum()

scale_pos_weight = negative / positive

print("\nTraining class distribution:")
print(y_train.value_counts())

print(
    "\nscale_pos_weight:",
    scale_pos_weight
)


# ============================================================
# XGBOOST MODEL
# ============================================================

model = XGBClassifier(

    n_estimators=200,

    max_depth=4,

    learning_rate=0.05,

    subsample=0.8,

    colsample_bytree=0.8,

    objective="binary:logistic",

    eval_metric="logloss",

    scale_pos_weight=scale_pos_weight,

    random_state=42,

    n_jobs=-1
)


# ============================================================
# TRAIN
# ============================================================

print("\n" + "=" * 60)
print("TRAINING XGBOOST")
print("=" * 60)

model.fit(
    X_train,
    y_train
)

print("\nTraining complete!")


# ============================================================
# PREDICTIONS
# ============================================================

y_probability = model.predict_proba(
    X_test
)[:, 1]

y_prediction = (
    y_probability >= 0.5
).astype(int)


# ============================================================
# CLASSIFICATION REPORT
# ============================================================

print("\n" + "=" * 60)
print("CLASSIFICATION REPORT")
print("=" * 60)

print(
    classification_report(
        y_test,
        y_prediction,
        digits=4,
        zero_division=0
    )
)


# ============================================================
# CONFUSION MATRIX
# ============================================================

print("\n" + "=" * 60)
print("CONFUSION MATRIX")
print("=" * 60)

print(
    confusion_matrix(
        y_test,
        y_prediction
    )
)


# ============================================================
# ROC-AUC
# ============================================================

roc_auc = roc_auc_score(
    y_test,
    y_probability
)

print("\nROC-AUC:", round(roc_auc, 4))


# ============================================================
# PR-AUC
# ============================================================

pr_auc = average_precision_score(
    y_test,
    y_probability
)

print("PR-AUC:", round(pr_auc, 4))


# ============================================================
# FEATURE IMPORTANCE
# ============================================================

importance = pd.DataFrame({

    "feature": FEATURES,

    "importance":
        model.feature_importances_

})

importance = importance.sort_values(
    "importance",
    ascending=False
)


print("\n" + "=" * 60)
print("FEATURE IMPORTANCE")
print("=" * 60)

print(
    importance.to_string(
        index=False
    )
)


# ============================================================
# SHOW FLOOD PREDICTIONS
# ============================================================

results = test[
    [
        "time",
        "latitude",
        "longitude",
        "event_id"
    ]
].copy()

results["actual"] = y_test.values

results["flood_probability"] = y_probability

results["prediction"] = y_prediction

results = results.sort_values(
    "flood_probability",
    ascending=False
)


print("\n" + "=" * 60)
print("TOP 20 FLOOD PROBABILITIES")
print("=" * 60)

print(
    results.head(20).to_string(
        index=False
    )
)


# ============================================================
# SAVE MODEL
# ============================================================

# ============================================================
# SAVE MODEL AND PREPROCESSOR
# ============================================================

MODEL_PATH = Path(MODEL_FILE)
MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

model.save_model(str(MODEL_PATH))

IMPUTER_FILE = MODEL_PATH.parent / "xgboost_imputer.joblib"
joblib.dump(imputer, IMPUTER_FILE)

print("\nModel saved to:", MODEL_PATH)
print("Imputer saved to:", IMPUTER_FILE)
print("\nDONE.")
