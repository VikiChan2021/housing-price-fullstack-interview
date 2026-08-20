"""Transport tests for downstream status, timeout, probe, and payload validation."""

import asyncio

import httpx
import pytest

from app.ml_client import HttpMlApiClient, UpstreamBadGateway, UpstreamTimeout
from app.schemas import PropertyFeatures

PROPERTY = PropertyFeatures(
    square_footage=1550,
    bedrooms=3,
    bathrooms=2,
    year_built=1997,
    lot_size=6800,
    distance_to_city_center=4.1,
    school_rating=7.6,
)


def test_http_client_validates_success_and_probes() -> None:
    # MockTransport exercises HTTPX serialization and response parsing without opening a socket.
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v1/predict":
            assert request.headers["X-Request-ID"] == "request-1"
            return httpx.Response(
                200,
                json={
                    "predictions": [{"index": 0, "predicted_price": 250000, "warnings": []}],
                    "count": 1,
                    "model_version": "ridge-v1-test",
                    "request_id": "request-1",
                },
            )
        return httpx.Response(200)

    client = HttpMlApiClient("http://ml", 1, httpx.MockTransport(handler))

    async def scenario() -> None:
        prediction = await client.predict([PROPERTY], "request-1")
        assert prediction.predictions[0].predicted_price == 250000
        assert await client.health() is True
        assert await client.ready() is True
        await client.aclose()

    asyncio.run(scenario())


@pytest.mark.parametrize("status", [422, 500, 503])
def test_http_client_maps_upstream_status(status: int) -> None:
    transport = httpx.MockTransport(lambda _: httpx.Response(status))
    client = HttpMlApiClient("http://ml", 1, transport)

    async def scenario() -> None:
        with pytest.raises(UpstreamBadGateway, match=f"HTTP {status}"):
            await client.predict([PROPERTY], "request-1")
        await client.aclose()

    asyncio.run(scenario())


def test_http_client_maps_timeout_and_bad_payload() -> None:
    # Transport failure and schema failure intentionally map to different public categories.
    def timeout(_: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow")

    timeout_client = HttpMlApiClient("http://ml", 1, httpx.MockTransport(timeout))
    invalid_client = HttpMlApiClient(
        "http://ml", 1, httpx.MockTransport(lambda _: httpx.Response(200, json={"bad": True}))
    )

    async def scenario() -> None:
        with pytest.raises(UpstreamTimeout):
            await timeout_client.predict([PROPERTY], "request-1")
        with pytest.raises(UpstreamBadGateway, match="invalid response"):
            await invalid_client.predict([PROPERTY], "request-1")
        await timeout_client.aclose()
        await invalid_client.aclose()

    asyncio.run(scenario())
