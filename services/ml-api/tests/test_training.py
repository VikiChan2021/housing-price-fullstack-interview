import csv
import json
from pathlib import Path

import joblib
import numpy as np

from app.constants import FEATURE_NAMES
from app.data import load_prediction_data
from app.training import train


def test_training_is_reproducible_and_writes_reviewable_artifacts(
    tmp_path: Path, repository_root: Path
) -> None:
    outputs = []
    for run in ("one", "two"):
        directory = tmp_path / run
        metadata = train(
            repository_root / "data/raw/House Price Dataset.csv",
            repository_root / "data/raw/Test Data For Prediction.csv",
            directory / "model.joblib",
            directory / "metadata.json",
            directory / "predictions.csv",
        )
        artifact = joblib.load(directory / "model.joblib")
        features = load_prediction_data(repository_root / "data/raw/Test Data For Prediction.csv")
        outputs.append((metadata, artifact["pipeline"].predict(features), directory))

    first, second = outputs
    assert first[0]["model_version"] == second[0]["model_version"]
    assert first[0]["metrics"] == second[0]["metrics"]
    assert first[0]["baseline_metrics"] == second[0]["baseline_metrics"]
    assert np.array_equal(first[1], second[1])
    assert first[0]["feature_names"] == list(FEATURE_NAMES)
    assert "id" not in first[0]["feature_names"]
    assert first[0]["training_rows"] == 50
    assert first[0]["metrics"]["r2_mean"] > 0.9
    assert first[0]["metrics"]["mae_mean"] > 0
    assert first[0]["metrics"]["rmse_mean"] > 0

    persisted = json.loads((first[2] / "metadata.json").read_text(encoding="utf-8"))
    assert persisted["training_data_sha256"].startswith("0E36C622")
    with (first[2] / "predictions.csv").open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 10
    assert all(float(row["predicted_price"]) > 0 for row in rows)
