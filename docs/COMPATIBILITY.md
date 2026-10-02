# Compatibility

Only combinations that were actually run are listed as verified. Anything else is not a claim of support.

| Component | Version | Status | Evidence |
|---|---|---|---|
| Checkmk | 2.5.x | verified | test site (Python 3.13): install, update, removal, rule form, notifications, password store, failure paths; see `PROJECT_STATUS.md` |
| Checkmk edition | Community (CE) | install verified | CLI path (`mkp add` / `enable` / `remove`) on a CE site, 2026-10-02; delivery on CE is still to be run |
| Checkmk edition | Enterprise | verified | GUI upload and enable, rule form, notifications on the test site |
| Checkmk | 2.4 and older | not supported | not tested, the extension uses the 2.5 Ruleset API v1 `NotificationParameters` discovery |
| Apprise | 2.0 | verified | real Apprise -> Signal: plain text and rich text arrive clean; converters cross-checked locally with Apprise 2.0.0 |
| Apprise | older than 2.0 | not supported | rich text needs the HTML to Markdown converter |
| Apprise API | the maintainer's instance, Apprise library 2.0.0 (API version not recorded) | verified | `locked` access with credentials and tag delivered end to end (Signal); endpoint `POST /notify/{key}` also checked against the API sources and documentation |
| Python on the Checkmk site | 3.13 (Checkmk 2.5) | verified | test site |
| Python for development/CI | 3.12 and 3.13 | verified | CI runs the unit tests on both |
| Operating system | the Checkmk host (Linux) | verified on the test site | the unit tests also run on Windows (developer machine) |
| Checkmk Exchange | - | not claimed | the package was not checked against the Exchange submission requirements |

## Targets

The plug-in is provider-agnostic. Delivery to Signal through Apprise was verified end to end; every other target depends on the Apprise configuration. Rich text on a target that renders formatting (bold labels) is still to be verified on a real target.
