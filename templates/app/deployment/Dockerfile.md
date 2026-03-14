# `Dockerfile`

See also:

- [../../../specs/contracts/deployment/README.md](../../../specs/contracts/deployment/README.md)

Minimal same-origin image shape:

```dockerfile
FROM node:24-bookworm-slim AS frontend-build

WORKDIR /frontend
COPY frontend/package.json /frontend/package.json
RUN npm install
COPY frontend /frontend
RUN npm run build

FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash nginx \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend /app/backend
COPY reference /app/reference
COPY --from=frontend-build /frontend /app/frontend
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY entrypoint.sh /app/entrypoint.sh

WORKDIR /app/backend
RUN python -m pip install --no-cache-dir -U pip \
    && python -m pip install --no-cache-dir -r requirements.txt \
    && chmod +x /app/entrypoint.sh
EXPOSE 80
CMD ["/app/entrypoint.sh"]
```

Notes:

- Build the frontend in-image for a self-contained deployable image.
- Build the frontend in a Node `24.x` stage so the runtime Node version is not
  left to distro package defaults.
- Install `nginx.conf` into nginx's active config path, not just `/app/`.
- For dev mode, use a compose override instead of changing the default image.
- If the app supports uploaded files, create or mount a persistent media root
  in the runtime image instead of keeping uploaded bytes in an ephemeral layer.
