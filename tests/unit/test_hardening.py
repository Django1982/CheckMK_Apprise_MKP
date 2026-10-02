# SPDX-License-Identifier: GPL-2.0-only
"""M4 hardening tests: failure classification, proxy handling and malformed input."""

import json
import os
import socket
import ssl
import threading
import time
import unittest
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest import mock

from test_core import MockApprise, apprise, fixture, parameters, run_main


class TransportErrorClassificationTest(unittest.TestCase):
    """Each lower-level exception maps to a stable message and exit code."""

    def result(self, error: BaseException):
        return apprise._error_result(error)

    def test_certificate_verification_failure(self):
        error = urllib.error.URLError(ssl.SSLCertVerificationError(1, "bad certificate"))
        result = self.result(error)
        self.assertEqual(result.exit_code, apprise.EXIT_TEMPORARY)
        self.assertIn("certificate verification failed", result.message)

    def test_other_tls_errors(self):
        result = self.result(urllib.error.URLError(ssl.SSLError(1, "handshake failure")))
        self.assertEqual(result.exit_code, apprise.EXIT_TEMPORARY)
        self.assertTrue(result.message.endswith("TLS error"))

    def test_dns_failure(self):
        result = self.result(urllib.error.URLError(socket.gaierror(-2, "unknown")))
        self.assertEqual(result.exit_code, apprise.EXIT_TEMPORARY)
        self.assertIn("DNS", result.message)

    def test_timeouts(self):
        for error in (TimeoutError(), urllib.error.URLError(TimeoutError())):
            with self.subTest(type(error).__name__):
                result = self.result(error)
                self.assertEqual(result.exit_code, apprise.EXIT_TEMPORARY)
                self.assertTrue(result.message.endswith("timeout"))

    def test_refused_and_reset(self):
        for error in (
            urllib.error.URLError(ConnectionRefusedError()),
            ConnectionResetError(),
            BrokenPipeError(),
        ):
            with self.subTest(type(error).__name__):
                result = self.result(error)
                self.assertEqual(result.exit_code, apprise.EXIT_TEMPORARY)
                self.assertTrue(result.message.endswith("connection error"))

    def test_messages_never_contain_the_exception_text(self):
        secret = "https://user:topsecret@apprise.example/notify/key"
        result = self.result(urllib.error.URLError(OSError(secret)))
        self.assertNotIn("topsecret", result.message)
        self.assertNotIn("apprise.example", result.message)

    def test_unexpected_exception_is_temporary_and_silent(self):
        env = {**fixture("service_critical"), **parameters(base_url="http://apprise.invalid")}
        with mock.patch.object(
            apprise.urllib.request.OpenerDirector, "open", side_effect=RuntimeError("topsecret")
        ):
            code, out = run_main(env)
        self.assertEqual(code, 1)
        self.assertNotIn("topsecret", out)


class SuccessStatusTest(unittest.TestCase):
    def deliver(self, server: MockApprise):
        return run_main({**fixture("service_critical"), **parameters(base_url=server.url)})

    def test_204_means_nothing_was_sent(self):
        # Older Apprise API versions answered 204 for a key without a configuration.
        with MockApprise(204) as server:
            code, out = self.deliver(server)
        self.assertEqual(code, 2)
        self.assertIn("nothing was sent", out)
        self.assertNotIn("delivered", out)

    def test_other_2xx_is_not_treated_as_delivered(self):
        with MockApprise(202) as server:
            code, out = self.deliver(server)
        self.assertEqual(code, 2)
        self.assertNotIn("delivered", out)

    def test_200_is_delivered(self):
        with MockApprise(200) as server:
            self.assertEqual(self.deliver(server)[0], 0)


class ProxyTest(unittest.TestCase):
    def test_environment_proxies_are_ignored(self):
        proxy_env = {
            "http_proxy": "http://127.0.0.1:9",
            "HTTP_PROXY": "http://127.0.0.1:9",
            "https_proxy": "http://127.0.0.1:9",
            "HTTPS_PROXY": "http://127.0.0.1:9",
            "no_proxy": "",
            "NO_PROXY": "",
        }
        with MockApprise(200) as server, mock.patch.dict(os.environ, proxy_env):
            code, out = run_main({**fixture("service_critical"), **parameters(base_url=server.url)})
        self.assertEqual(code, 0, out)
        self.assertEqual(len(server.requests), 1)


class MalformedInputTest(unittest.TestCase):
    def test_missing_notification_type_is_permanent(self):
        env = fixture("service_critical")
        del env["NOTIFY_NOTIFICATIONTYPE"]
        code, out = run_main({**env, **parameters()})
        self.assertEqual(code, 2)
        self.assertIn("NOTIFICATIONTYPE", out)

    def test_malformed_password_parameters(self):
        base = {**fixture("service_critical"), **parameters(username="alice")}
        cases = {
            "unknown kind": {"NOTIFY_PARAMETER_PASSWORD_2": "weird"},
            "stored without id": {
                "NOTIFY_PARAMETER_PASSWORD_2": "stored_password",
                "NOTIFY_PARAMETER_PASSWORD_3_1": "",
            },
            "explicit but empty": {
                "NOTIFY_PARAMETER_PASSWORD_2": "explicit_password",
                "NOTIFY_PARAMETER_PASSWORD_3_2": "",
            },
        }
        for name, extra in cases.items():
            with self.subTest(name):
                code, out = run_main({**base, **extra})
                self.assertEqual(code, 2)
                self.assertIn("Apprise configuration invalid", out)


