# Project Status

> Persistent, coding-agent-neutral implementation state. Update this file during meaningful work and **before every handoff or end of session**. Do not rely on chat history or vendor-specific agent memory as the project record.

## Current state

- **Active milestone:** M0.2 – Technical Skeleton
- **Overall status:** M0.2 verified on a Checkmk 2.5 test site; M1 not started
- **Last verified milestone:** M0.1 – Project Preparation
- **Last updated:** 2026-10-01
- **Updated by:** Claude Code (M0.2 implementation session)

## Milestone overview

| Milestone | Status | Verification |
|---|---|---|
| M0.1 – Project Preparation | done | planning/repository baseline prepared; repository sanity assets included |
| M0.2 – Technical Skeleton | verified | install/enable/uninstall, method selectable, form + validation + save/reload, stub invocation (exit 2) verified manually on a Checkmk 2.5 site (Python 3.13); `NOTIFY_PARAMETER_*` value dump deferred to M2 |
| M1 – Notification Core | not started | not yet implemented |
| M2 – Native Checkmk UX | not started | not yet implemented |
| M3 – Routing & Formatting | not started | not yet implemented |
| M4 – Hardening | not started | not yet implemented |
| M5 – Release Readiness | not started | not yet implemented |

## Current objective

Implement M0.2 according to `CODINGAGENT_TASK.md` and `docs/DEVELOPMENT_PLAN.md` without prematurely implementing later milestones.

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

M0.2 verified (see log). Open carry-over: record real `NOTIFY_PARAMETER_*` names/value formats (bool/int/empty tag) in M2. M1 not started.

## Blockers

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
| - | `NOTIFY_PARAMETER_*` dump | not run | needs Apprise-independent temporary dump; moved to M2 |

## Next concrete actions

1. Start M1 (notification core) per `CODINGAGENT_TASK.md`.

## Handoff notes

A future agent may be Codex, Claude, Gemini, or another coding agent. Do not assume access to previous chat context, hidden reasoning, IDE state, or vendor-specific memory. The repository contents plus this status file must be sufficient to continue safely.
