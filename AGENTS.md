# Agent Instructions

These instructions apply to the entire repository.

> Portability note: `AGENTS.md` is a convenience/compatibility instruction file and is **not assumed to be a universal coding-agent standard**. Agents that do not natively consume this file must still read it when directed by `CODINGAGENT_TASK.md`. No project-critical rule may live only here; the agent-neutral task and project documentation remain authoritative for cross-agent handoff.

## Mission

Build a production-grade Checkmk 2.5 notification extension that sends notifications to an Apprise API server. Keep the Checkmk side intentionally small, auditable and dependency-light.

## Non-negotiable constraints

1. **License:** GPL-2.0-only. Do not change the repository to AGPLv3, GPLv3 or another license without explicit maintainer approval and a fresh compatibility review.
2. **Target:** Checkmk 2.5.x is the primary supported release line for v1.
3. **Public APIs only:** use documented Checkmk extension/plugin APIs. Do not depend on private/internal Checkmk modules when a supported public API exists.
4. **Notification method name:** `apprise`.
5. `NotificationParameters.name` must match the notification script name: `apprise`.
6. **Transport:** API-first. Use `POST /notify/{config_id}` against Apprise API.
7. **No bundled Apprise:** do not vendor the Apprise Python package and do not require `pip install apprise` on the Checkmk server.
8. **No runtime third-party dependency for the notification script** unless a later design decision explicitly approves one. Prefer Python standard library HTTP/TLS facilities.
9. **Secrets:** never print passwords, authorization headers, raw secret-bearing URLs or password-store values in normal or debug output.
10. **TLS verification defaults to enabled.** An opt-out may exist for controlled environments but must be explicit and visible.
11. **Timeouts are mandatory.** No unbounded HTTP request.
12. **Retry semantics must follow Checkmk:** exit `0` success, exit `1` temporary failure/retry sensible, exit `2` permanent failure/retry not sensible.
13. Do not implement an independent retry queue in v1. Checkmk/its notification spooler remains responsible for retry scheduling.
14. Keep host and service message generation deterministic and unit-testable.
15. Never silently swallow configuration errors.

## Coding style

- Python 3, compatible with the Python version shipped/supported by Checkmk 2.5.
- Type hints for non-trivial functions.
- Small pure functions for parsing, state mapping, payload building and sanitization.
- Security-sensitive behavior receives explicit tests.
- Avoid clever abstractions. The notification path must remain easy to audit.
- Keep provider-specific behavior out of this repository; provider routing belongs to Apprise.

## Source layout

The repository mirrors the intended Checkmk site-local paths below `src/local/`:

```text
src/local/share/check_mk/notifications/apprise
src/local/lib/python3/cmk_addons/plugins/apprise/rulesets/notification.py
```

Additional files may be introduced if justified, but do not move these integration entry points without a documented reason.

## Before completing a milestone

- Update `PROJECT_STATUS.md` with actual progress, verification results, blockers, and next steps.
- Run all repository tests.
- Run lint/static checks configured by the repository.
- Verify no secrets are present in fixtures or logs.
- Update `CHANGELOG.md` for user-visible changes.
- Update the relevant documentation when behavior or configuration changes.
- Preserve the milestone acceptance criteria in `docs/DEVELOPMENT_PLAN.md`.
