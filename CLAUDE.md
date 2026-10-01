# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this repository.

## State of the repo

M0.2 skeleton implemented (notification stub, ruleset form, MKP builder); delivery logic starts in M1. Commands:

```bash
python -m unittest discover -s tests/unit -v              # all tests
python -m unittest discover -s tests/unit -k MkpBuildTest  # single test (substring match)
python -m ruff check .                                    # lint (config in pyproject.toml)
python scripts/build_mkp.py                               # builds dist/apprise-<version>.mkp
```

CI: `repository-sanity` (required files/dirs, private-key scan) and `unit-tests` (ruff, unittest on Python 3.12 and 3.13, MKP build). Do not delete the files/dirs `repository-sanity` checks. `cmk` is not installable locally, so the ruleset file is only checked statically in tests; real verification needs a Checkmk 2.5 site (`docs/SMOKE_TEST.md`).

## Read first (agent-neutral source of truth)

Per `CODINGAGENT_TASK.md`, read in this order before changing anything: `CODINGAGENT_TASK.md`, `PROJECT_STATUS.md`, `AGENTS.md`, then `docs/` (`LICENSING`, `ARCHITECTURE`, `TECHNICAL_SPEC`, `DEVELOPMENT_PLAN`, `GITHUB_GOVERNANCE`, `RESEARCH_SOURCES`). `PROJECT_STATUS.md` is the persistent progress record: mark the milestone `in progress` when starting, and update it (with exact commands run and results, using the vocabulary `not started / in progress / blocked / implemented, not verified / verified / done`) before ending a session. Never keep a project-critical rule only in this file; mirror it in the agent-neutral docs. Milestones (M0.2 → M5) are defined in `CODINGAGENT_TASK.md` and `docs/DEVELOPMENT_PLAN.md`; implement only the active milestone's scope. `AGENTS.md` holds the non-negotiable constraints (GPL-2.0-only, public Checkmk APIs only, etc.).

## Architecture (big picture)

A Checkmk 2.5 notification script that turns Checkmk's `NOTIFY_*` environment into a JSON `POST /notify/{config_id}` to an Apprise API server. Apprise does all provider routing (via tags); the Checkmk side stays provider-agnostic.

Two integration entry points, mirroring site-local paths (do not move them):

- `src/local/share/check_mk/notifications/apprise` — the executable notification script (stdlib-only Python; no `requests`, no Apprise package, no shelling out to curl).
- `src/local/lib/python3/cmk_addons/plugins/apprise/rulesets/notification.py` — Ruleset API v1 `NotificationParameters` with `name="apprise"`, which must equal the script name.

Notification script pipeline, kept as small pure functions so each is unit-testable without Checkmk or Apprise: parse/validate env → normalize event → map event/state to Apprise `type` (`info|success|warning|failure`; event type takes precedence over current state so recoveries render as recoveries) → build title/body → build payload (`title`, `body`, `type`, `format`, optional `tag` only when configured) → bounded HTTP request → classify result → exit code.

Cross-file contracts that are easy to get wrong:

- Parameter dict key `foo_bar` reaches the script as `NOTIFY_PARAMETER_FOO_BAR`; the ruleset form keys and the script's env parsing must stay in sync.
- Exit codes: `0` sent, `1` temporary failure (Checkmk retries), `2` permanent failure. The HTTP status → exit code classification (esp. 401/403, 404, 408, 409, 429, 5xx) must be documented in M4. No custom retry queue.
- Secrets use Checkmk password-store form fields and must never appear in stdout/stderr, including exception text. TLS verify defaults on; every request has a timeout; build URLs with `urllib.parse` and validate `config_id`.
- Out of scope for v1: embedded Apprise/CLI transport, stateless `/notify/`, attachments, user templates, bulk notifications.

Tests go in `tests/unit` with `NOTIFY_*` fixtures in `tests/fixtures` and a local mock HTTP server for transport; no real Checkmk/Apprise required.
