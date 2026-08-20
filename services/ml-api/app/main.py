"""Create the ML FastAPI application and own model-runtime startup lifecycle."""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from app.http import install_http_handlers
from app.routers import infrastructure_router, model_router, prediction_router
from app.runtime import ModelArtifactError, load_runtime


def _repository_root() -> Path:
    """Locate artifacts reliably for local runs started from different directories."""

    source = Path(__file__).resolve()
    for candidate in (source.parent, *source.parents):
        if (candidate / "models").is_dir() and (candidate / "services/ml-api").is_dir():
            return candidate
    return Path.cwd()


def _paths() -> tuple[Path, Path]:
    """Resolve explicit environment overrides before repository-local defaults."""

    model_path = os.getenv("ML_MODEL_PATH")
    metadata_path = os.getenv("ML_METADATA_PATH")
    if model_path and metadata_path:
        return Path(model_path), Path(metadata_path)
    root = _repository_root()
    return (
        Path(model_path or root / "models/model.joblib"),
        Path(metadata_path or root / "models/metadata.json"),
    )


def create_app(model_path: Path | None = None, metadata_path: Path | None = None) -> FastAPI:
    """Build an independently testable application with optional artifact paths."""

    configured_model, configured_metadata = _paths()
    chosen_model = model_path or configured_model
    chosen_metadata = metadata_path or configured_metadata

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        # Load once at startup; request handlers never retrain or deserialize per request.
        try:
            application.state.runtime = load_runtime(chosen_model, chosen_metadata)
            application.state.load_error = None
        except ModelArtifactError as exc:
            # Keep the process alive so health/readiness can expose the artifact failure.
            application.state.runtime = None
            application.state.load_error = str(exc)
        yield

    application = FastAPI(
        title="Housing Price ML API",
        version="0.1.0",
        description="Artifact-backed Ridge regression with deterministic nested CV training.",
        lifespan=lifespan,
    )
    install_http_handlers(application)
    application.include_router(prediction_router)
    application.include_router(model_router)
    application.include_router(infrastructure_router)
    return application


app = create_app()
