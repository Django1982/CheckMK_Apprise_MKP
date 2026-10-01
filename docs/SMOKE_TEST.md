# M0.2 Smoke Test: Install into a clean Checkmk 2.5 site

Use a dedicated test site, never production. Status: executed manually on a Checkmk 2.5 test site (see `PROJECT_STATUS.md`); the parameter-dump item is deferred to M2.

## Build

```bash
python scripts/build_mkp.py          # writes dist/apprise-<version>.mkp
python -m unittest discover -s tests/unit
```

The build is reproducible: building twice yields identical bytes.

## Install (as the site user)

```bash
mkp add apprise-0.1.0.mkp
mkp enable apprise      # only if the package is not enabled automatically
mkp list
```

Expected installed files:

```text
~/local/share/check_mk/notifications/apprise          (mode 755)
~/local/lib/python3/cmk_addons/plugins/apprise/rulesets/notification.py
```

## Checklist

- [x] `mkp add` / `mkp list` succeed; the notification script is executable (`ls -l`).
- [x] Setup > Events > Notifications > Add rule (set exactly one recipient, e.g. a single specific user, otherwise the script runs once per contact): method **Apprise** is selectable.
- [x] The parameter form renders without a traceback (check `~/var/log/web.log`).
- [x] Defaults shown: format Markdown, TLS verification on, timeout 10 s.
- [x] Invalid base URL / config ID is rejected by the form; valid values are saved and reloaded.
- [x] Open question: confirm the manifest value `version.packaged` is accepted.
- [x] Trigger a test notification (Setup > Notifications > test; one problem and one recovery result are expected). The stub must print
      `Apprise notification not sent: delivery is not implemented ...` and exit with 2, without traceback.
- [ ] Record the exact `NOTIFY_PARAMETER_*` names/values received (including the boolean and integer
      representations); the results feed M2.
- [x] `mkp remove apprise` deletes only the two files above (the then-empty `notifications/` directory is removed too, which is expected).

Record results in `PROJECT_STATUS.md` (verification log).
