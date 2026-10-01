# Research Sources

Primary references used for the initial design. Re-check these before relying on details that may change with Checkmk/Apprise releases.

## Checkmk

### Notifications

- https://docs.checkmk.com/latest/en/notifications.html

Key design points:

- local notification scripts live below the site-local notification directory
- notification context is supplied through `NOTIFY_*` environment variables
- Checkmk owns notification execution/spooling behavior

### MKP development

- https://docs.checkmk.com/latest/en/devel_mkps.html

Key design points:

- local extension files are packaged as MKPs
- package versions use Semantic Versioning
- current Checkmk docs explicitly warn that Exchange extensions use GPLv2-licensed programming interfaces and are subject to GPLv2

### Ruleset API – NotificationParameters

- https://docs.checkmk.com/plugin-api/latest/cmk.rulesets/v1.rule_specs.html

Relevant API:

```text
cmk.rulesets.v1.rule_specs.NotificationParameters
```

### Form Specs

- https://docs.checkmk.com/plugin-api/latest/cmk.rulesets/v1.form_specs.html

Relevant for strings, booleans/selections and password/password-store-capable configuration.

### Password Store

- https://docs.checkmk.com/latest/en/password_store.html

### Checkmk source confirmations

Repository:

- https://github.com/Checkmk/checkmk

Relevant current-source areas verified during planning:

- `cmk/base/notify.py`
  - exit code semantics: 0 success, 1 retry later, 2 permanent/no retry
  - notification script environment prepends `NOTIFY_`
  - dict parameters are added with `PARAMETER` prefix; key `foo_bar` becomes `PARAMETER_FOO_BAR`, then `NOTIFY_PARAMETER_FOO_BAR`
- `.werks/17884.md`
  - Checkmk 2.5 uses Ruleset API `NotificationParameters` discovery for third-party notification parameters
  - legacy notification parameter registry registration is no longer supported for this extension pattern

## Apprise

### Apprise API project

- https://github.com/caronc/apprise-api
- https://github.com/caronc/apprise-api/blob/master/README.md
- https://github.com/caronc/apprise-api/blob/master/swagger.yaml

Relevant endpoint:

```text
POST /notify/{KEY}
```

Relevant payload fields in current documentation:

- `body`
- `title`
- `type`: `info`, `success`, `warning`, `failure`
- `tag`
- `format`: `text`, `markdown`, `html`

Current Apprise API documentation also describes access modes (`user`, `locked`, `public`, `disabled`) and notes that some modes require a specific tag and reject `all`. Verify exact auth behavior when implementing M2.

### Apprise project

- https://github.com/caronc/apprise
- https://appriseit.com/

Use Apprise tags for downstream routing. Do not mirror provider configuration into Checkmk.

## GitHub

### Rulesets / protected branch behavior

- https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets
- https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches

### Dependency review

- https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/reviewing-dependency-changes-in-a-pull-request

### Dependabot version updates

- https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/secure-your-dependencies/configure-version-updates

## GNU license compatibility reference

- https://www.gnu.org/licenses/gpl-faq.html.en

Relevant planning point: GPLv2-only cannot simply be combined/relicensed as GPLv3; this informs the decision not to use AGPLv3 for the Checkmk MKP.
