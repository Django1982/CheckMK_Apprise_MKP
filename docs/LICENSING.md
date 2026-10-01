# Licensing Decision

## Decision

The Checkmk Apprise extension repository uses:

```text
GPL-2.0-only
```

SPDX identifier:

```text
GPL-2.0-only
```

## Why not AGPLv3 for this MKP?

AGPLv3 was initially preferred for strong copyleft. However, current Checkmk developer documentation for MKP publication states that extensions use programming interfaces licensed under GPL v2 and are therefore also subject to GPL v2.

Separately, GPLv2-only and GPLv3-family licenses are not generally compatible for a combined work. AGPLv3 is based on GPLv3 terms with an additional network-interaction provision, so choosing AGPLv3 for code that forms a Checkmk extension creates avoidable license compatibility risk.

Therefore the conservative project decision is **GPL-2.0-only** for the Checkmk extension.

## What this does not prevent

A genuinely separate service/component that does not form part of the Checkmk MKP could have a different license after a separate legal/compatibility review. For example, a standalone service built independently around Apprise could potentially be AGPLv3 without changing this MKP's license.

## Source-code policy

Do not copy Checkmk implementation code into this repository merely for convenience. Use the documented extension API and independently implement the adapter.

If any third-party source is later incorporated, record:

- source/project
- exact file/component
- upstream license
- compatibility conclusion
- required notices

in this document before merging.

## Disclaimer

This document records the project's engineering/license compatibility decision; it is not legal advice.
