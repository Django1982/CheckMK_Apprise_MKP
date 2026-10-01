# Checkmk Apprise Notification Extension

A planned Checkmk 2.5 notification extension that forwards Checkmk notification events to an Apprise API server and lets Apprise perform the final provider routing.

> Status: project preparation / pre-implementation skeleton.

## Intended architecture

```text
Checkmk Notification Engine
        │
        │ NOTIFY_* environment
        ▼
Checkmk Apprise notification script
        │
        │ HTTPS + JSON
        ▼
Apprise API /notify/{config_id}
        │
        ├── tag: ops
        ├── tag: network
        └── tag: critical
             │
             ▼
        downstream providers
```

The Checkmk integration deliberately remains provider-agnostic. Discord, Matrix, Gotify, mail, Slack and other destinations remain Apprise configuration concerns.

## Project state

The repository structure, project rules and implementation brief are prepared. The next implementation milestone is **M0.2 – Technical Skeleton**, followed by the notification core.

Start with:

- [`CODINGAGENT_TASK.md`](CODINGAGENT_TASK.md) – agent-neutral implementation assignment
- [`PROJECT_STATUS.md`](PROJECT_STATUS.md) – persistent implementation progress and handoff state
- [`AGENTS.md`](AGENTS.md) – supplemental repository-level agent rules; not assumed to be universal
- [`docs/DEVELOPMENT_PLAN.md`](docs/DEVELOPMENT_PLAN.md) – milestone plan
- [`docs/TECHNICAL_SPEC.md`](docs/TECHNICAL_SPEC.md) – technical contract
- [`docs/GITHUB_GOVERNANCE.md`](docs/GITHUB_GOVERNANCE.md) – GitHub and merge policy
- [`docs/LICENSING.md`](docs/LICENSING.md) – license decision and rationale
- [`docs/RESEARCH_SOURCES.md`](docs/RESEARCH_SOURCES.md) – primary references

## License

This Checkmk extension is planned as **GPL-2.0-only**. See [`docs/LICENSING.md`](docs/LICENSING.md) for the reason this differs from the initially considered AGPLv3 license.
