# Changelog

All notable changes to this project will be documented here.

The project follows Semantic Versioning once release artifacts begin.

## [Unreleased]

### Added

- M0.1 project preparation skeleton
- initial architecture and technical specification
- GitHub governance baseline
- coding-agent assignment
- M0.2 technical skeleton: `apprise` notification stub, `NotificationParameters` form (Ruleset API v1), reproducible stdlib MKP builder (`scripts/build_mkp.py`), unit tests, lint/test CI workflow and install smoke-test checklist
- M1 notification core: `NOTIFY_*` parsing and validation, event/state to Apprise type mapping, deterministic host/service title and body, JSON payload, bounded stdlib HTTP client (no redirects, TLS verification on by default), HTTP/network failure classification to Checkmk exit codes 0/1/2, 47 unit tests with a local mock server
- M2 authentication: optional HTTP Basic username and password (Checkmk `Password` form spec: explicit or password store), password-store resolution, visible warning for credentials over plain HTTP, mock server `--user/--password`
- M3 message formatting: Markdown escaping of all monitoring values, bold labels and hard line breaks in `markdown` format; `html` removed from the accepted formats
- M4 start: HTTP/transport classification hardening and tests (`tests/unit/test_hardening.py`); unit tests also run on Python 3.13 in CI

### Fixed

- message format: `markdown` is replaced by `html` (shown as "Rich text"); Apprise converts HTML to plain text, Markdown or HTML per target, whereas it cannot convert Markdown to plain text. Our own Markdown escaping is removed. Rules saved with the unreleased `markdown` value must be set to plain text or rich text again
- plain text is now the default message format; Apprise has no Markdown->Text converter, so Markdown showed raw `**` and backslashes on text-only targets such as Signal
- HTTP 204 (and any 2xx other than 200) was reported as delivered; it now fails with exit 2 because nothing was sent
- a missing `NOTIFY_NOTIFICATIONTYPE` was silently treated as `PROBLEM`; it is now an invalid event (exit 2)
- the "TLS verification disabled" warning is only printed for `https://` URLs
- environment proxy variables are ignored deterministically; certificate verification failures now state what to check

### Changed

- licensing decision set to GPL-2.0-only after Checkmk extension compatibility review
- corrected Checkmk notification exit-code semantics: 1 is retryable, 2 is permanent
