# SPDX-License-Identifier: GPL-2.0-only
"""M4 hardening tests: failure classification, proxy handling and malformed input."""

import os
import socket
import ssl
import unittest
import urllib.error
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


if __name__ == "__main__":
    unittest.main()
