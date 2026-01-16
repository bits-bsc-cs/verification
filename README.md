# Verification System


## About

This is an AIO container that includes the site, the server, and the discord bot for verifying users
onto a discord server through their email addresses.


## Usage

The container exposes the following sets of ports (set in the compose file).
- 5000 ==> client side site
- 8000 ==> server
- 80, 443 ==> http connections
- 81 ==> NPM (nginx) web UI


## Nginx Part

Go to `http://<server ip>:81` on your web browser, then
- sign up with a strong password and an email address (will be used by letsencrypt tls)
- Add a proxy host for your site and point it to `http://verification:8000`
- Go to custom locations pane in that proxy host setting.
- In the custom locations, add the location path `/verify` with the forwarded route `http://verification:5000`

Make sure to enable security, certificates, and access lists according to your needs.


### Environment Configuration

- Copy `.env.example` to your compose file's directory, and fill in Discord, Resend, and other secrets.
- `docker-compose.yml` references `.env` through `env_file`, so the same configuration powers both local dev and container runs.
- Server settings read env vars directly; `.env` is only a convenience for Compose.


### Notes
- Currently, the db is sqlite. Don't expect hundreds of requests per minute.
- Default site is the BITS Student Community Verification site.
- The JavaScript of client is mostly AI made. @whiteboardguy is an htmx guy. Please give him bloat less lessons.

- These notes above may change as different database, custom site, and other options may be added in the future. 


## License
[GNU](./LICENSE) extremism ftw.
