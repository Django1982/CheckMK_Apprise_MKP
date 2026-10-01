# M0.2 Smoke Test: Install into a clean Checkmk 2.5 site

Use a dedicated test site, never production. Status of this checklist: **not yet executed** (no Checkmk 2.5 site was available during implementation).

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

- [ ] `mkp add` / `mkp list` succeed; the notification script is executable (`ls -l`).
- [ ] Setup > Events > Notifications > Add rule: method **Apprise** is selectable.
- [ ] The parameter form renders without a traceback (check `~/var/log/web.log`).
- [ ] Defaults shown: format Markdown, TLS verification on, timeout 10 s.
- [ ] Invalid base URL / config ID is rejected by the form; valid values are saved and reloaded.
- [ ] Open question: confirm the manifest value `version.packaged` is accepted.
- [ ] Trigger a test notification (Setup > Notifications > test). The stub must print
      `Apprise notification not sent: delivery is not implemented ...` and exit with 2, without traceback.
- [ ] Record the exact `NOTIFY_PARAMETER_*` names/values received (including the boolean and integer
      representations); the results feed M2.
- [ ] `mkp remove apprise` deletes only the two files above.

Record results in `PROJECT_STATUS.md` (verification log).
