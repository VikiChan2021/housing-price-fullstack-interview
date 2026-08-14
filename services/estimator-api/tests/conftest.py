import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI


@asynccontextmanager
async def client_for(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            yield client


def request(app: FastAPI, method: str, path: str, **kwargs: object) -> httpx.Response:
    async def send() -> httpx.Response:
        async with client_for(app) as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(send())
