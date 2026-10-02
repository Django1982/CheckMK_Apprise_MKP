# Technical Specification

## Target

Primary target: **Checkmk 2.5.x**.

The first release uses an external **Apprise API** server through a saved configuration endpoint. Checkmk 2.4 compatibility is not a v1 requirement unless explicitly added after implementation testing.

## Checkmk extension points

### Notification script

Target site-local path:

```text
~/local/share/check_mk/notifications/apprise
```

Repository mirror:

```text
src/local/share/check_mk/notifications/apprise
```

The final file must be executable.

### Ruleset / notification parameters

Target site-local path:

```text
~/local/lib/python3/cmk_addons/plugins/apprise/rulesets/notification.py
```

Repository mirror:

```text
src/local/lib/python3/cmk_addons/plugins/apprise/rulesets/notification.py
```

Use Checkmk Ruleset API v1 `NotificationParameters`. The variable should follow Checkmk's discovery convention (`rule_spec_...`) and:

```python
name = "apprise"
```

must match the notification script name.

Do not use the legacy `notification_parameter_registry.register(...)` extension method for Checkmk 2.5.

## Parameter transfer contract

For named dictionary parameters, Checkmk builds a `PARAMETER_*` event context and then exports the notification context with `NOTIFY_` prefixes.

Example:

```text
configuration key: foo_bar
runtime env:       NOTIFY_PARAMETER_FOO_BAR
```

The implementation must test its exact keys rather than depending on undocumented casing assumptions.

## Initial configuration fields

Field names below are conceptual. The implementation may choose concise stable keys but must document the resulting `NOTIFY_PARAMETER_*` names.

| Field | Required | Default | Notes |
|---|---:|---|---|
| API base URL | yes | none | `https://apprise.example.net` style base, no `/notify/...` entered by user |
| Config ID | yes | none | Saved Apprise configuration key/id |
| Username | conditional | none | HTTP Basic user (`NOTIFY_PARAMETER_USERNAME`); must be set together with the password |
| Password | conditional | none | Checkmk `Password` form spec (explicit or password store); see "Credentials" below |
| Routing tag | no | unset | Pass-through Apprise tag expression |
| Message format | yes | `markdown` | `text`, `markdown`, optionally `html` |
| Verify TLS | yes | `true` | Secure default |
| Timeout seconds | yes | `10` proposed | Bound and validate range |

Secrets must use a Checkmk password-store capable field/API where applicable.

## Credentials (M2)

Apprise API authentication is HTTP Basic (`Authorization: Basic ...`) on every request. Access modes per configuration (verified against the Apprise API README):

| Mode | Credentials | Tag |
|---|---|---|
| `user` | required | optional |
| `locked` | required | specific tag, `all` rejected |
| `public` | none | specific tag, `all` rejected |
| `disabled` | admin only | n/a |

Leave username/password unset for `public`. `locked` and `public` need a routing tag; a missing tag shows up as HTTP 400 (exit 2).

A `Password` form spec is flattened by Checkmk into `NOTIFY_PARAMETER_PASSWORD_1` (`cmk_postprocessed`), `_2` (`explicit_password` or `stored_password`), `_3_1` (id) and `_3_2` (value, empty for stored). An explicit password is read from `_3_2`. A stored password is resolved with `cmk.utils.password_store.extract(id)`, imported lazily and only for stored passwords.

**Decision (approved by the maintainer on 2026-10-01, on a test instance):** `cmk.utils.password_store` is not a documented public extension API. It is what Checkmk's bundled notification plugins use, and its docstring says it is intended for third-party plugins and must not change behavior. No public alternative for resolving the store in a notification script was found. If it is unavailable, the script exits 2 with a generic message. Credentials over plain `http://` are allowed but print a visible warning.

## Apprise endpoint

Stateful configuration endpoint:

```http
POST {base_url}/notify/{config_id}
Content-Type: application/json
```

Baseline payload:

```json
{
  "title": "CRITICAL: host.example - CPU utilization",
  "body": "...",
  "type": "failure",
  "format": "markdown",
  "tag": "critical"
}
```

Rules:

- `body` is required.
- Omit `tag` if no tag is configured.
- `type` must be one of `info`, `success`, `warning`, `failure`.
- use only formats supported by the current Apprise API version.
- validate/escape `config_id` when constructing the request URL.

Current Apprise API behavior includes access modes where non-admin/public/locked notification calls may require a specific tag and reject `all`. Implementation docs must call this out if it affects the supported authentication mode.

