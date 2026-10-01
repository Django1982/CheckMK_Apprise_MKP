# Architecture

## Goal

Expose Apprise as a native Checkmk notification method while keeping the Checkmk extension independent of every downstream notification provider.

## Context

```text
┌────────────────────────────┐
│ Checkmk Notification Engine│
└──────────────┬─────────────┘
               │ NOTIFY_*
               ▼
┌────────────────────────────┐
│ apprise notification script│
│                            │
│ parse → normalize → render │
│       → HTTP client        │
└──────────────┬─────────────┘
               │ HTTPS JSON
               ▼
┌────────────────────────────┐
│ Apprise API                │
│ POST /notify/{config_id}   │
└──────────────┬─────────────┘
               │ tag routing
      ┌────────┼───────────┐
      ▼        ▼           ▼
    Mail     Gotify      Matrix / ...
```

## Architectural boundaries

### Checkmk adapter

Responsibilities:

- consume `NOTIFY_*` environment variables
- consume `NOTIFY_PARAMETER_*` configuration variables
- distinguish host/service notifications
- classify Checkmk event/state
- translate exit result to Checkmk's `0/1/2` notification semantics

Must not know about Discord, Telegram, Matrix, mail provider syntax, etc.

### Message builder

Responsibilities:

- normalize input
- create provider-neutral title/body
- map Checkmk state/event to Apprise `type`
- optionally add Checkmk URL/context when available and safe
- bound/clean content

Should be pure enough to unit test without network access.

### Apprise client

Responsibilities:

- safe URL construction
- JSON encoding
- optional authentication verified against Apprise API behavior
- TLS verification handling
- bounded timeout
- HTTP response classification
- sanitized diagnostics

Must not implement a durable retry queue.

## Dependency policy

The runtime notification path should rely on the Python standard library unless a strong, documented reason requires an additional dependency. The extension does **not** embed Apprise and does **not** require Apprise to be installed into Checkmk's Python environment.

The remote Apprise API service is an external operational dependency.

## Configuration model

Checkmk owns:

- Apprise API base URL
- Apprise saved configuration ID
- credentials/reference to Checkmk password store when needed
- routing tag expression
- message format
- TLS verify switch
- timeout

Apprise owns:

- actual notification provider URLs/secrets
- provider groups and tags
- provider-specific retries/options
- provider-specific formatting limitations

## Future extensibility

A local Apprise CLI transport may be considered later, but it must be introduced behind a clearly separated transport interface. It is intentionally outside v1 so the initial extension remains simple and deployable without modifying the Checkmk site's Python packages.
