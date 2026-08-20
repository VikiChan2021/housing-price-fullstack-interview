"""Train, evaluate, version, and serialize the deterministic Ridge model artifact."""

import argparse
import csv
import hashlib
import json
import platform
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import sklearn
from sklearn.base import RegressorMixin
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.constants import (
    ALPHA_GRID,
    EVALUATION_IMPLEMENTATION_VERSION,
    FEATURE_NAMES,
    LIMITATIONS,
    N_SPLITS,
    RANDOM_SEED,
)
from app.data import TrainingData, load_prediction_data, load_training_data


@dataclass(frozen=True)
class FoldMetrics:
    """Metrics calculated from one untouched outer cross-validation fold."""

    r2: float
    mae: float
    rmse: float


def _ridge(alpha: float) -> Pipeline:
    # Keeping scaling inside the Pipeline prevents training/inference preprocessing drift.
    return Pipeline([("scaler", StandardScaler()), ("ridge", Ridge(alpha=alpha))])


def _select_alpha(features: np.ndarray, target: np.ndarray) -> float:
    """Select alpha using only the supplied training partition."""

    inner = KFold(n_splits=N_SPLITS, shuffle=True, random_state=RANDOM_SEED)
    scores: list[tuple[float, float]] = []
    for alpha in ALPHA_GRID:
        rmses = []
        for train_index, validation_index in inner.split(features):
            model = _ridge(alpha)
            model.fit(features[train_index], target[train_index])
            predictions = model.predict(features[validation_index])
            rmses.append(root_mean_squared_error(target[validation_index], predictions))
        scores.append((float(np.mean(rmses)), alpha))
    best_rmse = min(score for score, _ in scores)
    # np.isclose avoids unstable tie decisions caused by floating-point representation noise.
    return min(alpha for score, alpha in scores if np.isclose(score, best_rmse, rtol=1e-12))


def _metrics(target: np.ndarray, predictions: np.ndarray) -> FoldMetrics:
    return FoldMetrics(
        r2=float(r2_score(target, predictions)),
        mae=float(mean_absolute_error(target, predictions)),
        rmse=float(root_mean_squared_error(target, predictions)),
    )


def _summarize(folds: list[FoldMetrics]) -> dict[str, float | str]:
    """Aggregate fold metrics using population standard deviation as documented metadata."""

    result: dict[str, float | str] = {"evaluation_protocol": "nested_5_fold_cross_validation"}
    for name in ("r2", "mae", "rmse"):
        values = np.asarray([getattr(fold, name) for fold in folds])
        result[f"{name}_mean"] = float(values.mean())
        result[f"{name}_std"] = float(values.std(ddof=0))
    return result


def _evaluate_model(data: TrainingData) -> tuple[dict[str, Any], list[float]]:
    """Run nested CV so hyperparameter selection never sees an outer test fold."""

    outer = KFold(n_splits=N_SPLITS, shuffle=True, random_state=RANDOM_SEED)
    ridge_folds: list[FoldMetrics] = []
    baseline_folds: list[FoldMetrics] = []
    selected_alphas: list[float] = []
    for train_index, test_index in outer.split(data.features):
        train_features, test_features = data.features[train_index], data.features[test_index]
        train_target, test_target = data.target[train_index], data.target[test_index]
        # Alpha selection is repeated inside each outer fold to avoid optimistic evaluation leakage.
        alpha = _select_alpha(train_features, train_target)
        selected_alphas.append(alpha)

        ridge = _ridge(alpha)
        ridge.fit(train_features, train_target)
        ridge_folds.append(_metrics(test_target, ridge.predict(test_features)))

        # Ordinary linear regression is retained as a transparent comparison baseline.
        baseline: RegressorMixin = LinearRegression()
        baseline.fit(train_features, train_target)
        baseline_folds.append(_metrics(test_target, baseline.predict(test_features)))
    return {
        "ridge": _summarize(ridge_folds),
        "baseline": _summarize(baseline_folds),
    }, selected_alphas


