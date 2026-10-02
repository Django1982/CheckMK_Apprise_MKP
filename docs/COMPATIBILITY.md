# Compatibility

Only combinations that were actually run are listed as verified. Anything else is not a claim of support.

| Component | Version | Status | Evidence |
|---|---|---|---|
| Checkmk | 2.5.x | verified | test site (Python 3.13): install, update, removal, rule form, notifications, password store, failure paths; see `PROJECT_STATUS.md` |
| Checkmk edition | Community (CE, core `nagios`) | verified | release 1.0.0 downloaded from GitHub, checksum checked, installed with `mkp add` / `enable`, `cmk -R`, delivery to the real Apprise, 2026-10-02 |
| Checkmk edition | Enterprise (core `cmc`) | verified | release 1.0.0 downloaded from GitHub and installed via GUI upload; earlier builds: rule form, notifications, password store, failure paths |
| Checkmk | 2.6 and later | not supported | not tested; the package manifest says `version.usable_until = 2.5.99`. A later Checkmk version needs a tested release first |
| Checkmk | 2.4 and older | not supported | not tested, the extension uses the 2.5 Ruleset API v1 `NotificationParameters` discovery |
| Apprise | 2.0 | verified | real Apprise -> Signal: plain text and rich text arrive clean; converters cross-checked locally with Apprise 2.0.0 |
| Apprise | older than 2.0 | not supported | rich text needs the HTML to Markdown converter |
| Apprise API | the maintainer's instance, Apprise library 2.0.0 (API version not recorded) | verified | `locked` access with credentials and tag delivered end to end (Signal); endpoint `POST /notify/{key}` also checked against the API sources and documentation |
| Python on the Checkmk site | 3.13 (Checkmk 2.5) | verified | test site |
| Python for development/CI | 3.12 and 3.13 | verified | CI runs the unit tests on both |
| Operating system | the Checkmk host (Linux) | verified on the test site | the unit tests also run on Windows (developer machine) |
| Checkmk Exchange | - | not submitted | see the section below |

## Targets

The plug-in is provider-agnostic. Delivery to Signal through Apprise was verified end to end; every other target depends on the Apprise configuration. Rich text on a target that renders formatting (bold labels) is still to be verified on a real target.

## Checkmk Exchange

Not submitted and no compatibility is claimed. The Exchange documentation requires GPL v2, a security review by Checkmk, and says that packages which "read from or write to directories outside a site directory, or that use APIs not provided by Checkmk, will be rejected". Points a reviewer may look at:

- **Files outside the site:** none. The only optional file, the CA certificate, must lie inside the site directory (since 1.0.1, symbolic links resolved).
- **Password store:** stored passwords are resolved with `cmk.utils.password_store.extract`, the function Checkmk's own notification plug-ins use; its docstring says it is meant for third-party plug-ins and must not change behavior. It is not part of the documented plug-in API (`cmk.password_store.v1_unstable` is documented as work in progress). It is imported only when a stored password is configured; an explicit password in the rule needs no such call.
- **Network:** the only network access is the configured Apprise server.
