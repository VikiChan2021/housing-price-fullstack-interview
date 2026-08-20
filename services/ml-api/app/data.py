"""Validate immutable source CSV files and convert them into typed NumPy arrays."""

import csv
import hashlib
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from app.constants import FEATURE_NAMES, INTEGER_FIELDS, PREDICTION_COLUMNS, TRAIN_COLUMNS


class DataContractError(ValueError):
    """Raised when an immutable source CSV violates the documented contract."""


@dataclass(frozen=True)
class TrainingData:
    """Validated training arrays plus provenance needed for reproducible artifacts."""

    features: NDArray[np.float64]
    target: NDArray[np.float64]
    identifiers: tuple[int, ...]
    sha256: str
    feature_ranges: dict[str, dict[str, float]]


def _read_rows(path: Path, expected_columns: tuple[str, ...]) -> list[dict[str, str]]:
    """Read a non-empty CSV only when its ordered header exactly matches the contract."""

    if not path.is_file():
        raise DataContractError(f"CSV file does not exist: {path}")
    # utf-8-sig consumes an optional BOM without changing the first column name.
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if tuple(reader.fieldnames or ()) != expected_columns:
            found = reader.fieldnames
            raise DataContractError(
                f"Unexpected columns in {path.name}: {found}; expected {expected_columns}"
            )
        rows = list(reader)
    if not rows:
        raise DataContractError(f"CSV file is empty: {path}")
    return rows


def _number(row: dict[str, str], field: str, row_number: int) -> float:
    """Parse one finite numeric cell and enforce integer-only fields before casting."""

    raw = row.get(field, "")
    if raw is None or raw.strip() == "":
        raise DataContractError(f"Missing {field} at data row {row_number}")
    try:
        value = float(raw)
    except ValueError as exc:
        raise DataContractError(f"Invalid number for {field} at data row {row_number}") from exc
    if not math.isfinite(value):
        raise DataContractError(f"Non-finite {field} at data row {row_number}")
    if field in INTEGER_FIELDS and not value.is_integer():
        raise DataContractError(f"Expected integer {field} at data row {row_number}")
    return value


def load_training_data(path: Path, expected_rows: int = 50) -> TrainingData:
    """Load the fixed training set while excluding identifiers from model features."""

    rows = _read_rows(path, TRAIN_COLUMNS)
    if len(rows) != expected_rows:
        raise DataContractError(f"Expected {expected_rows} training rows, found {len(rows)}")

    identifiers = tuple(int(_number(row, "id", index)) for index, row in enumerate(rows, 1))
    if len(set(identifiers)) != len(identifiers):
        raise DataContractError("Training identifiers must be unique")

    # Iterating FEATURE_NAMES here preserves the exact column order expected by the pipeline.
    features = np.asarray(
        [
            [_number(row, field, index) for field in FEATURE_NAMES]
            for index, row in enumerate(rows, 1)
        ],
        dtype=np.float64,
    )
    target = np.asarray(
        [_number(row, "price", index) for index, row in enumerate(rows, 1)], dtype=np.float64
    )
    # Ranges are stored per feature so inference can warn about extrapolation.
    feature_ranges = {
        name: {"min": float(features[:, index].min()), "max": float(features[:, index].max())}
        for index, name in enumerate(FEATURE_NAMES)
    }
    return TrainingData(
        features=features,
        target=target,
        identifiers=identifiers,
        sha256=hashlib.sha256(path.read_bytes()).hexdigest().upper(),
        feature_ranges=feature_ranges,
    )


def load_prediction_data(path: Path, expected_rows: int = 10) -> NDArray[np.float64]:
    """Load the supplied prediction rows using the same ordered feature contract."""

    rows = _read_rows(path, PREDICTION_COLUMNS)
    if len(rows) != expected_rows:
        raise DataContractError(f"Expected {expected_rows} prediction rows, found {len(rows)}")
    return np.asarray(
        [
            [_number(row, field, index) for field in FEATURE_NAMES]
            for index, row in enumerate(rows, 1)
        ],
        dtype=np.float64,
    )
