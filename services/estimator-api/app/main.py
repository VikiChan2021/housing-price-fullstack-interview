import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.http import install_http_handlers
from app.ml_client import HttpMlApiClient, MlApiClient
from app.routers import estimate_router, infrastructure_router


def create_app(client: MlApiClient | None = None) -> FastAPI:
    configured_client = client or HttpMlApiClient(
        base_url=os.getenv("ML_API_BASE_URL", "http://ml-api:8000"),
        timeout_seconds=float(os.getenv("ML_API_TIMEOUT_SECONDS", "3")),
    )

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        application.state.ml_client = configured_client
        yield
        await configured_client.aclose()

    application = FastAPI(
        title="Housing Price Estimator API",
        version="0.1.0",
        description="Validated estimate orchestration backed only by ML API HTTP calls.",
        lifespan=lifespan,
    )
    install_http_handlers(application)
    application.include_router(estimate_router)
    application.include_router(infrastructure_router)
    return application


app = create_app()
