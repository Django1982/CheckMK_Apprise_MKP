# Project Status

> Persistent, coding-agent-neutral implementation state. Update this file during meaningful work and **before every handoff or end of session**. Do not rely on chat history or vendor-specific agent memory as the project record.

## Current state

- **Active milestone:** none. Version 1.0.0 is released (tag `v1.0.0`, 2026-10-02); maintenance and backlog only
- **Overall status:** M0.1 to M5 done. Release published, `main` protected by an active branch ruleset (PR required, squash only, three required checks), `CODEOWNERS` set
- **Last verified milestone:** M5 – the downloaded 1.0.0 release asset was installed on a Community Edition and an Enterprise site and delivered to the real Apprise
- **Last updated:** 2026-10-02
- **Updated by:** Claude Code

## Milestone overview

| Milestone | Status | Verification |
|---|---|---|
| M0.1 – Project Preparation | done | repository baseline and sanity CI |
| M0.2 – Technical Skeleton | done | install/enable/uninstall, method selectable, form validation, save/reload on a Checkmk 2.5 site (Python 3.13) |
| M1 – Notification Core | done | manual Checkmk runs for host/service problem, recovery, UNKNOWN, downtime start/end/cancelled, flapping start, failure paths, Unicode, log inspection. Acknowledgement, custom, flapping stop and host UP are unit-tested only |
| M2 – Native Checkmk UX | done | `NOTIFY_PARAMETER_*` formats confirmed (bool `True`/`False`, int, empty tag omitted); explicit and password-store passwords sent as Basic auth; wrong password -> HTTP 401/exit 2; GUI hides the password; log shows only parameter names |
| M3 – Routing & Formatting | done | tag pass-through, type mapping, content bounds; message formats `text` (default) and `html` (rich text; Apprise converts per target, Markdown removed because Apprise cannot convert it to text targets). Real Apprise 2.0 -> Signal: plain text and rich text arrive clean |
| M4 – Hardening | done | classification matrix, TLS/proxy/redirect handling, total request deadline (covers DNS and slow-drip responses), value size limits, bounded response read, optional CA file, troubleshooting guide; mutation-checked tests |
| M5 – Release Readiness | done | v1.0.0 published by the release workflow (MKP + SHA-256, not a pre-release); the asset's checksum equals a local rebuild from the tag (Linux CI vs Windows); see "Release 1.0.0" |

## Current objective

None required. Optional backlog items below; no blocker.

## Release 1.0.0

Tag `v1.0.0` on 2026-10-02 (commit `19ba385`). Release assets `apprise-1.0.0.mkp` (SHA-256 `fe90228fbb551b0eb4b55891c0eb0d08440c9aae56ee2dcd05ad6c035f1e3511`) and `apprise-1.0.0.mkp.sha256`. Verified by the maintainer: checksum of the downloaded file, install on CE (CLI, core `nagios`) and EE (GUI), rule, delivery of a service problem, downtime cancelled/start/end with the correct titles and comments.

