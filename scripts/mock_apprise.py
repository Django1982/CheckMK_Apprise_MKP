#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Minimal fake Apprise API for manual integration tests (stdlib only, test use only).

Accepts ``POST /notify/<id>`` for the known ids, prints each received payload and
answers like the real API would (404 unknown id, 400 invalid payload). Flags let you
force failure modes without restarting Checkmk::

    python3 mock_apprise.py --port 8000                      # happy path
    python3 mock_apprise.py --port 8000 --status 503         # always answer 503
    python3 mock_apprise.py --port 8000 --user alice --password test  # require Basic auth
    python3 mock_apprise.py --port 8000 --delay 15           # trigger the client timeout
    python3 mock_apprise.py --port 8443 --tls-cert c.pem --tls-key k.pem

Do not expose this to untrusted networks and never use real secrets with it.
"""

import argparse
import base64
import json
import ssl
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TYPES = ("info", "success", "warning", "failure")
FORMATS = ("text", "markdown", "html", "", None)


def describe_auth(header: str) -> str:
    """Show received Basic credentials; fine here because this mock only sees test values."""
    if not header.startswith("Basic "):
        return "no Basic credentials"
    try:
        return "user:password = " + base64.b64decode(header[6:]).decode("utf-8", "replace")
    except ValueError:
        return "malformed credentials"


def make_handler(args: argparse.Namespace) -> type[BaseHTTPRequestHandler]:
    expected_auth = ""
    if args.user:
        expected_auth = (
            "Basic " + base64.b64encode(f"{args.user}:{args.password}".encode()).decode()
        )

    class Handler(BaseHTTPRequestHandler):
        def _reply(self, status: int, text: str = "") -> None:
            data = json.dumps({"mock": text or status}).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length)
            print(f"\n=== {time.strftime('%H:%M:%S')} POST {self.path}", flush=True)
            print("User-Agent:", self.headers.get("User-Agent"), flush=True)
            try:
                payload = json.loads(raw)
            except ValueError:
                print("invalid JSON", flush=True)
                return self._reply(400, "invalid json")
            for key in ("title", "type", "format", "tag"):
                print(f"{key}: {payload.get(key)!r}", flush=True)
            print("body:\n" + str(payload.get("body")), flush=True)

            time.sleep(args.delay)
            if args.user:
                got = self.headers.get("Authorization", "")
                ok = got == expected_auth
                print(
                    f"auth: {'OK' if ok else 'REJECTED'} (received {describe_auth(got)})",
                    flush=True,
                )
                if not ok:
                    return self._reply(401, "authentication required")
            if args.status:
                return self._reply(args.status, "forced status")
            prefix, _, key = self.path.partition("/notify/")
            if prefix or key not in args.known_ids:
                return self._reply(404, "unknown key")
            if not payload.get("body") or payload.get("type", "info") not in TYPES:
                return self._reply(400, "invalid payload")
            if payload.get("format") not in FORMATS:
                return self._reply(400, "invalid format")
            return self._reply(200, "ok")

        def log_message(self, *log_args) -> None:
            pass

    return Handler


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--known-ids", nargs="+", default=["checkmk"])
    parser.add_argument("--status", type=int, default=0, help="always answer this HTTP status")
    parser.add_argument("--delay", type=float, default=0, help="seconds before answering")
    parser.add_argument("--user", help="require HTTP Basic auth with this user")
    parser.add_argument("--password", default="", help="password for --user (test value only)")
    parser.add_argument("--tls-cert")
    parser.add_argument("--tls-key")
    args = parser.parse_args()

    class QuietServer(ThreadingHTTPServer):
        def handle_error(self, request, client_address):
            pass  # clients that hit their timeout abort the connection on purpose

    server = QuietServer((args.host, args.port), make_handler(args))
    scheme = "http"
    if args.tls_cert:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(args.tls_cert, args.tls_key)
        server.socket = context.wrap_socket(server.socket, server_side=True)
        scheme = "https"
    print(
        f"Mock Apprise API on {scheme}://{args.host}:{args.port} (ids: {args.known_ids})",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
