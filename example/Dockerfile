FROM node:24-bookworm-slim AS frontend-build

WORKDIR /frontend
COPY frontend/package.json /frontend/package.json
COPY frontend/package-lock.json /frontend/package-lock.json
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
COPY --from=frontend-build /frontend/dist /app/frontend/dist
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY entrypoint.sh /app/entrypoint.sh

WORKDIR /app/backend
RUN python -m pip install --no-cache-dir -U pip \
    && python -m pip install --no-cache-dir -r requirements.txt \
    && chmod +x /app/entrypoint.sh

EXPOSE 80
CMD ["/app/entrypoint.sh"]