def _configuration_hash() -> str:
    """Hash every training choice that can change model selection or evaluation."""

    configuration = {
        "feature_names": FEATURE_NAMES,
        "random_seed": RANDOM_SEED,
        "outer_folds": N_SPLITS,
        "inner_folds": N_SPLITS,
        "alpha_grid": ALPHA_GRID,
        "scikit_learn": sklearn.__version__,
        "evaluation_implementation": EVALUATION_IMPLEMENTATION_VERSION,
    }
    # Canonical JSON removes formatting and key-order differences from the hash input.
    encoded = json.dumps(configuration, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest().upper()


def train(
    training_csv: Path,
    prediction_csv: Path,
    model_path: Path,
    metadata_path: Path,
    predictions_path: Path,
) -> dict[str, Any]:
    """Build all mutually consistent artifacts from one validated source dataset."""

    data = load_training_data(training_csv)
    evaluation, outer_alphas = _evaluate_model(data)
    # Evaluation finishes first; the deployable model is then fit once on all available rows.
    final_alpha = _select_alpha(data.features, data.target)
    pipeline = _ridge(final_alpha)
    pipeline.fit(data.features, data.target)

    configuration_hash = _configuration_hash()
    # Version identity changes when either source bytes or training configuration changes.
    model_version = f"ridge-v1-{data.sha256[:8].lower()}-{configuration_hash[:8].lower()}"
    scaler: StandardScaler = pipeline.named_steps["scaler"]
    regressor: Ridge = pipeline.named_steps["ridge"]
    metadata: dict[str, Any] = {
        "model_name": "ridge_regression",
        "model_version": model_version,
        "feature_names": list(FEATURE_NAMES),
        "coefficient_space": "standardized",
        "hyperparameters": {"alpha": final_alpha},
        # strict=True makes a feature/coefficient length mismatch fail instead of
        # truncating silently.
        "coefficients": dict(zip(FEATURE_NAMES, map(float, regressor.coef_), strict=True)),
        "intercept": float(regressor.intercept_),
        "feature_mean": dict(zip(FEATURE_NAMES, map(float, scaler.mean_), strict=True)),
        "feature_scale": dict(zip(FEATURE_NAMES, map(float, scaler.scale_), strict=True)),
        "feature_ranges": data.feature_ranges,
        "training_rows": len(data.target),
        "training_data_sha256": data.sha256,
        "training_configuration_sha256": configuration_hash,
        "metrics": evaluation["ridge"],
        "baseline_metrics": evaluation["baseline"],
        "outer_selected_alphas": outer_alphas,
        "evaluation": {
            "protocol": "nested_5_fold_cross_validation",
            "random_seed": RANDOM_SEED,
            "outer_folds": N_SPLITS,
            "inner_folds": N_SPLITS,
            "alpha_grid": list(ALPHA_GRID),
            "standard_deviation_ddof": 0,
            "selection_metric": "mean_rmse",
            "tie_breaker": "smaller_alpha",
            "implementation_version": EVALUATION_IMPLEMENTATION_VERSION,
        },
        "dependencies": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scikit_learn": sklearn.__version__,
            "joblib": joblib.__version__,
        },
        "trained_at": datetime.now(UTC).isoformat(),
        "limitations": list(LIMITATIONS),
    }

    model_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    predictions_path.parent.mkdir(parents=True, exist_ok=True)
    # Store feature order beside the pipeline so startup can reject incompatible artifacts.
    joblib.dump({"pipeline": pipeline, "feature_names": list(FEATURE_NAMES)}, model_path)
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    prediction_features = load_prediction_data(prediction_csv)
    predicted_prices = pipeline.predict(prediction_features)
    # The reviewable prediction CSV uses a BOM for spreadsheet compatibility.
    with predictions_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow([*FEATURE_NAMES, "predicted_price", "model_version"])
        for features, price in zip(prediction_features, predicted_prices, strict=True):
            writer.writerow([*map(float, features), float(price), model_version])
    return metadata


def _repository_root() -> Path:
    """Locate the checkout without assuming the caller's current working directory."""

    source = Path(__file__).resolve()
    for candidate in (source.parent, *source.parents):
        if (candidate / "data/raw").is_dir() and (candidate / "services/ml-api").is_dir():
            return candidate
    return Path.cwd()


def main() -> None:
    """Expose deterministic training as a command-line entry point with overrideable paths."""

    root = _repository_root()
    parser = argparse.ArgumentParser(description="Train the deterministic housing Ridge model")
    parser.add_argument(
        "--training-csv", type=Path, default=root / "data/raw/House Price Dataset.csv"
    )
    parser.add_argument(
        "--prediction-csv", type=Path, default=root / "data/raw/Test Data For Prediction.csv"
    )
    parser.add_argument("--model-path", type=Path, default=root / "models/model.joblib")
    parser.add_argument("--metadata-path", type=Path, default=root / "models/metadata.json")
    parser.add_argument(
        "--predictions-path", type=Path, default=root / "data/processed/test_predictions.csv"
    )
    arguments = parser.parse_args()
    metadata = train(
        arguments.training_csv,
        arguments.prediction_csv,
        arguments.model_path,
        arguments.metadata_path,
        arguments.predictions_path,
    )
    print(
        json.dumps(
            {"model_version": metadata["model_version"], "metrics": metadata["metrics"]}, indent=2
        )
    )


# Importing this module must not retrain the model; only direct execution invokes the CLI.
if __name__ == "__main__":
    main()
