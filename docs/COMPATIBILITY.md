# Compatibility

Only combinations that were actually run are listed as verified. Anything else is not a claim of support.

| Component | Version | Status | Evidence |
|---|---|---|---|
| Checkmk | 2.5.x | verified | test site (Python 3.13): install, update, removal, rule form, notifications, password store, failure paths; see `PROJECT_STATUS.md` |
| Checkmk edition | Community (Raw) | pending | clean install on a fresh site is part of the 1.0.0 acceptance |
| Checkmk edition | other editions | not recorded | the work test site's edition is not documented; the plug-in uses only Ruleset API v1 and the notification mechanism, which do not depend on the edition |
| Checkmk | 2.4 and older | not supported | not tested, the extension uses the 2.5 Ruleset API v1 `NotificationParameters` discovery |
| Apprise | 2.0 | verified | real Apprise -> Signal: plain text and rich text arrive clean; converters cross-checked locally with Apprise 2.0.0 |
| Apprise | older than 2.0 | not supported | rich text needs the HTML to Markdown converter |
| Apprise API | version of the maintainer's instance | to be recorded | endpoint `POST /notify/{key}` and the `locked` mode with tag are verified against the API source and documentation; end-to-end with credentials and a real `locked` configuration is part of the 1.0.0 acceptance |
| Python on the Checkmk site | 3.13 (Checkmk 2.5) | verified | test site |
| Python for development/CI | 3.12 and 3.13 | verified | CI runs the unit tests on both |
| Operating system | the Checkmk host (Linux) | verified on the test site | the unit tests also run on Windows (developer machine) |
| Checkmk Exchange | - | not claimed | the package was not checked against the Exchange submission requirements |

## Targets

The plug-in is provider-agnostic. Delivery to Signal through Apprise was verified end to end; every other target depends on the Apprise configuration. Rich text on a target that renders formatting (bold labels) is still to be verified on a real target.
