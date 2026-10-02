# Troubleshooting

## Where to look

The script prints one short line per notification; Checkmk shows it as the plug-in output and writes it to the site's notification log:

```bash
grep -i apprise ~/var/log/notify.log | tail -n 30
```

The line never contains the Apprise URL, the Config ID, credentials or the server's response. Increase Checkmk's notification log level if you need to see which rule and which contact triggered the call.

## Exit codes

| Exit | Meaning for Checkmk | What the plug-in does |
|---:|---|---|
| 0 | delivered | Apprise answered HTTP 200 |
| 1 | temporary failure | Checkmk retries later (spooler), the result is shown as WARN |
| 2 | permanent failure | Checkmk does not retry, the result is shown as CRIT |

## Messages and what to do

| Output | Exit | Cause | Action |
|---|---:|---|---|
| `delivered (HTTP 200)` | 0 | everything fine | none |
| `Apprise configuration invalid: missing BASE_URL, CONFIG_ID` | 2 | required rule fields empty | fill in the rule |
| `... BASE_URL must be an http(s) URL` / `must not contain credentials` / `... a query or fragment` | 2 | malformed base URL | use `https://apprise.example.net`, optionally with a path prefix |
| `... CONFIG_ID has an invalid format` | 2 | Config ID must be 1-64 of letters, digits, `_`, `-` | fix the ID |
| `... TIMEOUT must be between 1 and 120` / `... invalid boolean` | 2 | invalid value reached the script | re-save the rule in the GUI |
| `... USERNAME and PASSWORD must be set together` | 2 | only one of the two set | set both or neither |
| `... password could not be read from the password store` | 2 | stored password missing or not readable by the site | check that the entry still exists in the Checkmk password store and re-select it in the rule |
| `... TAG is too long or contains control characters` | 2 | tag longer than 200 characters or with control characters | shorten the tag |
| `Checkmk event invalid: ...` | 2 | the Checkmk event lacks `NOTIFY_WHAT`, host name, service description or notification type | unexpected context; send a test notification and compare. Bulk notifications are not supported |
| `temporarily failed: timeout` | 1 | Apprise or the network did not answer within the configured time (total deadline, includes DNS) | check connectivity and Apprise load, raise the timeout if the target is slow |
| `temporarily failed: DNS resolution failed` | 1 | host name cannot be resolved from the Checkmk host | fix DNS or use an address |
| `temporarily failed: connection error` | 1 | refused, reset or unreachable | is Apprise running, firewall, port |
| `temporarily failed: TLS error` | 1 | handshake problem | check TLS version/ciphers of the Apprise endpoint |
| `temporarily failed: TLS certificate verification failed (check CA, host name and expiry)` | 1 | certificate not trusted by the Checkmk host, wrong host name or expired | use a publicly trusted certificate, install your CA in the host's trust store, or fix the name/expiry. Disabling verification is possible but not recommended |
| `temporarily failed: HTTP 5xx` / `408` / `429` | 1 | Apprise or a proxy in front of it is failing, rate limiting | check the Apprise container logs |
| `temporarily failed: HTTP 424` | 1 | Apprise accepted the request but could not deliver. A provider outage is transient, but Apprise also uses 424 when the **tag matches no target** | if it repeats: check that the tag exists on the configuration and that the target URLs work (Apprise logs) |
| `permanently failed: HTTP 400 - check Config ID, routing tag ...` | 2 | invalid payload, or access mode `locked`/`public` without a specific tag (`all` is rejected) | set a routing tag that exists in the configuration |
| `permanently failed: HTTP 401/403 - check credentials ...` | 2 | wrong user/password, or the configuration denies this user | check the credentials and the Apprise access mode |
| `permanently failed: HTTP 404 - check Config ID ...` | 2 | no configuration with this ID | check the Config ID |
| `permanently failed: HTTP 2xx - nothing was sent` | 2 | success status other than 200 (older Apprise API versions answered 204 for a key without configuration) | check that the Config ID has a saved configuration |
| `permanently failed: HTTP 3xx - redirects are not followed` | 2 | the URL redirects (http to https, trailing path) | use the final URL of the Apprise API |
| `WARNING: TLS certificate verification is disabled` | - | the rule has "Verify TLS certificate" off | re-enable once the certificate is fixed |
| `WARNING: credentials are sent over unencrypted HTTP` | - | credentials configured with an `http://` URL | switch to `https://` |

## Common situations

- **The same message arrives several times.** The rule's recipient selection calls the script once per contact. Select exactly one recipient (a single specific user).
- **Formatting characters show up in the message.** Use the format "Plain text". "Rich text" is converted by Apprise per target; Markdown is deliberately not offered because Apprise cannot convert it to plain-text targets (Apprise 2.0 is the supported baseline).
- **Nothing happens and nothing is logged.** Check that the notification rule matches and that the method is "Apprise" (Setup > Notifications, test notification). Run `cmk -R` after installing or updating the package.
- **A very long plug-in output is cut.** The script limits values (identifiers 255, output 1500, long output 2000, comment 1000 characters). Targets with smaller limits are handled by Apprise itself (see the overflow option of the Apprise URL).
- **Behind a proxy.** Environment proxy variables are ignored on purpose; the Checkmk host must reach the Apprise server directly.

## Testing without a real Apprise

`scripts/mock_apprise.py` is a stand-in Apprise API for manual tests (Basic auth, forced HTTP status, delays, TLS). See its docstring. Use it only with test values.
