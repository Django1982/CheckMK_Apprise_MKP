# Changelog

All notable changes to this project will be documented here.

The project follows Semantic Versioning once release artifacts begin.

## [Unreleased]

### Added

- M0.1 project preparation skeleton
- initial architecture and technical specification
- GitHub governance baseline
- coding-agent assignment
- M0.2 technical skeleton: `apprise` notification stub, `NotificationParameters` form (Ruleset API v1), reproducible stdlib MKP builder (`scripts/build_mkp.py`), unit tests, lint/test CI workflow and install smoke-test checklist

### Changed

- licensing decision set to GPL-2.0-only after Checkmk extension compatibility review
- corrected Checkmk notification exit-code semantics: 1 is retryable, 2 is permanent
