# syntax=docker/dockerfile:1.7
FROM python@sha256:423ed6ab25b1921a477529254bfeeabf5855151dc2c3141699a1bfc852199fbf AS builder

ARG UV_VERSION=0.11.32
WORKDIR /build

RUN pip install --no-cache-dir "uv==${UV_VERSION}"
COPY services/ml-api/pyproject.toml services/ml-api/uv.lock ./
RUN uv sync --frozen --no-dev

COPY services/ml-api/app ./app
COPY data/raw /source-data
RUN .venv/bin/python -m app.training \
    --training-csv "/source-data/House Price Dataset.csv" \
    --prediction-csv "/source-data/Test Data For Prediction.csv" \
    --model-path /artifacts/model.joblib \
    --metadata-path /artifacts/metadata.json \
    --predictions-path /artifacts/test_predictions.csv

FROM python@sha256:423ed6ab25b1921a477529254bfeeabf5855151dc2c3141699a1bfc852199fbf AS runtime

ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ML_MODEL_PATH=/app/models/model.joblib \
    ML_METADATA_PATH=/app/models/metadata.json

WORKDIR /app
RUN addgroup --system app && adduser --system --ingroup app app
COPY --from=builder --chown=app:app /build/.venv ./.venv
COPY --from=builder --chown=app:app /build/app ./app
COPY --from=builder --chown=app:app /artifacts ./models

USER app
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
