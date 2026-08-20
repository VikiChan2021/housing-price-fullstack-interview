# BuildKit cache mounting keeps Maven dependencies out of the final layer and accelerates rebuilds.
FROM maven@sha256:c07f7ccfb8ca6c9fa29ee523f00afa7d2ca6132c92f8652c4aebb5ee3491f502 AS builder

WORKDIR /build
COPY services/market-api/pom.xml ./
COPY services/market-api/src ./src
# Tests run in the verification workflow; the image build packages compiled production classes.
RUN --mount=type=cache,target=/root/.m2 \
  mvn --batch-mode package -Dmaven.test.skip=true

FROM maven@sha256:c07f7ccfb8ca6c9fa29ee523f00afa7d2ca6132c92f8652c4aebb5ee3491f502 AS runtime

ENV MARKET_DATA_PATH=/app/data/house-price-dataset.csv \
    MARKET_CACHE_TTL_SECONDS=300 \
    MARKET_CACHE_MAX_ENTRIES=256 \
    ML_API_BASE_URL=http://ml-api:8000 \
    ML_API_TIMEOUT_SECONDS=5

WORKDIR /app
RUN useradd --system --create-home app
# Copy only the executable JAR and immutable CSV into the non-root runtime image.
COPY --from=builder --chown=app:app /build/target/market-api-0.1.0.jar ./market-api.jar
COPY --chown=app:app ["data/raw/House Price Dataset.csv", "./data/house-price-dataset.csv"]

USER app
EXPOSE 8080
# Spring health reports dataset availability and the current ML dependency state.
HEALTHCHECK --interval=10s --timeout=3s --start-period=20s --retries=3 \
  CMD curl --fail --silent http://127.0.0.1:8080/health > /dev/null || exit 1

ENTRYPOINT ["java", "-jar", "/app/market-api.jar"]
