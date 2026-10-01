# Contributing

Thanks for contributing to Checkmk Apprise.

## Before coding

Read:

- `CODINGAGENT_TASK.md`
- `PROJECT_STATUS.md`
- `AGENTS.md` (supplemental; not universal across coding agents)
- `docs/TECHNICAL_SPEC.md`
- `docs/DEVELOPMENT_PLAN.md`

## Workflow

1. Create a short-lived branch from `main`.
2. Make one coherent change.
3. Add/update tests.
4. Update docs for behavior/configuration changes.
5. Run local checks.
6. Open a pull request using the repository template.

Suggested branch prefixes:

```text
feat/ fix/ docs/ test/ chore/
```

## License

Contributions are accepted under the repository's **GPL-2.0-only** license.

New source files should include an SPDX header where practical:

```text
SPDX-License-Identifier: GPL-2.0-only
```

Do not submit code copied from incompatible sources.

## Design rules

- provider routing belongs to Apprise
- Checkmk adapter stays small
- no bundled Apprise runtime
- secrets must never be logged
- no new runtime dependency without a documented reason
- new network behavior requires timeout/error tests

## Pull requests

A PR should explain:

- what changed
- why
- test coverage
- security/compatibility impact
- Checkmk versions tested, if applicable

Avoid mixing refactors and behavior changes unless necessary.
