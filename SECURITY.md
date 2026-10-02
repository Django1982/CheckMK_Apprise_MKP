# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| 1.0.x | yes (security fixes) |
| older | no |

## Reporting a vulnerability

Do not open a public issue containing credentials, exploit details or sensitive environment data.

Use GitHub's private vulnerability reporting for this repository (Security tab, "Report a vulnerability"). If it is not available, contact the maintainer privately through the contact options on the maintainer's GitHub profile. Do not post details in a public issue.

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
- arbitrary file access outside the Checkmk site directory (the optional CA file must lie inside the site; the plug-in reads no other files)
