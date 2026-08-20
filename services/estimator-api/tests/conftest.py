"""Lifespan-aware ASGI helpers for synchronous Estimator API tests."""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI


@asynccontextmanager
async def client_for(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    # Running the lifespan ensures the injected client is installed and closed exactly
    # as in production.
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            yield client


def request(app: FastAPI, method: str, path: str, **kwargs: object) -> httpx.Response:
    # Hide event-loop setup so contract cases can read as straightforward request/response tests.
    async def send() -> httpx.Response:
        async with client_for(app) as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(send())
