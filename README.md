# BITS Student Community Verification

## Usage

This AIO container is built on python slim image and exposes two ports: 8000 for the frontend/client
and 5000 for the backend/server.

Its not just recommended but important to put these behind nginx or nginx proxy manager.

If you proxy `/verify*` paths to the backend port (5000) while serving static files on 8000, the existing frontend keeps working without code changes (js is using the browser's URL api to find the backend's url).

(Image has inbuilt NginxProxyManager which is accessible at <ip_of_host>:81. Used the gui image for ease of use and remote management.)

For NPM, add a proxy host `example.com` -> `http://verification:8000` and a custom location `/verify` -> `http://verification:5000`, enable SSL, and toggle Force SSL/HTTP2 if desired.

### Environment Configuration
- Copy `server/.env.example` to `server/.env` and fill in Discord, Resend, and other secrets.
- `docker-compose.yml` references `./server/.env` through `env_file`, so the same configuration powers both local dev and container runs.
- Server settings read env vars directly; `.env` is only a convenience for Compose.


### Usage
1. `cp server/.env.example server/.env` and populate secrets.
2. `mkdir -p db npm/data npm/letsencrypt`.
3. `docker compose up --build`.
4. Log into NPM at `http://localhost:81` (default `admin@example.com` / `changeme`) and create the proxy host + `/verify` custom location.
5. Open firewall ports `80`, `81`, `443` only; keep `8000`/`5000` internal.
6. Visit `http://localhost:80` (or your domain) to reach the site, then shut down with `docker compose down`.
