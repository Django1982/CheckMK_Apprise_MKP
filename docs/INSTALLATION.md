# Installation, update and removal

## Requirements

- Checkmk 2.5.x (see [`COMPATIBILITY.md`](COMPATIBILITY.md))
- An Apprise API server (Apprise 2.0) reachable from the Checkmk host, with a saved configuration
- Nothing else: the notification script uses only the Python standard library of the Checkmk site; Apprise is **not** installed on the Checkmk server

## Get the package

Download `apprise-<version>.mkp` (and its `.sha256` file) from the GitHub release and verify it:

```bash
sha256sum -c apprise-<version>.mkp.sha256
```

Or build it from a checkout of the repository (needs only Python 3):

```bash
git checkout <tag or branch>
python3 scripts/build_mkp.py          # writes dist/apprise-<version>.mkp
```

The build is reproducible: the same sources always give the same bytes.

## Install

In the GUI (editions with the extension package page): **Setup > Maintenance > Extension packages > Upload package**, then enable it. The Community Edition has no upload page; use the command line there.

On the Checkmk server as the site user (all editions):

```bash
mkp add apprise-<version>.mkp
mkp enable apprise        # only if the package is not enabled automatically
mkp list
cmk -R                    # reload so the new notification method is picked up
```

Installed files:

```text
~/local/share/check_mk/notifications/apprise      (executable)
~/local/lib/python3/cmk_addons/plugins/apprise/rulesets/notification.py
```

Then create the notification rule, see [`CONFIGURATION.md`](CONFIGURATION.md).

## Files you place by hand

`mkp add` creates the package files with the right owner. Files you copy into `~/local/` yourself (for example a CA certificate for the rule, or a diagnostic script) must belong to the **site user** and be readable by it. A file copied as `root` breaks `cmk -R` with `Permission denied` for notification scripts and makes the plug-in report `CA_FILE cannot be read by the site user`. Copy as the site user (`omd su SITE`) or fix it:

```bash
chown SITE:SITE ~/local/share/check_mk/notifications/FILE
chmod 755 ~/local/share/check_mk/notifications/FILE     # scripts; certificates: 644
```

## Update

```bash
mkp remove apprise
mkp add apprise-<new version>.mkp
cmk -R
```

Existing rules keep their saved values. Check the changelog for renamed or removed options; for example the unreleased `markdown` message format was replaced by `html` ("Rich text"), and a rule that still holds the old value must be saved again with a supported format.

## Remove

```bash
mkp remove apprise
```

Only the two files above are removed. Notification rules that use the method stay in the configuration; delete them in the GUI.

## Check that it works

1. **Setup > Events > Notifications > Add rule**: the method **Apprise** is selectable and the parameter form loads without an error.
2. Use **Setup > Notifications > Test notifications** and check the result line and
   ```bash
   grep -i apprise ~/var/log/notify.log | tail
   ```
3. Problems: [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md).
