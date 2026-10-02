# Release checklist

Use this for every release, starting with `v1.0.0`. Release tags look like `v1.0.0` (Semantic Versioning).

## Before tagging

- [ ] `PROJECT_STATUS.md` is current and has no open blocker for the release
- [ ] All milestone acceptance criteria in `docs/DEVELOPMENT_PLAN.md` are met or consciously deferred (listed in the changelog)
- [ ] `CHANGELOG.md`: the `[Unreleased]` section is moved to the new version with the date
- [ ] `PACKAGE_VERSION` in `scripts/build_mkp.py` and the `User-Agent` version in the script match the release (the script's user agent shows only major.minor)
- [ ] CI is green on `main` (`repository-sanity`, `dependency-review`, `unit-tests`)
- [ ] `python -m ruff check .` and `python -m unittest discover -s tests/unit` pass locally; with Apprise installed in a scratch venv the two cross-check tests also pass
- [ ] No secrets in fixtures, docs or logs (`grep -rIn -i "password\|token\|secret" tests docs src` reviewed)
- [ ] Documentation matches the behavior: `README.md`, `docs/INSTALLATION.md`, `docs/CONFIGURATION.md`, `docs/TROUBLESHOOTING.md`, `docs/COMPATIBILITY.md`, `docs/TECHNICAL_SPEC.md`

## Acceptance on real systems

- [ ] Clean install of the MKP on a fresh Checkmk 2.5 site (record the edition), including GUI upload and `mkp` install
- [ ] Rule form loads, validation rejects bad values, values are saved and reloaded
- [ ] End-to-end delivery against the real Apprise API: `locked` access with credentials and tag, over HTTPS
- [ ] Problem, recovery, acknowledgement, downtime and custom notification delivered; one failure path (Apprise stopped) retried by Checkmk
- [ ] `notify.log` reviewed: no URL, Config ID, credentials or server response
- [ ] Update from the previous version and removal leave no stray files
- [ ] Compatibility matrix updated with exactly what was run

## Build and publish

- [ ] Tag the commit on `main`: `git tag -s vX.Y.Z` (or annotated) and push the tag
- [ ] The release workflow builds the MKP from the tagged source, attaches `apprise-X.Y.Z.mkp` and its SHA-256 checksum to the GitHub release
- [ ] Rebuild locally from the tag and compare the checksum (the build is reproducible)
- [ ] Release notes: supported Checkmk and Apprise versions, upgrade notes, known limitations
- [ ] Do **not** submit to the Checkmk Exchange without a separate decision and a check against its current submission requirements

## After the release

- [ ] Move remaining items to the backlog in `PROJECT_STATUS.md`
- [ ] Open the next `[Unreleased]` section in the changelog
