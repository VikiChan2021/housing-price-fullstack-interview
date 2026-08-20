"""Asynchronous, contract-validating HTTP boundary around the ML API."""

from collections.abc import Sequence
from typing import Protocol

import httpx
from pydantic import ValidationError

from app.schemas import MlPredictionResponse, PropertyFeatures


class UpstreamTimeout(RuntimeError):
    pass


class UpstreamUnavailable(RuntimeError):
    pass


class UpstreamBadGateway(RuntimeError):
    pass


class MlApiClient(Protocol):
    """Structural interface used by production HTTP code and lightweight test doubles."""

    async def predict(
        self, properties: Sequence[PropertyFeatures], request_id: str
    ) -> MlPredictionResponse: ...

    async def health(self) -> bool: ...

    async def ready(self) -> bool: ...

    async def aclose(self) -> None: ...


class HttpMlApiClient:
    """Reuse one bounded AsyncClient for predictions and dependency probes."""

    def __init__(
        self,
        base_url: str,
        timeout_seconds: float,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        # rstrip prevents double slashes while preserving any intentional URL path prefix.
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=httpx.Timeout(timeout_seconds),
            transport=transport,
        )

    async def predict(
        self, properties: Sequence[PropertyFeatures], request_id: str
    ) -> MlPredictionResponse:
        payload: object
        # The ML API supports both shapes; retain the compact object for a single estimate.
        if len(properties) == 1:
            payload = properties[0].model_dump()
        else:
            payload = [item.model_dump() for item in properties]
        try:
            response = await self._client.post(
                "/api/v1/predict", json=payload, headers={"X-Request-ID": request_id}
            )
        except httpx.TimeoutException as exc:
            raise UpstreamTimeout("ML API request timed out") from exc
        except httpx.RequestError as exc:
            raise UpstreamUnavailable("ML API is unavailable") from exc

        if response.status_code >= 400:
            # Reachable but unsuccessful dependencies map to a bad-gateway category.
            raise UpstreamBadGateway(f"ML API returned HTTP {response.status_code}")
        try:
            prediction = MlPredictionResponse.model_validate(response.json())
        except (ValueError, ValidationError) as exc:
            raise UpstreamBadGateway("ML API returned an invalid response") from exc
        # Validate semantic invariants that JSON schema validation alone cannot express.
        if prediction.count != len(properties) or len(prediction.predictions) != len(properties):
            raise UpstreamBadGateway("ML API returned the wrong prediction count")
        if [item.index for item in prediction.predictions] != list(range(len(properties))):
            raise UpstreamBadGateway("ML API returned predictions out of order")
        return prediction

    async def _probe(self, path: str) -> bool:
        """Collapse all dependency probe failures into a status used by health endpoints."""

        try:
            response = await self._client.get(path)
            return response.status_code == 200
        except httpx.RequestError:
            return False

    async def health(self) -> bool:
        return await self._probe("/health")

    async def ready(self) -> bool:
        return await self._probe("/ready")

    async def aclose(self) -> None:
        """Release pooled sockets during the FastAPI lifespan shutdown phase."""

        await self._client.aclose()
