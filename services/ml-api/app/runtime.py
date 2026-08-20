"""Load a validated model artifact once and provide ordered runtime inference."""

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import joblib
import numpy as np
from sklearn.pipeline import Pipeline

from app.constants import FEATURE_NAMES
from app.schemas import ModelInfo, PropertyFeatures, RangeWarning


class ModelArtifactError(RuntimeError):
    """Raised when model artifacts are missing, unreadable, or inconsistent."""


@dataclass(frozen=True)
class ModelRuntime:
    """Immutable pairing of executable pipeline and reviewable model metadata."""

    pipeline: Pipeline
    metadata: dict[str, Any]
    model_info: ModelInfo

    @property
    def model_version(self) -> str:
        return self.model_info.model_version

    def predict(self, items: list[PropertyFeatures]) -> list[float]:
        """Convert validated request models into the artifact's exact feature order."""

        matrix = np.asarray(
            [[getattr(item, feature) for feature in FEATURE_NAMES] for item in items],
            dtype=np.float64,
        )
        predictions = self.pipeline.predict(matrix)
        values = [float(value) for value in predictions]
        # A loaded artifact is still unusable if it produces non-finite or non-price outputs.
        if any(not math.isfinite(value) or value <= 0 for value in values):
            raise ModelArtifactError("Model produced an invalid price")
        return values

    def warnings_for(self, item: PropertyFeatures) -> list[RangeWarning]:
        """Describe inputs outside observed data ranges without rejecting valid API values."""

        ranges = cast(dict[str, dict[str, float]], self.metadata["feature_ranges"])
        warnings: list[RangeWarning] = []
        for field in FEATURE_NAMES:
            value = float(getattr(item, field))
            observed = ranges[field]
            if value < observed["min"] or value > observed["max"]:
                warnings.append(
                    RangeWarning(
                        field=field,
                        value=value,
                        training_min=observed["min"],
                        training_max=observed["max"],
                    )
                )
        return warnings


def load_runtime(model_path: Path, metadata_path: Path) -> ModelRuntime:
    """Fail closed when binary artifact, metadata, schema, or a smoke prediction disagree."""

    if not model_path.is_file() or not metadata_path.is_file():
        raise ModelArtifactError("Model artifact or metadata is missing")
    try:
        artifact = joblib.load(model_path)
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        artifact_features = tuple(artifact["feature_names"])
        metadata_features = tuple(metadata["feature_names"])
        # Equality checks both membership and order, which is essential for matrix inference.
        if artifact_features != FEATURE_NAMES or metadata_features != FEATURE_NAMES:
            raise ModelArtifactError("Artifact feature order does not match the API schema")
        ranges = metadata["feature_ranges"]
        if set(ranges) != set(FEATURE_NAMES):
            raise ModelArtifactError("Training ranges do not match the API schema")
        pipeline = artifact["pipeline"]
        # Pydantic validates the persisted metadata against the public model-info contract.
        model_info = ModelInfo.model_validate(
            {key: metadata[key] for key in ModelInfo.model_fields}
        )
        runtime = ModelRuntime(pipeline=pipeline, metadata=metadata, model_info=model_info)
        probe = PropertyFeatures(
            square_footage=1550,
            bedrooms=3,
            bathrooms=2,
            year_built=1997,
            lot_size=6800,
            distance_to_city_center=4.1,
            school_rating=7.6,
        )
        # A startup smoke prediction catches pipelines that deserialize but cannot execute.
        runtime.predict([probe])
        return runtime
    except ModelArtifactError:
        raise
    except Exception as exc:
        raise ModelArtifactError("Model artifact could not be loaded or validated") from exc
