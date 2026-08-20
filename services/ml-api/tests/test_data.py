"""Contract tests for source-row counts, BOM handling, hashes, and feature ordering."""

from pathlib import Path

import pytest

from app.constants import FEATURE_NAMES
from app.data import DataContractError, load_prediction_data, load_training_data


def test_training_loader_handles_bom_and_excludes_id(repository_root: Path) -> None:
    data = load_training_data(repository_root / "data/raw/House Price Dataset.csv")

    # Shape, order, IDs, and hash together pin the exact immutable interview input.
    assert data.features.shape == (50, 7)
    assert data.target.shape == (50,)
    assert data.identifiers == tuple(range(1, 51))
    assert tuple(data.feature_ranges) == FEATURE_NAMES
    assert data.sha256 == "0E36C6224E1F6FB97C308C9DBE1D6DA22D78D78055181067F8AC4C7155A4A726"


def test_prediction_loader_preserves_ten_rows(repository_root: Path) -> None:
    data = load_prediction_data(repository_root / "data/raw/Test Data For Prediction.csv")

    assert data.shape == (10, 7)
    assert data[0].tolist() == [1550.0, 3.0, 2.0, 1997.0, 6800.0, 4.1, 7.6]


def test_training_loader_rejects_wrong_row_count(repository_root: Path) -> None:
    with pytest.raises(DataContractError, match="Expected 51 training rows"):
        load_training_data(repository_root / "data/raw/House Price Dataset.csv", expected_rows=51)
