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
| Credentials | conditional | none | Exact UI depends on verified Apprise API access mode/auth behavior |
| Routing tag | no | unset | Pass-through Apprise tag expression |
| Message format | yes | `markdown` | `text`, `markdown`, optionally `html` |
| Verify TLS | yes | `true` | Secure default |
| Timeout seconds | yes | `10` proposed | Bound and validate range |

Secrets must use a Checkmk password-store capable field/API where applicable.

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

The exact HTTP classification matrix is finalized in M4. Avoid treating every non-2xx response identically.

Implemented in M1 (provisional until M4; `classify_status` in the script):

| Outcome | Exit | Reason |
|---|---:|---|
| 2xx | 0 | accepted |
| 408, 429, 5xx | 1 | transient / rate limit / server side |
| 424 | 1 | Apprise accepted the request but a downstream provider failed; may be transient |
| timeout, DNS failure, connection error, TLS error | 1 | do not lose the alert; the problem is usually fixable outside the notification |
| other 3xx | 2 | redirects are deliberately not followed |
| 400, 401, 403, 404, 406, 409, 431 and other 4xx | 2 | request/configuration problem, retrying cannot help |
| invalid local configuration or Checkmk event | 2 | nothing to retry |

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
