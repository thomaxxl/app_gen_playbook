# `nginx.conf`

See also:

- [../../../specs/contracts/deployment/README.md](../../../specs/contracts/deployment/README.md)

Minimal same-origin reverse proxy shape:

```nginx
server {
    listen 80;
    server_name _;

    location = / {
        return 302 /admin-app/;
    }

    location = /index.html {
        return 302 /admin-app/;
    }

    location = /admin-app {
        return 302 /admin-app/;
    }

    location = /admin-app/ {
        alias /app/frontend/dist/index.html;
        default_type text/html;
    }

    location /admin-app/assets/ {
        alias /app/frontend/dist/assets/;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:5656/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /docs {
        proxy_pass http://127.0.0.1:5656/docs;
    }

    location /jsonapi.json {
        proxy_pass http://127.0.0.1:5656/jsonapi.json;
    }

    location /ui/ {
        proxy_pass http://127.0.0.1:5656/ui/;
    }

    location /media/ {
        proxy_pass http://127.0.0.1:5656/media/;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /_protected_media/ {
        internal;
        alias /app/backend/data/media/;
    }
}
```

Notes:

- Keep `/admin-app/` and `/api` on one origin.
- Root `/` and `/index.html` redirect to `/admin-app/`.
- If the backend docs use extra assets, proxy those too.
- Use the `/_protected_media/` block only when the backend is configured for
  nginx media serving through `X-Accel-Redirect`.
