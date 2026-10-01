# Scripts

- `build_mkp.py` – reproducible, stdlib-only MKP builder: `python scripts/build_mkp.py [--output-dir dist]`. Sets mode 0755 on the notification script regardless of the checkout's file mode.

Helpers must not assume a production Checkmk site path unless explicitly invoked for integration testing.
