# SPDX-License-Identifier: GPL-2.0-only
"""TLS tests with real certificates: default verification, private CA file, opt-out."""

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from test_core import MockApprise, apprise, fixture, parameters, run_main

OPENSSL = shutil.which("openssl")


def make_certificate(directory: Path, name: str, common_name: str = "127.0.0.1") -> tuple[str, str]:
    """Create a self-signed certificate valid for 127.0.0.1 (test data only)."""
    cert, key = directory / f"{name}.pem", directory / f"{name}.key"
    subprocess.run(  # noqa: S603
        [
            OPENSSL,
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-keyout",
            str(key),
            "-out",
            str(cert),
            "-days",
            "2",
            "-subj",
            f"/CN={common_name}",
            "-addext",
            "subjectAltName=IP:127.0.0.1",
        ],
        check=True,
        capture_output=True,
        timeout=60,
    )
    return str(cert), str(key)


@unittest.skipIf(OPENSSL is None, "openssl is not available")
class SelfSignedTlsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.dir = Path(cls._tmp.name)
        cls.cert, cls.key = make_certificate(cls.dir, "server")
        cls.other_cert, _ = make_certificate(cls.dir, "other")

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def deliver(self, server: MockApprise, **params: str):
        env = {**fixture("service_critical"), **parameters(base_url=server.url, **params)}
        return run_main(env)

    def test_default_verification_rejects_a_self_signed_certificate(self):
        with MockApprise(200, tls=(self.cert, self.key)) as server:
            code, out = self.deliver(server)
        self.assertEqual(code, 1)
        self.assertIn("certificate verification failed", out)
        self.assertEqual(server.requests, [])

    def test_ca_file_makes_the_self_signed_certificate_trusted(self):
        with MockApprise(200, tls=(self.cert, self.key)) as server:
            code, out = self.deliver(server, ca_file=self.cert)
        self.assertEqual(code, 0, out)
        self.assertIn("delivered (HTTP 200)", out)
        self.assertEqual(len(server.requests), 1)

    def test_a_different_ca_file_does_not_trust_the_server(self):
        with MockApprise(200, tls=(self.cert, self.key)) as server:
            code, out = self.deliver(server, ca_file=self.other_cert)
        self.assertEqual(code, 1)
        self.assertIn("certificate verification failed", out)

    def test_ca_file_keeps_the_host_name_check(self):
        # the certificate is only valid for 127.0.0.1, so "localhost" must be rejected
        with MockApprise(200, tls=(self.cert, self.key)) as server:
            url = server.url.replace("127.0.0.1", "localhost")
            code, out = run_main(
                {
                    **fixture("service_critical"),
                    **parameters(base_url=url, ca_file=self.cert),
                }
            )
        self.assertEqual(code, 1)
        self.assertIn("certificate verification failed", out)

    def test_verification_can_still_be_disabled_explicitly(self):
        with MockApprise(200, tls=(self.cert, self.key)) as server:
            code, out = self.deliver(server, verify_tls="false")
        self.assertEqual(code, 0, out)
        self.assertIn("WARNING: TLS certificate verification is disabled", out)

    def test_tilde_in_the_path_is_expanded(self):
        with mock_home(self.dir):
            config = apprise.parse_config(parameters(ca_file="~/server.pem"))
        self.assertEqual(Path(config.ca_file), self.dir / "server.pem")

    def test_invalid_ca_files_are_permanent_configuration_errors(self):
        empty = self.dir / "empty.pem"
        empty.write_text("", encoding="utf-8")
        garbage = self.dir / "garbage.pem"
        garbage.write_text("this is not a certificate\n", encoding="utf-8")
        for name, path in {
            "missing": str(self.dir / "does-not-exist.pem"),
            "directory": str(self.dir),
            "empty": str(empty),
            "garbage": str(garbage),
            "control character": "bad\npath.pem",
        }.items():
            with self.subTest(name):
                env = {**fixture("service_critical"), **parameters(ca_file=path)}
                code, out = run_main(env)
                self.assertEqual(code, 2)
                self.assertIn("CA_FILE", out)
                self.assertNotIn(str(self.dir), out)


class mock_home:  # noqa: N801 - tiny context manager used as a function
    """Point os.path.expanduser at a directory without touching the real home."""

    def __init__(self, home: Path):
        from unittest import mock

        self._patch = mock.patch.dict("os.environ", {"HOME": str(home), "USERPROFILE": str(home)})

    def __enter__(self):
        self._patch.start()

    def __exit__(self, *exc):
        self._patch.stop()


class CaFileWithoutOpenSslTest(unittest.TestCase):
    def test_empty_value_means_system_trust(self):
        self.assertEqual(apprise.parse_config(parameters()).ca_file, "")
        self.assertEqual(apprise.parse_config(parameters(ca_file="  ")).ca_file, "")

    def test_default_context_uses_system_certificates(self):
        context = apprise.build_ssl_context(True)
        self.assertEqual(context.verify_mode, apprise.ssl.CERT_REQUIRED)


if __name__ == "__main__":
    unittest.main()
