# `docker-compose.yml`

See also:

- [../../../specs/contracts/deployment/README.md](../../../specs/contracts/deployment/README.md)

Minimal compose shape:

```yaml
services:
  my-app:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      MY_APP_DB_PATH: /data/app.sqlite
    ports:
      - "8000:80"
    restart: unless-stopped
    volumes:
      - my_app_data:/data

volumes:
  my_app_data:
```

Notes:

- Keep SQLite on a volume.
- Publish nginx on one host port and proxy the rest internally.
- If the app supports uploaded files, keep the media root on a persistent
  volume too.