Repository settings (2026-10-02): `.github/CODEOWNERS` names the maintainer (PR #20); the branch ruleset `Default Rule` on `main` is active with the settings in `docs/GITHUB_GOVERNANCE.md` (PR #21 served as the test pull request: required checks listed, squash merge worked).

## Findings review (external review, 2026-10-01)

| Finding | Decision |
|---|---|
| HTTP 204 treated as success (P0) | Fixed: only 200 is delivered; every other 2xx is exit 2. Current Apprise API answers 404 for an empty configuration; older versions answered 204 |
| 424 ambiguous (P1) | Kept as exit 1, documented as a deliberate trade-off with a troubleshooting hint |
| TLS certificate failure retryable (P1) | Kept as exit 1 on purpose (an alert should not be lost while an admin fixes the certificate); the message says what to check. Maintainer decision, unchanged after the tests against a real HTTPS instance |
| Missing `NOTIFICATIONTYPE` defaulted to PROBLEM (P1) | Fixed: invalid event, exit 2 |
| Implicit environment proxies (P2) | Decided: ignored, documented, test proves it |
| TLS-disabled warning on `http://` (P2) | Fixed: only for `https://` |
| TLS/DNS tests (P2) | Classification tests per exception type; DNS test no longer uses the network; TLS tests use real certificates |
| `PROJECT_STATUS.md` stale (P3) | Fixed; kept current since |
| CI only Python 3.12 (P3) | CI runs the unit tests on 3.12 and 3.13 (single `unit-tests` job) |

## Message format finding (2026-10-02)

Real Apprise -> Signal showed raw Markdown. Cause (Apprise sources): the API passes `format` as the input format (`body_format`), and Apprise has no Markdown->Text converter, so text targets get the Markdown unchanged. Plain text input is converted correctly per target and became the default (PR #10). Because offering a rich option must also work on text targets, Markdown was replaced by HTML input, which Apprise converts cleanly to text, Markdown and HTML (PR #11).

## Open items

- Rich text on a target that renders formatting (Signal with `?format=markdown`, Matrix, Discord, mail): not run live. Checked only with Apprise 2.0.0's converters (HTML -> text equals the plain layout for all fixtures, HTML -> Markdown gives bold labels).
- Manual runs of acknowledgement, custom, flapping stop and host UP (unit-tested).
- Documented user guidance (already in the docs): select exactly one recipient per rule; repeated HTTP 424 means check routing tags and the Apprise configuration; hand-placed files under `~/local/` must belong to the site user.

## Blockers

None. Approved decision: stored passwords are resolved with `cmk.utils.password_store.extract` (not a documented public API; see `docs/TECHNICAL_SPEC.md`, "Credentials").

Lessons: notification script line 2 must be `# <title>` (Checkmk dropdown name); `MatchRegex` error messages must be `Message(...)`, not `str`; Checkmk flattens tuple parameters (`PASSWORD` -> `NOTIFY_PARAMETER_PASSWORD_1/_2/_3_1/_3_2`); `ssl.SSLError` is a subclass of `OSError` (catch it first); OpenSSL versions differ in what they accept (for example a BOM in a PEM file), so tests must not depend on it; a file copied as root under `~/local/` breaks `cmk -R`.

## Decisions that must be preserved

- Use public/supported Checkmk extension APIs where available (documented exception: password store lookup).
- Use `NotificationParameters` Ruleset API v1 with `name="apprise"`.
- Use Apprise API `POST /notify/{config_id}` as the v1 transport.
- Do not vendor Apprise or require a local Apprise CLI/Python installation.
- TLS verification defaults to enabled and requests require an explicit timeout.
- No custom retry queue in v1.
- Secrets must never be emitted to normal/debug output.
- Only HTTP 200 counts as delivered; redirects and environment proxies are not used.
- Plain text is the default message format; Markdown is not offered.
- Do not make an agent-specific instruction file the sole source of any critical rule.

## Verification log

Record only commands that were actually executed.

| Date | Command / check | Result | Notes |
|---|---|---|---|
| 2026-10-01 | manual M0.2 on Checkmk 2.5 site `dev` | passed | install, method selectable, form, validation, save/reload, remove; after fixes for the script title line and the `Message` validator crash |
| 2026-10-01 | manual M1 against `scripts/mock_apprise.py` via Checkmk | passed | events, failure paths (timeout/503/refused -> exit 1; 400 -> exit 2), Unicode, `notify.log` free of URL/config id/secret |
| 2026-10-01 | manual M2 via Checkmk against the mock with `--user/--password` | passed | explicit and password-store password, wrong password rejected, GUI secrecy |
| 2026-10-01 | mutation check of the proxy test | passed | test fails without `ProxyHandler({})` |
| 2026-10-02 | manual HTTPS notification through Checkmk to the maintainer's real Apprise API (internal service, Let's Encrypt certificate), package 0.3.1 | passed (reported by maintainer) | routing tag only; plain, unformatted message |
| 2026-10-02 | manual: package 0.4.0 on Signal | finding | Markdown arrived raw (see message format finding) |
| 2026-10-02 | manual: package 0.6.0, format Rich text, real Apprise 2.0 -> Signal | passed (reported by maintainer) | the plain layout, values verbatim, no markup characters |
| 2026-10-02 | manual: package 0.7.0: delivery with Basic auth (rich text), `--delay 15` with a shorter timeout | passed (reported by maintainer) | `temporarily failed: timeout`, Checkmk retries |
| 2026-10-02 | unit tests with real self-signed certificates (openssl) | passed | default verification rejects, `ca_file` trusts, other CA rejects, host name still checked, opt-out works; CI runs them on ubuntu |
| 2026-10-02 | manual: CE site CLI install; EE site GUI upload; `locked` access with user/password against the real Apprise (library 2.0.0) | passed (reported by maintainer) | install paths and locked mode verified |
| 2026-10-02 | manual: package 0.8.0/0.8.1 against `phpipam.k8.do-dat.int` (internal CA, `*.k8.do-dat.int`) | passed (reported by maintainer) | no CA file -> certificate verification failed (exit 1); CA file owned by root -> generic error in 0.8.0, `cannot be read by the site user` since 0.8.1; readable CA file -> TLS verified, server answered `HTTP 302` -> exit 2 |
| 2026-10-02 | manual: `scripts/notify_env_dump.py` on the test site for a host downtime start | passed (reported by maintainer) | no end-time variable; the comment already contains the author; a copy owned by root broke `cmk -R` (documented in `docs/INSTALLATION.md`); script and rule removed afterwards |
| 2026-10-02 | `python -m unittest discover -s tests/unit`, `python -m ruff check .` at v1.0.0 | passed (109 tests, 2 skipped without Apprise; with Apprise 2.0.0 in a local venv all run) | CI on Python 3.12 and 3.13 |
| 2026-10-02 | release workflow on tag `v1.0.0` | passed | published MKP + checksum; checksum equals a local rebuild from the tag |
| 2026-10-02 | manual: release 1.0.0 downloaded from GitHub, checksum checked, installed on CE (`mkp`, `cmk -R`) and EE (GUI), delivery to the real Apprise, downtime cancelled/start/end messages | passed (reported by maintainer) | |
| 2026-10-02 | clean virtual environment from `requirements-dev.txt` (ruff 0.16.9, apprise 2.0.0): `ruff check .`, all unit tests | passed (109 tests, none skipped) | the pinned set is what CI installs |
| 2026-10-02 | branch ruleset on `main` activated; test pull request #21 | passed | required checks `repository-sanity`, `dependency-review`, `unit-tests` listed for the PR, squash merge worked; active rules read back via the GitHub API |

## Backlog (optional, not required)

- Optional link back to Checkmk in the message: `NOTIFY_HOSTURL` is relative (`/check_mk/index.py?...`), so a field for the Checkmk base URL would be required.
- Downtime end time: closed, Checkmk passes no end time to notification scripts (a Livestatus query could add it; not planned). The expected duration can go into the downtime comment.
- Consider "require branches to be up to date" in the ruleset once pull requests run in parallel.
- Checkmk Exchange: not claimed; would need a check against its current submission requirements first.

## Handoff notes

A future agent may be Codex, Claude, Gemini, or another coding agent. Do not assume access to previous chat context, hidden reasoning, IDE state, or vendor-specific memory. The repository contents plus this status file must be sufficient to continue safely.
