import { fileURLToPath, URL } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";
function adminAppDevBase() {
    return {
        name: "admin-app-dev-base",
        configureServer(server) {
            server.middlewares.use((req, _res, next) => {
                if (req.url === "/admin-app") {
                    req.url = "/";
                }
                else if (req.url?.startsWith("/admin-app/")) {
                    req.url = req.url.replace(/^\/admin-app/, "") || "/";
                }
                next();
            });
        },
    };
}
export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, process.cwd(), "");
    const backendOrigin = env.VITE_BACKEND_ORIGIN || "http://127.0.0.1:5656";
    const proxyConfig = {
        "/api": backendOrigin,
        "/media": backendOrigin,
        "/ui": backendOrigin,
        "/jsonapi.json": backendOrigin,
        "/swagger.json": backendOrigin,
    };
    const fsPromisesShim = fileURLToPath(new URL("./src/shims/fs-promises.ts", import.meta.url));
    const safrsClientEntry = fileURLToPath(new URL("./node_modules/safrs-jsonapi-client/src/index.ts", import.meta.url));
    return {
        base: "/admin-app/",
        plugins: [adminAppDevBase(), react()],
        resolve: {
            alias: {
                "fs/promises": fsPromisesShim,
                "node:fs/promises": fsPromisesShim,
                "safrs-jsonapi-client": safrsClientEntry,
            },
        },
        server: {
            strictPort: true,
            proxy: proxyConfig,
        },
    };
});
