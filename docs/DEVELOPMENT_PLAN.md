# Development Plan

## Milestones

| Milestone | Name | Outcome |
|---|---|---|
| M0.1 | Project Preparation | Repository, governance, CI baseline, licensing and agent brief are ready |
| M0.2 | Technical Skeleton | Installable Checkmk 2.5 MKP skeleton and native notification parameter UI |
| M1 | Notification Core | End-to-end Checkmk → Apprise API delivery |
| M2 | Native Checkmk UX | Production-ready parameter form and secret handling |
| M3 | Routing & Formatting | Stable tag routing and host/service message format |
| M4 | Hardening | Failure classification, TLS, timeout, logging and security tests |
| M5 | Release Readiness | Documentation, compatibility validation and release artifact |

---

## M0.1 – Project Preparation

### Scope

Prepare everything that should exist before feature implementation begins.

### Deliverables

- repository layout
- GPL-2.0-only license decision
- agent-neutral `CODINGAGENT_TASK.md`, persistent `PROJECT_STATUS.md`, and supplemental `AGENTS.md`
- README, changelog, contribution and security docs
- issue and pull request templates
- Dependabot for GitHub Actions
- baseline repository-sanity CI
- dependency review workflow where supported
- `.editorconfig`, `.gitattributes`, `.gitignore`
- documented `main` branch GitHub Ruleset
- no invented CODEOWNERS account

### Definition of Done

- repository can be initialized and pushed without cleanup work
- CI baseline passes
- project scope and out-of-scope list are explicit
- progress/handoff state is persisted in `PROJECT_STATUS.md` independently of any coding-agent vendor
- branch/merge policy is explicit
- licensing has no known GPLv2/AGPLv3 conflict

---

## M0.2 – Technical Skeleton

### Scope

Create the Checkmk extension entry points and a reproducible MKP package, without implementing the full notification client yet.

### Deliverables

```text
src/local/share/check_mk/notifications/apprise
src/local/lib/python3/cmk_addons/plugins/apprise/rulesets/notification.py
```

Plus:

- executable notification stub
- `NotificationParameters` definition named `apprise`
- initial configuration form
- package metadata/build procedure
- smoke-test installation procedure

### Definition of Done

- MKP builds
- MKP installs on Checkmk 2.5 test site
- `Apprise` method is selectable in notification Setup
- configuration form loads and stores values
- notification stub can be invoked by Checkmk without traceback

---

## M1 – Notification Core

### Scope

Implement reliable Checkmk → Apprise API notification delivery.

### Deliverables

- environment parser
- normalized notification model
- state/event mapping
- message builder
- Apprise API HTTP client
- result/error classifier
- redacted diagnostics
- unit tests

### Definition of Done

- successful mock API call returns 0
- retryable network/API failures return 1
- permanent configuration/request failures return 2
- no tested error path leaks credentials

---

## M2 – Native Checkmk UX

### Scope

Complete production-safe Setup integration.

### Deliverables

- URL/config ID fields
- authentication/secret fields validated against actual Apprise access modes
- Checkmk password store integration
- tag expression
- message format
- TLS verification
- timeout
- validation/help text

### Definition of Done

- named fields reach notification script with verified `NOTIFY_PARAMETER_*` names
- secrets resolve correctly at runtime
- GUI does not reveal stored secrets
- invalid obvious values are rejected before notification execution

---

## M3 – Routing & Formatting

### Scope

Turn raw monitoring events into useful human messages without encoding provider-specific behavior.

### Deliverables

- deterministic host template
- deterministic service template
- event-aware recovery/ack/downtime/flapping formatting
- Apprise tag pass-through
- content bounds

### Definition of Done

- host/service samples are covered by snapshots or exact string assertions
- type/tag/format payload fields are tested
- Apprise provider configuration remains entirely external

---

## M4 – Hardening

### Scope

Make failure behavior predictable and safe.

### Deliverables

- documented HTTP/error retry matrix
- TLS verification tests
- timeout tests
- DNS/connection failure tests
- Unicode tests
- secret-redaction tests
- safe response logging limits

### Definition of Done

- every important failure path maps deterministically to exit 1 or 2
- no unbounded network wait/read
- no raw secret in output

---

## M5 – Release Readiness

### Scope

Prepare v1.0.0 for real users.

### Deliverables

- install/update/uninstall docs
- configuration examples
- troubleshooting
- compatibility matrix
- release checklist
- changelog
- release MKP
- optional automated release build/checksum workflow

### Definition of Done

- clean installation test on supported Checkmk version(s)
- end-to-end delivery against a real Apprise API test instance
- release artifact reproducible from tagged source
- no unsupported compatibility claims
