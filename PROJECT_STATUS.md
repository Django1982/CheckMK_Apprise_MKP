# Project Status

> Persistent, coding-agent-neutral implementation state. Update this file during meaningful work and **before every handoff or end of session**. Do not rely on chat history or vendor-specific agent memory as the project record.

## Current state

- **Active milestone:** M3 – Routing & Formatting
- **Overall status:** M0.2 done (merged, PR #3); M0.2 and M1 done; M2 verified on a Checkmk 2.5 test site (mock Apprise)
- **Last verified milestone:** M0.2 – Technical Skeleton
- **Last updated:** 2026-10-01
- **Updated by:** Claude Code (M0.2 implementation session)

## Milestone overview

| Milestone | Status | Verification |
|---|---|---|
| M0.1 – Project Preparation | done | planning/repository baseline prepared; repository sanity assets included |
| M0.2 – Technical Skeleton | done | install/enable/uninstall, method selectable, form + validation + save/reload, stub invocation (exit 2) verified manually on a Checkmk 2.5 site (Python 3.13); `NOTIFY_PARAMETER_*` value dump deferred to M2 |
| M1 – Notification Core | done (mock-verified; merged in PR #4) | 48 unit tests + manual Checkmk runs against the mock for main events, failure paths, Unicode and log inspection; open: ack/downtime-end/custom/flapping-stop/host-UP manual runs (unit-tested only), HTTPS/TLS manual test (maintainer tests separately), real Apprise API |
| M2 – Native Checkmk UX | done (mock-verified) | `NOTIFY_PARAMETER_*` names/formats confirmed (bool `True`/`False`, int, empty tag omitted); explicit and password-store passwords reach the server as Basic auth; wrong password -> HTTP 401/exit 2; GUI hides stored password; log shows only parameter names. Not verified against a real Apprise 'locked' config |
| M3 – Routing & Formatting | not started | not yet implemented |
| M4 – Hardening | not started | not yet implemented |
| M5 – Release Readiness | not started | not yet implemented |

## Current objective

Verify M1 end-to-end against a real Apprise API and Checkmk 2.5, then continue with M2 (native UX, credentials) without prematurely implementing later milestones.

## Completed / verified

- Project architecture and initial technical scope documented.
- Checkmk 2.5 is the primary target for v1.
- Notification method/script name fixed as `apprise`.
- Checkmk exit-code contract documented: `0` success, `1` retryable failure, `2` permanent failure.
- Named Checkmk notification parameter mapping documented, e.g. `foo_bar` -> `NOTIFY_PARAMETER_FOO_BAR`.
- API-first Apprise design selected; no bundled Apprise runtime.
- GPL-2.0-only licensing decision documented for the Checkmk extension.
- GitHub repository/governance baseline prepared.
- Coding-agent handoff made vendor-neutral; `AGENTS.md` is supplemental rather than the sole instruction source.

## In progress

M1 code complete locally. Open items:
- end-to-end run against a real Apprise API (maintainer is arranging an instance);
- record real `NOTIFY_PARAMETER_*` value formats (bool/int/empty tag); the parser currently accepts true/false/1/0/yes/no/on/off and `True`/`False`;
- M3 will refine message layout (markdown escaping, URLs); M1 uses the plain TECHNICAL_SPEC layout for all formats;
- M2: authentication and password-store handling are not implemented (Apprise access mode still to be verified);
- HTTP classification is provisional until M4 (table in `docs/TECHNICAL_SPEC.md`); 424 is treated as temporary, redirects as permanent;
- flapping stop/disabled map to `info` (decision recorded in code and tests).

## Blockers

- None. (M2 decision recorded: using `cmk.utils.password_store.extract` for stored passwords was approved by the maintainer on 2026-10-01; see `docs/TECHNICAL_SPEC.md`, "Credentials".)

None. Notes:

- The site runs Python 3.13 (Checkmk 2.5); `pyproject.toml` still targets py312, harmless.
- Lessons: notification script line 2 must be `# <title>` (Checkmk dropdown name); `MatchRegex` error messages must be `Message(...)`, not `str`.
- Documentation TODO (M5): configure exactly one recipient in the Checkmk rule; "all contacts" calls the script once per contact and would send duplicates to Apprise.
- The stub exits 2 on purpose so it is not mistaken for working delivery.

## Decisions that must be preserved

- Use public/supported Checkmk extension APIs where available.
- Use `NotificationParameters` Ruleset API v1 with `name="apprise"`.
- Use Apprise API `POST /notify/{config_id}` as the v1 transport.
- Do not vendor Apprise or require a local Apprise CLI/Python installation.
- TLS verification defaults to enabled and requests require an explicit timeout.
- No custom retry queue in v1.
- Secrets must never be emitted to normal/debug output.
- Do not make an agent-specific instruction file the sole source of any critical rule.

## Verification log

Record only commands that were actually executed. Replace/add rows as work progresses.

| Date | Command / check | Result | Notes |
|---|---|---|---|
| 2026-10-01 | planning handoff/package preparation | passed | no Checkmk implementation exists yet |
| 2026-10-01 | `python -m unittest discover -s tests/unit -v` | passed (6 tests) | Python 3.10 locally; CI uses 3.12 |
| 2026-10-01 | `python -m ruff check .` | passed | ruff 0.16.9 |
| 2026-10-01 | `python scripts/build_mkp.py` | passed | apprise-0.1.0.mkp, reproducible (tested) |
| 2026-10-01 | manual: mkp add/enable, method selectable, form, validation, save/reload, mkp remove | passed | after fixes for script title line and `Message` validator crash; Checkmk 2.5 test site `dev` |
| 2026-10-01 | manual: test notification (host, recipient cmkadmin) | passed | stub output shown, exit 2, no traceback |
| 2026-10-01 | manual M2 via Checkmk against mock with `--user/--password`: explicit password, password-store password, wrong password, GUI secrecy, `notify.log` | passed | store value resolved at runtime; wrong passwords rejected with exit 2 |
| 2026-10-01 | manual M1 against `scripts/mock_apprise.py` via Checkmk (v0.2.0): host DOWN, downtime start, service WARN/CRIT/UNKNOWN, real RECOVERY (fake check result), flapping start, empty tag, plug-in output | passed | titles, Apprise `type`, `format`, tag omitted when empty all as specified; boolean/integer parameters accepted by the parser; a transient failure was shown by Checkmk as temporary (exit 1) |
| 2026-10-01 | manual M1 failure paths via Checkmk against mock: timeout, HTTP 503, connection refused (all exit 1, Checkmk retries), HTTP 400 (exit 2, no retry); Unicode plug-in output; `notify.log` inspected | passed | log contains only parameter names, no URL/config id/secret |
| 2026-10-01 | `python -m unittest discover -s tests/unit` | passed (48 tests) | M1 core incl. mock server transport tests |
| 2026-10-01 | `python -m unittest discover -s tests/unit` (M2 branch) | passed (59 tests) | adds authentication tests with a fake password store |
| 2026-10-01 | `python -m ruff check .` / `ruff format` | passed | |
| 2026-10-01 | `python scripts/build_mkp.py` | passed | apprise-0.2.0.mkp |

## Next concrete actions

1. Run the packaged M1 build (0.2.0) on the Checkmk test site against an Apprise API; fix findings; mark M1 `verified`.
2. Then M2 (notification core) per `CODINGAGENT_TASK.md`.

## Handoff notes

A future agent may be Codex, Claude, Gemini, or another coding agent. Do not assume access to previous chat context, hidden reasoning, IDE state, or vendor-specific memory. The repository contents plus this status file must be sufficient to continue safely.
