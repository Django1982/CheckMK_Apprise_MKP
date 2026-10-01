# Project Status

> Persistent, coding-agent-neutral implementation state. Update this file during meaningful work and **before every handoff or end of session**. Do not rely on chat history or vendor-specific agent memory as the project record.

## Current state

- **Active milestone:** M0.2 – Technical Skeleton
- **Overall status:** not started
- **Last verified milestone:** M0.1 – Project Preparation
- **Last updated:** 2026-10-01
- **Updated by:** project planning handoff

## Milestone overview

| Milestone | Status | Verification |
|---|---|---|
| M0.1 – Project Preparation | done | planning/repository baseline prepared; repository sanity assets included |
| M0.2 – Technical Skeleton | not started | not yet implemented |
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

None. The next coding agent should mark M0.2 `in progress` when implementation actually begins.

## Blockers

None known at handoff time.

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

## Files / areas currently expected to change next

- `src/local/share/check_mk/notifications/apprise`
- `src/local/lib/python3/cmk_addons/plugins/apprise/rulesets/notification.py`
- MKP packaging/build metadata or scripts
- smoke-test/install documentation
- tests required for M0.2 baseline behavior

## Next concrete actions

1. Read `CODINGAGENT_TASK.md` and all mandatory documents in its stated order.
2. Reconcile this status with the actual repository tree.
3. Mark M0.2 `in progress` here.
4. Implement only the M0.2 Technical Skeleton scope first.
5. Run and record repository checks plus any new M0.2 tests/smoke checks.
6. Update this file before ending the session, including failures or incomplete work.

## Handoff notes

A future agent may be Codex, Claude, Gemini, or another coding agent. Do not assume access to previous chat context, hidden reasoning, IDE state, or vendor-specific memory. The repository contents plus this status file must be sufficient to continue safely.
