# syntax=docker/dockerfile:1.7
FROM node@sha256:6f7b03f7c2c8e2e784dcf9295400527b9b1270fd37b7e9a7285cf83b6951452d AS builder

ARG NEXT_PUBLIC_BASE_PATH=""
WORKDIR /app
RUN npm install --global pnpm@11.15.1

COPY apps/web/package.json apps/web/pnpm-lock.yaml apps/web/pnpm-workspace.yaml ./
RUN --mount=type=cache,target=/pnpm/store pnpm config set store-dir /pnpm/store \
    && pnpm install --frozen-lockfile

COPY apps/web ./
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
COPY --from=builder --chown=node:node /app/.next/standalone ./
COPY --from=builder --chown=node:node /app/.next/static ./.next/static

USER node
EXPOSE 3000
HEALTHCHECK --interval=10s --timeout=6s --start-period=15s --retries=5 \
  CMD node -e "fetch('http://127.0.0.1:3000'+(process.env.NEXT_PUBLIC_BASE_PATH||'')+'/api/ready').then(r=>{if(!r.ok)process.exit(1)}).catch(()=>process.exit(1))"

CMD ["node", "server.js"]
