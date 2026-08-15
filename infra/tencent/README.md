# Tencent Cloud deployment

Status: deployed and browser-verified on 2026-08-15.

The production portal is mounted below the existing BookSim site at:

```text
https://kandian.site/housing
```

The root `kandian.site` site remains unchanged. Nginx proxies only `/housing` and `/housing/` descendants to the Web container on loopback port 13300. The three backend ports are also loopback-only; service-to-service traffic uses the private Compose network.

Server deployment directory: `/home/codex-admin/housing-price-deploy`. All four services currently run under Compose project `housing-price-interview` with explicit memory limits. Direct public probes of ports 13300/18000/18001/18080 time out as expected; only Nginx ports 80/443 are public.

Production requirements:

- Build the Web image with `NEXT_PUBLIC_BASE_PATH=/housing`.
- Load the four verified `housing-price-*:local` images on the server.
- Copy root `compose.yaml` and `housing.env.example` to the isolated deployment directory.
- Start with `docker compose --env-file .env up --no-build -d --wait`.
- Install `nginx-housing.conf` as an Nginx snippet, include it only in the HTTPS `kandian.site` server block, run `nginx -t`, then reload.

Rollback order:

1. Remove the Nginx snippet include and reload Nginx.
2. Run `docker compose --env-file .env down` in the isolated deployment directory.
3. Restore the timestamped Nginx site backup if configuration validation fails.

Current Nginx backups:

- `/etc/nginx/backups/booksim-before-housing-20260815013813`
- `/etc/nginx/backups/booksim-before-housing-route-fix-20260815014151`

Do not commit the server `.env`, image archives, browser evidence, SSH keys, or deployment logs.
