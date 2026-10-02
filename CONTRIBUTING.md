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

## Local checks

```bash
python -m pip install -r requirements-dev.txt     # pinned ruff and apprise (use a virtual environment)
python -m ruff check .
python -m unittest discover -s tests/unit -v
python scripts/build_mkp.py
```

`requirements-dev.txt` is for development and CI only. The notification script has no runtime dependencies; Apprise is installed only so the tests can cross-check our messages against Apprise's own format converters (without it those tests are skipped). The versions are pinned and Dependabot proposes updates; a failing cross-check in such an update pull request is an early warning that Apprise's behavior changed. `openssl` is needed for the TLS tests (skipped without it).

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
