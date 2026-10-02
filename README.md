# Checkmk Apprise Notification Extension

A planned Checkmk 2.5 notification extension that forwards Checkmk notification events to an Apprise API server and lets Apprise perform the final provider routing.

> Status: working pre-release (0.x). Notification delivery, authentication and message formatting are implemented and tested against a mock and a real Apprise API; release readiness (M5) is still open. See [`PROJECT_STATUS.md`](PROJECT_STATUS.md).

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

Milestones M0.1 to M3 are done; M4 (hardening) is in progress, M5 (release readiness) is next. The current state, open items and verification log are in [`PROJECT_STATUS.md`](PROJECT_STATUS.md).

## Compatibility

| Component | Supported / verified |
|---|---|
| Checkmk | 2.5.x (Ruleset API v1); verified on a 2.5 test site, Python 3.13 |
| Apprise | **2.0** is the supported baseline. The message formats rely on Apprise's own format conversion; rich text needs the HTML to Markdown converter present in Apprise 2.0 |
| Apprise API | stateful endpoint `POST /notify/{config_id}`; only HTTP 200 counts as delivered |
| Notification script | Python standard library only, no Apprise package on the Checkmk server |

Message formats: **Plain text** (default) works everywhere. **Rich text** adds bold labels where a target supports formatting and falls back to the same plain text on targets that do not (for example Signal). Markdown is intentionally not offered because Apprise cannot convert it to plain text targets.

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
