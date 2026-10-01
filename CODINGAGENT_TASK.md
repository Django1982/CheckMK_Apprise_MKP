# Coding Agent Assignment: Checkmk Apprise Extension

## 1. Objective

Implement the foundation and then the first production-capable version of a Checkmk notification extension that forwards Checkmk host/service notifications to an Apprise API server.

The repository has already completed the design/research pass. Treat this assignment, `PROJECT_STATUS.md`, the documents in `docs/`, and repository policy files as the project specification. If implementation reality conflicts with the specification, verify the behavior against the current **Checkmk 2.5** and **Apprise API** primary documentation/source, document the discrepancy, and make the smallest safe correction.

### Agent-tool portability

This assignment is intentionally **coding-agent neutral**. It may be executed with Codex, Claude, Gemini, or another capable coding agent.

`AGENTS.md` is included as a repository-level compatibility/instruction file, but **it is not a universal standard and must not be assumed to be automatically consumed by every coding agent**. Different agents and IDE/CLI integrations may use their own native instruction files or precedence rules.

Therefore:

- always read `CODINGAGENT_TASK.md` explicitly, regardless of agent runtime;
- always read `PROJECT_STATUS.md` before making changes;
- read `AGENTS.md` as supplemental repository policy even if the current agent does not recognize it natively;
- do not place a critical project requirement only in an agent-specific file such as `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, or equivalent;
- if an agent-specific instruction file is introduced later, mirror all project-critical rules in agent-neutral project documentation;
- when instructions conflict, do not silently choose a tool-specific rule over the project specification; document the conflict and follow the maintainer/project-level decision.

This keeps handoffs portable between coding agents and prevents project state from living only inside one vendor's agent conventions.

Do not redesign the project into a generic framework.

## 2. Mandatory reading order

1. `CODINGAGENT_TASK.md` (this file)
2. `PROJECT_STATUS.md`
3. `AGENTS.md` (supplemental; see agent-tool portability above)
4. `docs/LICENSING.md`
5. `docs/ARCHITECTURE.md`
6. `docs/TECHNICAL_SPEC.md`
7. `docs/DEVELOPMENT_PLAN.md`
8. `docs/GITHUB_GOVERNANCE.md`
9. `docs/RESEARCH_SOURCES.md`

## 3. Work order

### M0.1 – Project Preparation

The repository already contains the initial M0.1 structure. Review it and complete/fix anything required for a healthy public open-source repository.

Deliverables:

- validate `.gitignore`, `.gitattributes`, `.editorconfig`
- validate issue forms and PR template
- validate `SECURITY.md`, `CONTRIBUTING.md`, license metadata and SPDX usage
- validate Dependabot and CI workflow syntax
- ensure CI has unique job/check names suitable for branch protection
- keep `CODEOWNERS` free of invented accounts; add real owners only when repository identity is known
- document exact GitHub Ruleset settings to apply to `main`
- do not create fake organization/user names

Acceptance criteria:

- clean repository initialization succeeds
- GitHub workflow YAML parses
- no workflow needs repository secrets for baseline tests
- baseline CI succeeds before Checkmk code exists
- governance documentation is actionable by a maintainer

### M0.2 – Technical Skeleton

Create the smallest installable Checkmk 2.5 extension skeleton.

Required entry points:

```text
src/local/share/check_mk/notifications/apprise
src/local/lib/python3/cmk_addons/plugins/apprise/rulesets/notification.py
```

Requirements:

- notification script is executable in the resulting MKP
- Checkmk discovers the `apprise` notification method
- `NotificationParameters` uses `name="apprise"`
- use the supported Ruleset API v1 approach; do not use the removed legacy notification parameter registry approach
- provide the initial parameter form described in `docs/TECHNICAL_SPEC.md`
- create an MKP build/package workflow or documented reproducible build procedure
- use Semantic Versioning for package versioning
- include a smoke-test/checklist for installing the package into a clean Checkmk 2.5 site

Acceptance criteria:

- MKP can be built reproducibly from the repository
- package installs into a Checkmk 2.5 test site
- notification method appears in Setup
- parameter UI renders without traceback
- uninstall removes only files owned by this package

### M1 – Notification Core

Implement the end-to-end notification path.

Required functional separation:

1. read and validate Checkmk `NOTIFY_*` environment
2. normalize event
3. map event/state to Apprise notification type
4. build title/body
5. build JSON payload
6. perform bounded HTTPS/HTTP request to Apprise API
7. classify result into Checkmk exit code semantics
8. sanitize output/logging

Do not add internal background jobs or queues.

Acceptance criteria:

- successful Apprise API response => exit 0
- timeout/connection/transient server error => exit 1 when retry is sensible
- invalid local configuration/non-retryable request => exit 2
- secrets never appear in stdout/stderr under tested failures
- unit tests cover host, service, recovery, warning, critical/down, acknowledgement/downtime/custom where applicable

### M2 – Native Checkmk Configuration UX

Complete the Checkmk configuration form and parameter handling.

Initial fields:

- Apprise API base URL
- Config ID
- authentication mode/credentials only as required by verified Apprise API behavior
- routing tag expression
- message format (`markdown` default; optional `text` and `html` if supported cleanly)
- TLS verification (`true` default)
- request timeout

Use Checkmk password-store capable form fields for secrets. Verify how the selected public Checkmk API resolves password-store references into notification parameters; do not guess.

Acceptance criteria:

- named dictionary keys arrive at the script as `NOTIFY_PARAMETER_<UPPERCASE_KEY>` according to Checkmk behavior
- password-store handling works without exposing the stored secret in UI/log output
- form validation prevents obviously invalid configuration

### M3 – Routing and Message Formatting

Implement stable message templates and Apprise tag routing.

Requirements:

- Apprise remains responsible for downstream providers
- support tag expressions accepted by the selected Apprise API version
- preserve a provider-neutral title/body
- produce useful host-only and service-specific messages
- limit/normalize unexpectedly large Checkmk values before sending/logging

Acceptance criteria:

- tag is passed only when configured
- `type` is one of `info`, `success`, `warning`, `failure`
- `format` matches supported Apprise API values
- tests prove state/type mapping and deterministic formatting

### M4 – Hardening

Focus on correctness and safe failure.

Required coverage:

- TLS verification behavior
- timeout behavior
- malformed URL/config ID
- HTTP 4xx classification
- HTTP 429 classification
- HTTP 5xx classification
- DNS/connection failures
- invalid/non-JSON server responses if relevant
- response-size/log-size bounds
- secret redaction
- Unicode/non-ASCII notification content

Explicitly document the chosen retry classification, especially for `401/403`, `404`, `408`, `409`, `429`, and `5xx`.

### M5 – Release Readiness

Deliver release-quality documentation and artifact generation.

Required:

- installation guide
- configuration guide with Apprise tag examples
- troubleshooting guide
- compatibility matrix
- release checklist
- changelog
- MKP artifact
- checksums for release artifact if release workflow is implemented

Do not claim Checkmk Exchange compatibility until an actual package has been checked against its current submission requirements.

## 4. Technical contracts already verified

### Checkmk notification exit codes

From current Checkmk notification source semantics:

- `0` = notification successfully sent
- `1` = could not send now; retry later
- `2` = cannot send; retry does not make sense

These meanings are normative for this project.

### Checkmk parameter environment

Checkmk notification parameter dictionaries are added to the event context with the `PARAMETER` prefix and finally exported to notification scripts with `NOTIFY_` prefix. A dictionary key such as `foo_bar` is represented as:

```text
NOTIFY_PARAMETER_FOO_BAR
```

### Apprise API target

Use the stateful saved-configuration endpoint:

```http
POST /notify/{config_id}
Content-Type: application/json
```

Payload is centered on:

```json
{
  "title": "...",
  "body": "...",
  "type": "failure",
  "format": "markdown",
  "tag": "critical"
}
```

`body` is required. `type` supports `info`, `success`, `warning`, `failure`. `format` supports `text`, `markdown`, `html` in current Apprise API documentation. Tag handling may be restricted by an Apprise configuration's access mode; verify authentication/access behavior during implementation.

## 5. Proposed initial state mapping

Keep mapping in one explicit, tested function. Initial proposal:

| Checkmk condition/event | Apprise type |
|---|---|
| host UP / service OK / recovery | `success` |
| service WARN | `warning` |
| service CRIT / host DOWN | `failure` |
| UNKNOWN | `warning` |
| acknowledgement | `info` |
| downtime start/end | `info` |
| downtime cancelled | `warning` |
| flapping start | `warning` |
| flapping stop | `success` or `info` — choose once and document |
| custom notification | `info` |

If Checkmk exposes event type separately from current state, notification type/event context must take precedence where necessary so that a recovery is rendered as a recovery rather than merely the current state.

## 6. Security requirements

- no credentials in repository fixtures
- no authorization header in logs
- no raw secret-bearing endpoint URLs in logs
- redact credentials from exception text if a lower layer includes them
- TLS verification enabled by default
- explicit request timeout
- avoid redirects to unexpected schemes/hosts unless the HTTP implementation's behavior is reviewed and documented
- bounded response read if response bodies are logged
- use `urllib.parse` or equivalent safe URL construction; do not concatenate unescaped config IDs into arbitrary URLs without validation
- do not execute shell commands to invoke curl

## 7. Testing strategy

Unit tests must not require a real Checkmk or Apprise server.

Use fixtures for `NOTIFY_*` environments and a local/mock HTTP server for transport behavior. Integration testing against real Checkmk/Apprise may be documented separately and should not become mandatory for every local unit-test run.

Minimum test groups:

- environment parsing
- state/event mapping
- title/body generation
- payload generation
- parameter validation
- URL construction
- HTTP status/error classification
- secret redaction
- Unicode
- exit code behavior

## 8. Out of scope for v1

Do not add these unless the maintainers explicitly move them into scope:

- embedded Apprise Python library
- local Apprise CLI transport
- stateless `/notify/` mode with raw provider URLs
- attachments/graphs
- Jinja or arbitrary user templates
- automatic discovery of Apprise services
- Checkmk bulk notification support
- custom retry queue
- provider-specific settings in Checkmk

## 9. Persistent progress and handoff protocol

`PROJECT_STATUS.md` is the **persistent, agent-neutral source of truth for implementation progress**. Chat history, an agent's private context, IDE state, or an agent-specific instruction file must never be the only place where project progress is recorded.

Every coding agent must:

1. read `PROJECT_STATUS.md` before changing files;
2. reconcile it with the actual repository state before trusting a previous `done` claim;
3. set the active milestone/work item to `in progress` when substantive work begins;
4. update it after a meaningful checkpoint and always before ending a work session or handing off to another agent;
5. record only work that actually exists in the repository;
6. distinguish `implemented` from `verified` — untested work is never marked verified;
7. record the exact validation/test commands executed and their result;
8. record blockers, unresolved decisions, assumptions that affect implementation, and the concrete next action;
9. keep the file concise and current rather than turning it into a verbose chat transcript; Git history is the long-term history;
10. never store credentials, tokens, private URLs, or other secrets in the status file.

If a work session ends with failing tests or partially implemented code, say so explicitly in `PROJECT_STATUS.md`. Do not leave the repository appearing complete when it is not.

### Required status vocabulary

Use these states consistently where applicable:

- `not started`
- `in progress`
- `blocked`
- `implemented, not verified`
- `verified`
- `done`

`done` means the milestone's Definition of Done has been met, including required verification.

## 10. Completion report

At the end of each milestone, update `PROJECT_STATUS.md` and report to the maintainer:

- files changed
- behavior implemented
- tests executed and result
- assumptions made
- unresolved questions
- exact commands needed for a maintainer to reproduce build/test/install

The conversational completion report is useful, but **the persistent update to `PROJECT_STATUS.md` is mandatory** so another agent can continue without access to the prior session context.
