# GitHub Governance

## Repository defaults

Recommended defaults:

- default branch: `main`
- squash merge: enabled and preferred
- merge commits: disabled unless a later workflow requires them
- rebase merge: optional; keep history policy consistent
- automatically delete head branches after merge: enabled
- issues: enabled
- discussions: optional
- wiki: disabled unless actually used

## Branch naming

Use short-lived branches:

```text
feat/<topic>
fix/<topic>
docs/<topic>
test/<topic>
chore/<topic>
release/<version>
```

Direct feature work on `main` is discouraged.

## Commit/PR conventions

Use concise Conventional-Commit-style subjects where practical:

```text
feat: add Apprise payload builder
fix: classify HTTP 503 as retryable
docs: document locked Apprise tag requirement
test: cover password redaction
chore: update CI action
```

A pull request should contain one coherent change. Squash title should be suitable as the resulting commit subject.

## `main` Ruleset

Create a GitHub branch Ruleset targeting the default branch.

Recommended enforcement:

- **Require a pull request before merging:** ON
- **Required approvals:** 1 if a second human maintainer/reviewer exists; otherwise 0 initially rather than creating fake approval theater
- **Dismiss stale approvals when new commits are pushed:** ON when approvals are required
- **Require review from Code Owners:** only after `CODEOWNERS` contains real accounts
- **Require status checks:** ON
- **Require branches to be up to date:** ON after baseline CI is stable
- **Require conversation resolution:** ON
- **Block force pushes:** ON
- **Block branch deletion:** ON
- **Require linear history:** ON if squash/rebase-only policy is selected
- **Require signed commits:** optional; enable only if all maintainers/bots can comply without blocking automation
- **Bypass:** keep minimal; repository admins only for emergency recovery if desired

Baseline required checks once workflows have run at least once:

```text
repository-sanity
dependency-review
```

Add later implementation checks such as:

```text
lint
unit-tests
package-sanity
```

GitHub requires status check names to be unambiguous, so job/check names should remain unique across workflows.

## CODEOWNERS

`.github/CODEOWNERS` intentionally contains no invented owner. Before enabling required Code Owner review, replace its TODO with real GitHub usernames or a real organization team.

Example only:

```text
* @real-maintainer
/.github/ @real-maintainer
/src/ @real-maintainer
```

Do not commit placeholder account names that could accidentally resolve to unrelated GitHub users.

## Dependabot

Track GitHub Actions weekly through `.github/dependabot.yml`.

When Python development/runtime dependency manifests are introduced, add the appropriate `pip` ecosystem entry. Runtime dependency count should remain minimal.

## Dependency review

The repository contains a dependency-review workflow suitable for public GitHub repositories. If the actual repository is private, confirm that the account/organization plan enables the required dependency review capability before making the check mandatory.

## Security

- enable secret scanning where available
- enable push protection where available
- enable Dependabot alerts
- enable dependency graph
- consider CodeQL once meaningful Python implementation exists
- never store real Apprise credentials in Actions secrets unless a deliberately isolated integration test requires them

Baseline CI must not need secrets.

## Releases

Release tags:

```text
v0.1.0
v1.0.0
```

Release process eventually should:

1. pass required checks
2. update changelog
3. build MKP from the tagged source
4. record package checksum
5. attach artifact to GitHub release
6. document supported Checkmk versions

Do not publish an artifact automatically to the Checkmk Exchange without a separate explicit release/publishing step.
