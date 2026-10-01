# Handoff

This archive is intentionally a **planning + repository skeleton**, not a finished plugin.

The coding agent should start at `CODINGAGENT_TASK.md`, then read `PROJECT_STATUS.md` and the referenced project documentation.

`AGENTS.md` is supplemental and intentionally **not treated as a universal agent standard**. Codex, Claude, Gemini and other tools may use different native instruction files; the agent-neutral task and status files are the portable handoff contract.

Prepared milestones:

- M0.1: repository/project preparation baseline
- M0.2: next implementation target, technical Checkmk MKP skeleton

Important corrections captured in this handoff:

- Checkmk extension license: GPL-2.0-only for this project
- Checkmk notification exit codes: 0 success, 1 retryable, 2 permanent
- named notification parameters: `foo_bar` → `NOTIFY_PARAMETER_FOO_BAR`
