# Security Policy

## Supported versions

No production release exists yet. Security support begins with the first published release.

## Reporting a vulnerability

Do not open a public issue containing credentials, exploit details or sensitive environment data.

Until a private security reporting channel is configured on the real GitHub repository, contact the repository maintainer privately through the channel published in that repository's profile/project metadata.

Once GitHub Private Vulnerability Reporting is enabled, this document should be updated to point contributors there.

## Sensitive data rules

Never include real:

- Apprise passwords/tokens
- Checkmk password-store values
- Basic/Bearer authorization headers
- provider URLs containing secrets
- production host inventories or private addresses unless intentionally sanitized

Use obvious fake values in fixtures.

## Security priorities

The project treats these as release blockers:

- credential leakage through logs/exceptions
- disabled TLS verification by default
- unbounded network waits
- command/shell injection
- unsafe URL construction
- arbitrary file access outside expected Checkmk site-local paths
