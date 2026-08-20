# syntax=docker/dockerfile:1.7
# Builder and runtime share one digest-pinned Node release while retaining separate contents.
FROM node@sha256:6f7b03f7c2c8e2e784dcf9295400527b9b1270fd37b7e9a7285cf83b6951452d AS builder

ARG NEXT_PUBLIC_BASE_PATH=""
WORKDIR /app
RUN npm install --global pnpm@11.15.1

COPY apps/web/package.json apps/web/pnpm-lock.yaml apps/web/pnpm-workspace.yaml ./
# Cache the content-addressed pnpm store without copying it into an image layer.
RUN --mount=type=cache,target=/pnpm/store pnpm config set store-dir /pnpm/store \
    && pnpm install --frozen-lockfile

COPY apps/web ./
# NEXT_PUBLIC values are compiled into browser assets and therefore must be set before build.
ENV NEXT_PUBLIC_BASE_PATH=${NEXT_PUBLIC_BASE_PATH} \
    NEXT_TELEMETRY_DISABLED=1
RUN pnpm build

FROM node@sha256:6f7b03f7c2c8e2e784dcf9295400527b9b1270fd37b7e9a7285cf83b6951452d AS runtime

ARG NEXT_PUBLIC_BASE_PATH=""
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    NEXT_PUBLIC_BASE_PATH=${NEXT_PUBLIC_BASE_PATH} \
    HOSTNAME=0.0.0.0 \
    PORT=3000 \
    ESTIMATOR_API_BASE_URL=http://estimator-api:8001 \
    MARKET_API_BASE_URL=http://market-api:8080 \
    WEB_API_TIMEOUT_SECONDS=10

WORKDIR /app
# Standalone output omits development dependencies and source files from the runtime image.
COPY --from=builder --chown=node:node /app/.next/standalone ./
COPY --from=builder --chown=node:node /app/.next/static ./.next/static

USER node
EXPOSE 3000
# Web readiness verifies both private business APIs through the configured base path.
HEALTHCHECK --interval=10s --timeout=6s --start-period=15s --retries=5 \
  CMD node -e "fetch('http://127.0.0.1:3000'+(process.env.NEXT_PUBLIC_BASE_PATH||'')+'/api/ready').then(r=>{if(!r.ok)process.exit(1)}).catch(()=>process.exit(1))"

CMD ["node", "server.js"]