class RawServer:
    """Tiny HTTP server whose handler behaviour is supplied by the test."""

    def __init__(self, respond):
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                self.rfile.read(int(self.headers.get("Content-Length", 0)))
                respond(self)

            def log_message(self, *args):
                pass

        class Quiet(ThreadingHTTPServer):
            daemon_threads = True

            def handle_error(self, request, client_address):
                pass

        self.server = Quiet(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(
            target=self.server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True
        ).start()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.server.shutdown()
        self.server.server_close()


class DeadlineAndSizeTest(unittest.TestCase):
    def deliver(self, server_url: str, **params: str):
        env = {**fixture("service_critical"), **parameters(base_url=server_url, **params)}
        started = time.monotonic()
        code, out = run_main(env)
        return code, out, time.monotonic() - started

    def test_slow_drip_response_hits_the_total_deadline(self):
        # one byte every 0.4 s never trips the per-operation socket timeout of 1 s
        def drip(handler):
            handler.send_response(200)
            handler.send_header("Content-Length", "100")
            handler.end_headers()
            for _ in range(100):
                try:
                    handler.wfile.write(b"x")
                    handler.wfile.flush()
                except OSError:
                    return
                time.sleep(0.4)

        with RawServer(drip) as server:
            code, out, elapsed = self.deliver(server.url, timeout="1")
        self.assertEqual(code, 1)
        self.assertIn("timeout", out)
        self.assertLess(elapsed, 4)

    def test_hanging_dns_lookup_hits_the_total_deadline(self):
        def hang(*args, **kwargs):
            time.sleep(10)

        with mock.patch("socket.getaddrinfo", side_effect=hang):
            code, out, elapsed = self.deliver("http://apprise.invalid", timeout="1")
        self.assertEqual(code, 1)
        self.assertIn("timeout", out)
        self.assertLess(elapsed, 4)

    def test_huge_response_body_is_read_only_up_to_the_bound(self):
        def huge(handler):
            handler.send_response(200)
            handler.send_header("Content-Length", str(50 * 1024 * 1024))
            handler.end_headers()
            chunk = b"x" * 65536
            try:
                for _ in range(800):
                    handler.wfile.write(chunk)
            except OSError:
                pass

        with RawServer(huge) as server:
            code, out, elapsed = self.deliver(server.url)
        self.assertEqual(code, 0)
        self.assertIn("delivered (HTTP 200)", out)
        self.assertLess(elapsed, 5)

    def test_error_response_body_is_never_printed(self):
        def failing(handler):
            body = b"secret-token=abc123 https://user:pw@provider.example"
            handler.send_response(500)
            handler.send_header("Content-Length", str(len(body)))
            handler.end_headers()
            handler.wfile.write(body)

        with RawServer(failing) as server:
            code, out, _ = self.deliver(server.url)
        self.assertEqual(code, 1)
        for forbidden in ("secret-token", "abc123", "provider.example"):
            self.assertNotIn(forbidden, out)

    def test_worst_case_payload_stays_small(self):
        big = "x" * 100000
        env = {
            "NOTIFY_WHAT": "SERVICE",
            "NOTIFY_HOSTNAME": big,
            "NOTIFY_HOSTADDRESS": big,
            "NOTIFY_OMD_SITE": big,
            "NOTIFY_SERVICEDESC": big,
            "NOTIFY_SERVICESTATE": big,
            "NOTIFY_SERVICEOUTPUT": big,
            "NOTIFY_LONGSERVICEOUTPUT": big + "y",
            "NOTIFY_NOTIFICATIONTYPE": big,
            "NOTIFY_NOTIFICATIONAUTHOR": big,
            "NOTIFY_NOTIFICATIONCOMMENT": big,
        }
        event = apprise.parse_event(env)
        limits = {
            "host": apprise.MAX_ID_CHARS,
            "address": apprise.MAX_ID_CHARS,
            "site": apprise.MAX_ID_CHARS,
            "service": apprise.MAX_ID_CHARS,
            "state": apprise.MAX_ID_CHARS,
            "notification_type": apprise.MAX_ID_CHARS,
            "author": apprise.MAX_ID_CHARS,
            "output": apprise.MAX_OUTPUT_CHARS,
            "long_output": apprise.MAX_LONG_OUTPUT_CHARS,
            "comment": apprise.MAX_COMMENT_CHARS,
        }
        for field, limit in limits.items():
            with self.subTest(field):
                self.assertLessEqual(len(getattr(event, field)), limit)
        config = apprise.parse_config(parameters())
        for fmt in ("text", "html"):
            payload = apprise.build_payload(config, event)
            payload["body"] = apprise.build_body(event, fmt)
            with self.subTest(fmt):
                self.assertLess(len(json.dumps(payload)), 20000)

    def test_tag_limits(self):
        self.assertEqual(
            apprise.parse_config(parameters(tag="t" * apprise.MAX_TAG_CHARS)).tag,
            "t" * apprise.MAX_TAG_CHARS,
        )
        for bad in ("t" * (apprise.MAX_TAG_CHARS + 1), "ops\nnetwork", "ops\x00"):
            with self.subTest(repr(bad[:10])), self.assertRaises(apprise.ConfigError):
                apprise.parse_config(parameters(tag=bad))


if __name__ == "__main__":
    unittest.main()
