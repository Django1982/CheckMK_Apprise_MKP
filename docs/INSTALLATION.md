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

Either in the GUI: **Setup > Maintenance > Extension packages > Upload package**, then enable it.

Or on the Checkmk server as the site user:

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
