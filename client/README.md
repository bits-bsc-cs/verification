# BITS Student Community Verification

A student verification website for the BITS Pilani community. This version ships as a static HTML/CSS site with minimal vanilla JS that calls the FastAPI backend (documented in `api_docs.md`) to handle Discord verification via institutional email OTPs.

## Why

- **Site's the easiest way for someone to verify and join matrix/discord**

## Status

- Frontend is complete and mirrors the reference template.
- Works against the FastAPI backend documented in `api_docs.md`.
- OTP flows (request, status, verify) are implemented with cooldown + validation.

## Local Dev

1. Clone the repo and `cd client` (this folder).
2. Start the FastAPI backend separately (`uvicorn main:app --reload --port 5000`).
3. Serve this directory via any static server, e.g. `python -m http.server 4173`.
4. Open `http://localhost:4173` and exercise the flow.

All requests go to `http://localhost:5000`, so keep ports aligned or update `src/app.js`.

### Deployment

- **GitHub Pages** (or any static hosting hitting the backend URL)

## Usage

1. **Enter Discord Username**: Provide your 2-32 character Discord handle.
2. **Enter Email**: Use your BITS Pilani email ending in `@*.bits-pilani.ac.in`.
3. **Request OTP**: Triggers `POST /verify` to send a code (cooldown enforced).
4. **Check Status**: Uses `GET /verify/status/{email}` to see pending/verified state.
5. **Submit OTP**: Uses `POST /verify/otp` to complete Discord verification.

Buttons stay disabled until inputs pass validation, ensuring only valid BITS emails reach the backend.

## Testing

- Manual: run backend locally, serve the static site, walk through username/email/OTP flow.
- Automated tests are not available in this repo.

## License

FOSS ftw.

See [LICENSE](LICENSE) file for details.

## Support

For issues or questions, please open an issue in the repo.
