# Configuration

The Checkmk side only needs to know where the Apprise API is, which saved configuration to use and (optionally) which tag to route by. Which provider receives the message (Signal, Matrix, mail, ...) is configured in Apprise, not in Checkmk.

## 1. Prepare Apprise

1. In the Apprise API create a **saved configuration** with a key, for example `checkmk`, containing your target URLs and tags (see the Apprise documentation for the syntax). Tags are what the Checkmk rule uses for routing.
2. Choose how the configuration is protected. The plug-in speaks HTTP Basic authentication:

| Apprise access mode | Credentials in the rule | Routing tag in the rule |
|---|---|---|
| `user` | required | optional |
| `locked` | required | **required**, a specific tag, `all` is rejected |
| `public` | none | **required**, a specific tag, `all` is rejected |
| `disabled` | not usable | not usable (administrator only) |

Example from the Apprise API documentation for creating a `locked` configuration with an administrator account (placeholders, use your own values):

```bash
curl -X POST -H "Content-Type: application/json" -u ADMIN:ADMIN_PASSWORD \
  -d '{"access": "locked", "username": "checkmk", "password": "CHANGE_ME"}' \
  https://apprise.example.net/auth/checkmk
```

A missing or unknown tag in `locked` or `public` mode shows up as `HTTP 400` in Checkmk.

## 2. Create the Checkmk rule

**Setup > Events > Notifications > Add rule**, notification method **Apprise**.

| Field | Meaning | Script variable |
|---|---|---|
| Apprise API base URL | `https://apprise.example.net` (optionally with a path prefix); no `/notify/...`, no credentials | `NOTIFY_PARAMETER_BASE_URL` |
| Apprise configuration ID | key of the saved configuration, 1-64 of letters, digits, `_`, `-` | `NOTIFY_PARAMETER_CONFIG_ID` |
| Routing tag expression | optional; passed to Apprise unchanged, omitted when empty (max 200 characters) | `NOTIFY_PARAMETER_TAG` |
| Apprise username / password | optional HTTP Basic credentials, set both or neither; prefer a password from the Checkmk password store | `NOTIFY_PARAMETER_USERNAME`, `NOTIFY_PARAMETER_PASSWORD_*` |
| Message format | **Plain text** (default) or **Rich text** | `NOTIFY_PARAMETER_MESSAGE_FORMAT` |
| Verify TLS certificate | on by default; disable only in controlled environments | `NOTIFY_PARAMETER_VERIFY_TLS` |
| CA certificate file (PEM) | optional; for a private CA or a self-signed certificate, see below | `NOTIFY_PARAMETER_CA_FILE` |
| Request timeout | total time for one request, 1-120 s (default 10) | `NOTIFY_PARAMETER_TIMEOUT` |

### Private CA or self-signed certificate

Publicly trusted certificates (for example Let's Encrypt) need nothing. For a private CA or a self-signed certificate, keep verification **on** and point the rule to the certificate instead:

1. Get the CA certificate (or, for a self-signed server, the server certificate) as a PEM file, for example:
   ```bash
   openssl s_client -connect apprise.example.net:443 -servername apprise.example.net </dev/null 2>/dev/null | openssl x509 > ~/etc/apprise-ca.pem
   ```
   For a private CA, use the CA's own certificate file instead of the server certificate.
2. Make sure the site user can read it and enter the path in **CA certificate file (PEM)**, for example `~/etc/apprise-ca.pem` (`~` is the site's home directory).

When set, **only** that file is trusted, not the system certificates. The host name is still checked: the certificate must contain the name or IP address used in the base URL as subject alternative name. Renew the file when the certificate is replaced. An unreadable or invalid file is a configuration error (exit 2).

### Recipient

Checkmk calls the script **once per contact**. Apprise does the fan-out, so select **exactly one recipient** (for example one specific user); with "all contacts of the affected object" every contact would trigger the same message again.

### Message format

- **Plain text** works on every target: Apprise converts it to what each target needs.
- **Rich text** sends the same content with bold labels. Apprise turns it into bold labels on targets that support formatting and into exactly the plain text layout on targets that do not (for example Signal). Apprise 2.0 is the supported baseline.
- Markdown is intentionally not offered: Apprise cannot convert Markdown to plain-text targets, so it would show raw `**`.

## 3. Tag examples

The tag expression is handled by Apprise; see its documentation for the full syntax. Typical uses:

| Goal | Tag in the rule |
|---|---|
| everything to the operations targets | `ops` |
| critical network alerts | one rule with tag `network`; use Checkmk rule conditions (host/service groups, states) to select what reaches it |
| targets tagged with `ops` **or** `network` | `ops, network` (comma = OR) |
| targets tagged with both `ops` **and** `night` | `ops night` (space or `+` = AND) |
| combinations | `ops night, oncall` = (`ops` AND `night`) OR `oncall` |

The usual pattern: several Checkmk rules, each with its own conditions and tag, all using the same Apprise configuration ID.

## 4. What the message looks like

```text
CRITICAL: dc01.example.net - CPU utilization     <- title

Service: CPU utilization
State: CRITICAL
Output: CPU utilization: 97.8%

Host: dc01.example.net
Address: 10.10.20.11
Site: prod
Notification: PROBLEM
```

Notes from real Checkmk 2.5 events: downtime comments already start with `Author (name): ...`, so the author is not appended again; Checkmk does not pass the end of a downtime to notification scripts, so put the expected duration in the downtime comment if you want it in the message.

Recoveries are titled `RECOVERY: ... (OK)`, other events `ACKNOWLEDGEMENT`, `DOWNTIME START`, `DOWNTIME END`, `DOWNTIME CANCELLED`, `FLAPPING START/STOP/DISABLED`, `CUSTOM`. The Apprise message type follows the event: recovery `success`, WARN and UNKNOWN `warning`, CRIT and DOWN `failure`, acknowledgement/downtime/custom `info`, downtime cancelled and flapping start `warning`.

## 5. Failures and retries

| Result | Exit | Checkmk behavior |
|---|---:|---|
| Apprise answered 200 | 0 | delivered |
| timeout, DNS or connection error, TLS error, HTTP 408/424/429/5xx | 1 | Checkmk retries later |
| wrong credentials/tag/config ID, other 4xx, redirects, invalid rule | 2 | not retried; fix the configuration |

The plug-in has no retry queue of its own. Details and remedies: [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md); the exact matrix: [`TECHNICAL_SPEC.md`](TECHNICAL_SPEC.md).

## 6. Security notes

- The script never prints the Apprise URL, Config ID, credentials or Apprise's response.
- Credentials over plain `http://` are allowed but print a warning; use `https://`.
- Prefer a CA file over switching verification off.
- The request goes directly to the Apprise server; proxy environment variables are ignored.
- Stored passwords are resolved with Checkmk's own password-store function at run time.
