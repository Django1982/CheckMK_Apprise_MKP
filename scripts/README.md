# Scripts

- `build_mkp.py` – reproducible, stdlib-only MKP builder: `python scripts/build_mkp.py [--output-dir dist]`. Sets mode 0755 on the notification script regardless of the checkout's file mode.

Helpers must not assume a production Checkmk site path unless explicitly invoked for integration testing.
- `mock_apprise.py` – stand-in Apprise API for manual tests (Basic auth, forced HTTP status, delay, TLS); see its docstring.
- `notify_env_dump.py` – diagnostic Checkmk notification script that prints the `NOTIFY_*` variables of an event (never the rule parameters); see its docstring. Used to find out which variables an event provides, for example the end of a downtime.
