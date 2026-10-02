# Changelog

All notable changes to this project are documented here.

The project follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [1.0.0] - 2026-10-02

First release. A Checkmk 2.5 notification method `apprise` that sends host and service notifications to an Apprise API server (`POST /notify/{config_id}`) and leaves provider routing to Apprise. License: GPL-2.0-only.

### Added

- Notification script `apprise` using only the Python standard library (no Apprise package on the Checkmk server) and a Checkmk Ruleset API v1 `NotificationParameters` form named `apprise`.
- Rule fields: Apprise base URL, configuration ID, routing tag, username and password (explicit or from the Checkmk password store), message format (plain text or rich text), TLS verification, optional CA certificate file for private CAs and self-signed certificates, request timeout.
- Deterministic host and service messages for problems, recoveries, acknowledgements, downtimes, flapping and custom notifications, mapped to the Apprise types `info`, `success`, `warning` and `failure`.
- Result classification to Checkmk exit codes: 0 delivered (HTTP 200 only), 1 temporary failure (timeouts, DNS/connection/TLS errors, HTTP 408/424/429/5xx), 2 permanent failure (invalid configuration or event, other 4xx, redirects). Checkmk's own spooler does the retries.
- Safety properties: TLS verification on by default, total request deadline (including DNS), response bodies read only up to 4 KiB and never printed, credentials, URL and Config ID never printed, redirects not followed, environment proxies ignored, bounded value sizes, visible warnings for disabled TLS verification and for credentials over plain HTTP.
- Reproducible MKP build (`scripts/build_mkp.py`) with SHA-256 checksum, tag-triggered release workflow, `scripts/mock_apprise.py` (stand-in Apprise API) and `scripts/notify_env_dump.py` (diagnostic script) for manual tests.
- Documentation: installation, configuration (Apprise access modes, tag syntax, examples), troubleshooting, compatibility matrix, technical specification, release checklist.
- 109 unit tests (mock HTTP servers, real self-signed certificates via `openssl`, cross-check against Apprise's own format converters when Apprise is installed) on Python 3.12 and 3.13.

### Notes

- Supported baseline: Checkmk 2.5.x, Apprise 2.0. Apprise's access modes `user`, `locked` (credentials and a specific tag) and `public` (a specific tag) are supported.
- Message formats: plain text (default) and rich text. Markdown is not offered because Apprise cannot convert Markdown to plain-text targets such as Signal.
- Checkmk passes no end time for downtimes to notification scripts; put the expected duration in the downtime comment.
- Select exactly one recipient in the Checkmk rule; Checkmk calls the script once per contact.
- `cmk.utils.password_store.extract` (not a documented public API, used by Checkmk's own plug-ins) resolves passwords from the password store, imported only when such a password is configured.
- Not verified: delivery on the Community Edition (only installation was checked), rich text on a target that renders formatting, the Checkmk Exchange submission requirements (no compatibility is claimed).
