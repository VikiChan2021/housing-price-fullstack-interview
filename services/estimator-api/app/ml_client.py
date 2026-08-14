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
    async def predict(
        self, properties: Sequence[PropertyFeatures], request_id: str
    ) -> MlPredictionResponse: ...

    async def health(self) -> bool: ...

    async def ready(self) -> bool: ...

    async def aclose(self) -> None: ...


class HttpMlApiClient:
    def __init__(
        self,
        base_url: str,
        timeout_seconds: float,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=httpx.Timeout(timeout_seconds),
            transport=transport,
        )

    async def predict(
        self, properties: Sequence[PropertyFeatures], request_id: str
    ) -> MlPredictionResponse:
        payload: object
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
            raise UpstreamBadGateway(f"ML API returned HTTP {response.status_code}")
        try:
            prediction = MlPredictionResponse.model_validate(response.json())
        except (ValueError, ValidationError) as exc:
            raise UpstreamBadGateway("ML API returned an invalid response") from exc
        if prediction.count != len(properties) or len(prediction.predictions) != len(properties):
            raise UpstreamBadGateway("ML API returned the wrong prediction count")
        if [item.index for item in prediction.predictions] != list(range(len(properties))):
            raise UpstreamBadGateway("ML API returned predictions out of order")
        return prediction

    async def _probe(self, path: str) -> bool:
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
        await self._client.aclose()