## Checkmk exit semantics

These semantics are normative:

| Exit | Meaning | Example |
|---:|---|---|
| 0 | Notification successfully sent/accepted | Apprise request completed successfully |
| 1 | Could not send now; retry later | timeout, temporary DNS/network issue, retryable server response |
| 2 | Cannot send; retry does not make sense | malformed local configuration, invalid permanent request/auth failure |

Avoid treating every non-2xx response identically; the matrix below is the contract.

Implemented classification (`classify_status` / `_error_result` in the script):

| Outcome | Exit | Reason |
|---|---:|---|
| 200 | 0 | Apprise answers 200 once the notification is delivered |
| any other 2xx (incl. 204) | 2 | not a delivery confirmation; older Apprise API versions answered 204 for a key without (or with an empty) configuration, i.e. nothing was sent |
| 408, 429, 5xx | 1 | transient / rate limit / server side |
| 424 | 1 | Apprise could not deliver. Deliberate trade-off: Apprise uses 424 both for provider outages (transient) and for a tag that matches no target (permanent); retrying is preferred over losing an alert. Repeated 424 means: check routing tags and the Apprise configuration |
| timeout, DNS failure, connection refused/reset, TLS handshake error | 1 | usually fixable outside the notification |
| TLS certificate verification failure | 1 | deliberate trade-off: an administrator can fix the CA/host name/expiry within Checkmk's retry window; the message says what to check. Revisit if users prefer exit 2 |
| 3xx | 2 | redirects are deliberately not followed |
| 400, 401, 403, 404, 406, 409, 413, 431 and other 4xx | 2 | request/configuration problem, retrying cannot help |
| invalid local configuration, invalid Checkmk event (including a missing `NOTIFY_NOTIFICATIONTYPE`), unreadable password | 2 | nothing to retry |

Environment proxy variables (`http_proxy`, ...) are deliberately ignored; the request goes directly to the configured Apprise server. Response bodies are read (at most 4 KiB) but never logged.

## Proposed state/event → Apprise type mapping

| Condition | Type |
|---|---|
| recovery / host UP / service OK | `success` |
| WARN | `warning` |
| CRIT / host DOWN | `failure` |
| UNKNOWN | `warning` |
| acknowledgement | `info` |
| downtime start/end | `info` |
| downtime cancelled | `warning` |
| flapping start | `warning` |
| flapping stop | choose `success` or `info`, document and test |
| custom | `info` |

Notification event type must be considered in addition to current state so recovery/administrative events are represented correctly.

## Message format

Supported formats are `markdown` (default) and `text`; `html` is not supported because it would need its own escaping.

In `markdown` mode every monitoring value (host, service, output, comment, ...) is escaped (`\ ` * _ [ ] < > ~ | #`, plus list markers at line start), labels are bold and each line ends with two spaces so Markdown keeps the line breaks. Titles are plain text and never escaped. `text` mode uses the layout below unchanged.

### Service notification baseline

```text
CRITICAL: dc01.example.net - CPU utilization

Service: CPU utilization
State: CRITICAL
Output: CPU utilization: 97.8%

Host: dc01.example.net
Address: 10.10.20.11
Site: prod
Notification: PROBLEM
```

Only include fields that exist. Do not fabricate placeholders such as `unknown` unless they add value.

### Host notification baseline

```text
DOWN: router01.example.net

State: DOWN
Output: Packet loss: 100%

Host: router01.example.net
Address: 10.10.1.1
Site: prod
Notification: PROBLEM
```

Recovery messages should be clearly recognizable as recovery/success without relying on a downstream provider's color/icon support.

## Networking

Preferred v1 characteristics:

- Python standard library client
- JSON request body
- TLS certificate verification on by default
- explicit timeout
- bounded diagnostic response read
- no shelling out to `curl`
- no global monkey-patching of SSL behavior

## Logging

The notification script's stdout is consumed/logged by Checkmk. Keep messages short and operationally useful.

Safe examples:

```text
Apprise notification delivered (HTTP 200)
Apprise notification temporarily failed: HTTP 503
Apprise configuration invalid: missing Config ID
```

Unsafe examples:

```text
POST https://user:password@apprise.example/notify/checkmk
Authorization: Basic ...
Password store value: ...
```

## Packaging

Use Checkmk's MKP tooling and SemVer. Package only site-local extension files required for the plugin and documentation if appropriate.

The agent must validate package metadata and file permissions on a real Checkmk 2.5 site before declaring M0.2 complete.
