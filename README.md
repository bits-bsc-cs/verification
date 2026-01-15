# BITS Student Community Verification

## Usage

This AIO container is built on `python:3.13-slim` and exposes two ports: 8000 for the frontend/client
and 5000 for the backend/server.

Its not just recommended but important to put these behind nginx or nginx proxy manager.
If you proxy `/verify*` paths to the backend port (5000) while serving static files on 8000, the existing frontend keeps working without code changes.

### Environment Configuration
- Copy `server/.env.example` to `server/.env` and fill in Discord, Resend, and other secrets.
- `docker-compose.yml` references `./server/.env` through `env_file`, so the same configuration powers both local dev and container runs.
- Server settings read env vars directly; `.env` is only a convenience for Compose.


### Usage
1. `cp server/.env.example server/.env` and populate secrets.
2. `mkdir -p db` to persist `verification.db` via the volume.
3. `docker compose up --build`.
4. Hit `http://localhost:8000` for the site (it reaches the API on `http://localhost:5000`).
5. Shut down with `docker compose down`.
