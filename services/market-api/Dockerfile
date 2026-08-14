FROM maven@sha256:c07f7ccfb8ca6c9fa29ee523f00afa7d2ca6132c92f8652c4aebb5ee3491f502 AS builder

WORKDIR /build
COPY services/market-api/pom.xml ./
RUN mvn --batch-mode dependency:go-offline
COPY services/market-api/src ./src
RUN mvn --batch-mode package -DskipTests

FROM maven@sha256:c07f7ccfb8ca6c9fa29ee523f00afa7d2ca6132c92f8652c4aebb5ee3491f502 AS runtime

ENV MARKET_DATA_PATH=/app/data/house-price-dataset.csv \
    MARKET_CACHE_TTL_SECONDS=300 \
    MARKET_CACHE_MAX_ENTRIES=256 \
    ML_API_BASE_URL=http://ml-api:8000 \
    ML_API_TIMEOUT_SECONDS=5

WORKDIR /app
RUN useradd --system --create-home app
COPY --from=builder --chown=app:app /build/target/market-api-0.1.0.jar ./market-api.jar
COPY --chown=app:app ["data/raw/House Price Dataset.csv", "./data/house-price-dataset.csv"]

USER app
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=3s --start-period=20s --retries=3 \
  CMD curl --fail --silent http://127.0.0.1:8080/health > /dev/null || exit 1

ENTRYPOINT ["java", "-jar", "/app/market-api.jar"]
