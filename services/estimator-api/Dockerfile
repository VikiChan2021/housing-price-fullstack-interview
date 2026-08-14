# syntax=docker/dockerfile:1.7
FROM python@sha256:423ed6ab25b1921a477529254bfeeabf5855151dc2c3141699a1bfc852199fbf

ARG UV_VERSION=0.11.32
ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ML_API_BASE_URL=http://ml-api:8000 \
    ML_API_TIMEOUT_SECONDS=3

WORKDIR /app
RUN pip install --no-cache-dir "uv==${UV_VERSION}" \
    && addgroup --system app \
    && adduser --system --ingroup app app
COPY services/estimator-api/pyproject.toml services/estimator-api/uv.lock ./
RUN uv sync --frozen --no-dev
COPY --chown=app:app services/estimator-api/app ./app

USER app
EXPOSE 8001
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8001/health', timeout=2)"

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
