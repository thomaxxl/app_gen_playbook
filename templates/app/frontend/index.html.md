# `frontend/index.html`

See also:

- [../../../specs/contracts/frontend/build-and-deploy.md](../../../specs/contracts/frontend/build-and-deploy.md)

Use a minimal Vite HTML shell with the SPA rooted under the same-origin app.

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>My App Admin</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

Notes:

- Keep this file at `frontend/index.html`.
- Do not rely on a separately generated Vite scaffold for this file.
