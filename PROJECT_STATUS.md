# Project Status

> Persistent, coding-agent-neutral implementation state. Update this file during meaningful work and **before every handoff or end of session**. Do not rely on chat history or vendor-specific agent memory as the project record.

## Current state

- **Active milestone:** M4 – Hardening (started with the findings review below); M3 awaits its manual rendering check and PR
- **Overall status:** M0.1 to M2 done and merged to `main`; M3 implemented on branch `feat/message-formatting` (pushed, not merged); M4 in progress on branch `fix/http-classification`
- **Last verified milestone:** M2 – Native Checkmk UX (on a Checkmk 2.5 test site against `scripts/mock_apprise.py`)
- **Last updated:** 2026-10-01
- **Updated by:** Claude Code

## Milestone overview

| Milestone | Status | Verification |
|---|---|---|
| M0.1 – Project Preparation | done | repository baseline and sanity CI |
| M0.2 – Technical Skeleton | done | install/enable/uninstall, method selectable, form validation, save/reload verified on a Checkmk 2.5 site (Python 3.13) |
| M1 – Notification Core | done (mock-verified) | manual Checkmk runs against the mock for host/service problem, recovery, UNKNOWN, downtime start, flapping start, failure paths, Unicode, log inspection. Manual runs still open: acknowledgement, downtime end, custom, flapping stop, host UP (unit-tested only) |
| M2 – Native Checkmk UX | done (mock-verified) | `NOTIFY_PARAMETER_*` formats confirmed (bool `True`/`False`, int, empty tag omitted); explicit and password-store passwords sent as Basic auth; wrong password -> HTTP 401/exit 2; GUI hides the password; log shows only parameter names |
| M3 – Routing & Formatting | implemented, not verified | Markdown escaping, bold labels, hard line breaks, `html` removed; tag pass-through, type mapping and content bounds from M1; unit-tested; manual rendering check pending; no Checkmk deep links (deliberate) |
| M4 – Hardening | in progress | external review findings applied (see below); HTTPS/TLS manual test pending (maintainer, against a real instance) |
| M5 – Release Readiness | not started | |

## Current objective

Finish M4: land the classification fixes, then document timeouts/limits and extend tests; then M5 (installation, configuration and troubleshooting docs, compatibility matrix, release checklist, release MKP).

## Findings review (external review, 2026-10-01)

| Finding | Decision |
|---|---|
| HTTP 204 treated as success (P0) | Fixed: only 200 is delivered; every other 2xx is exit 2. Current Apprise API answers 404 for an empty configuration; older versions answered 204 |
| 424 ambiguous (P1) | Kept as exit 1, documented as a deliberate trade-off with troubleshooting hint |
| TLS certificate failure retryable (P1) | Kept as exit 1 deliberately (alerts should not be lost while an admin fixes the certificate); message now says what to check. Open for maintainer decision: switch to exit 2 |
| Missing `NOTIFICATIONTYPE` defaulted to PROBLEM (P1) | Fixed: invalid event, exit 2 |
| Implicit environment proxies (P2) | Decided: ignored, documented, test proves it |
| TLS-disabled warning on `http://` (P2) | Fixed: only for `https://` |
| TLS/DNS tests (P2) | Added classification tests per exception type; DNS test no longer uses the network |
| `PROJECT_STATUS.md` stale (P3) | Fixed (this file) |
| CI only Python 3.12 (P3) | CI now runs the unit tests on 3.12 and 3.13 (single `unit-tests` job) |

## Open items

- Real Apprise API (maintainer tests at home): `locked` mode with Basic auth and tag, HTTPS with a real certificate, how Markdown renders on a real target.
- M1 manual events listed above.
- Documentation (M5): configure exactly one recipient in the Checkmk rule; "all contacts" calls the script once per contact and would send duplicates. Repeated 424 means: check routing tags and the Apprise configuration.
- Maintainer decision: TLS certificate verification failure exit code (1 now).

## Blockers

None. Approved decision: stored passwords are resolved with `cmk.utils.password_store.extract` (not a documented public API; see `docs/TECHNICAL_SPEC.md`, "Credentials").

Lessons: notification script line 2 must be `# <title>` (Checkmk dropdown name); `MatchRegex` error messages must be `Message(...)`, not `str`; Checkmk flattens tuple parameters (`PASSWORD` -> `NOTIFY_PARAMETER_PASSWORD_1/_2/_3_1/_3_2`).

## Decisions that must be preserved

- Use public/supported Checkmk extension APIs where available (documented exception: password store lookup).
- Use `NotificationParameters` Ruleset API v1 with `name="apprise"`.
- Use Apprise API `POST /notify/{config_id}` as the v1 transport.
- Do not vendor Apprise or require a local Apprise CLI/Python installation.
- TLS verification defaults to enabled and requests require an explicit timeout.
- No custom retry queue in v1.
- Secrets must never be emitted to normal/debug output.
- Only HTTP 200 counts as delivered; redirects and environment proxies are not used.
- Do not make an agent-specific instruction file the sole source of any critical rule.

## Verification log

Record only commands that were actually executed.

| Date | Command / check | Result | Notes |
|---|---|---|---|
| 2026-10-01 | manual M0.2 on Checkmk 2.5 site `dev` | passed | install, method selectable, form, validation, save/reload, remove; after fixes for the script title line and the `Message` validator crash |
| 2026-10-01 | manual M1 against `scripts/mock_apprise.py` via Checkmk | passed | events, failure paths (timeout/503/refused -> exit 1; 400 -> exit 2), Unicode, `notify.log` free of URL/config id/secret |
| 2026-10-01 | manual M2 via Checkmk against the mock with `--user/--password` | passed | explicit and password-store password, wrong password rejected, GUI secrecy |
| 2026-10-01 | `python -m unittest discover -s tests/unit` (main + this fix branch) | passed (73 tests) | includes `test_hardening.py`; Python 3.10 locally |
| 2026-10-01 | mutation check of the proxy test | passed | test fails without `ProxyHandler({})` |
| 2026-10-01 | `python -m ruff check .` / `ruff format` | passed | ruff 0.16.9 |
| 2026-10-01 | `python scripts/build_mkp.py` | passed | apprise-0.3.1.mkp |
| - | manual HTTPS/TLS test, real Apprise API | not run | maintainer, later |

## Next concrete actions

1. Merge `fix/http-classification` (PR), then rebase `feat/message-formatting`, run the manual Markdown check on the test site and merge M3.
2. M4 remainder: response/log size bounds review, timeout behavior notes, TLS tests against a real certificate (maintainer).
3. M5: documentation set, compatibility matrix, release checklist, release MKP.

## Handoff notes

A future agent may be Codex, Claude, Gemini, or another coding agent. Do not assume access to previous chat context, hidden reasoning, IDE state, or vendor-specific memory. The repository contents plus this status file must be sufficient to continue safely.
