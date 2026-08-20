"""Shared fixtures that train one real artifact and drive FastAPI lifespan-aware requests."""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI

from app.training import train


@pytest.fixture(scope="session")
def repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


@pytest.fixture(scope="session")
def trained_artifacts(
    tmp_path_factory: pytest.TempPathFactory, repository_root: Path
) -> tuple[Path, Path]:
    # Training once per session keeps API tests realistic without repeating nested CV per case.
    directory = tmp_path_factory.mktemp("trained-model")
    model_path = directory / "model.joblib"
    metadata_path = directory / "metadata.json"
    train(
        repository_root / "data/raw/House Price Dataset.csv",
        repository_root / "data/raw/Test Data For Prediction.csv",
        model_path,
        metadata_path,
        directory / "predictions.csv",
    )
    return model_path, metadata_path


@asynccontextmanager
async def client_for(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    # ASGITransport avoids a network port while executing the real middleware and route stack.
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            yield client


def request(app: FastAPI, method: str, path: str, **kwargs: object) -> httpx.Response:
    # Tests remain synchronous while each request still runs in a complete async
    # application lifespan.
    async def send() -> httpx.Response:
        async with client_for(app) as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(send())
