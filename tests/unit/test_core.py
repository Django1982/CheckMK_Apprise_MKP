# SPDX-License-Identifier: GPL-2.0-only
"""M1 notification core tests. No real Checkmk or Apprise server is required."""

import base64
import importlib.machinery
import importlib.util
import io
import json
import socket
import ssl
import sys
import threading
import types
import unittest
from contextlib import redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from time import sleep
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "src/local/share/check_mk/notifications/apprise"
FIXTURES = REPO / "tests/fixtures"

_loader = importlib.machinery.SourceFileLoader("apprise_script", str(SCRIPT))
_spec = importlib.util.spec_from_loader("apprise_script", _loader)
apprise = importlib.util.module_from_spec(_spec)
_loader.exec_module(apprise)


def fixture(name: str) -> dict[str, str]:
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))


def parameters(**overrides: str) -> dict[str, str]:
    env = fixture("parameters")
    for key, value in overrides.items():
        env["NOTIFY_PARAMETER_" + key.upper()] = value
    return env


def event(name: str) -> "apprise.Event":
    return apprise.parse_event(fixture(name))


class MockApprise:
    """Local HTTP server that records requests and answers with a fixed status."""

    def __init__(
        self,
        status: int = 200,
        delay: float = 0,
        location: str = "",
        tls: tuple[str, str] | None = None,
    ):
        outer = self
        self.requests: list[dict] = []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                outer.requests.append(
                    {
                        "path": self.path,
                        "headers": dict(self.headers),
                        "body": json.loads(self.rfile.read(length)),
                    }
                )
                sleep(delay)
                self.send_response(status)
                if location:
                    self.send_header("Location", location)
                self.send_header("Content-Length", "2")
                self.end_headers()
                self.wfile.write(b"{}")

            def do_GET(self):  # target of a (never followed) redirect
                outer.requests.append({"path": self.path, "method": "GET"})
                self.send_response(200)
                self.send_header("Content-Length", "0")
                self.end_headers()

            def log_message(self, *args):
                pass

        class QuietServer(ThreadingHTTPServer):
            def handle_error(self, request, client_address):
                pass  # clients that time out abort the connection on purpose

        self.server = QuietServer(("127.0.0.1", 0), Handler)
        self.server.daemon_threads = True
        scheme = "http"
        if tls:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(*tls)
            self.server.socket = context.wrap_socket(self.server.socket, server_side=True)
            scheme = "https"
        self.url = f"{scheme}://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(
            target=self.server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True
        ).start()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.server.shutdown()
        self.server.server_close()


def run_main(env: dict[str, str]) -> tuple[int, str]:
    out = io.StringIO()
    with redirect_stdout(out):
        code = apprise.main(env)
    return code, out.getvalue()


class ConfigParsingTest(unittest.TestCase):
    def test_defaults(self):
        env = {
            "NOTIFY_PARAMETER_BASE_URL": "https://apprise.example.net/",
            "NOTIFY_PARAMETER_CONFIG_ID": "checkmk",
        }
        config = apprise.parse_config(env)
        self.assertEqual(config.base_url, "https://apprise.example.net")
        self.assertEqual(config.message_format, "text")
        self.assertTrue(config.verify_tls)
        self.assertEqual(config.timeout, 10)
        self.assertEqual(config.tag, "")

    def test_fixture_parameters(self):
        config = apprise.parse_config(fixture("parameters"))
        self.assertTrue(config.verify_tls)
        self.assertEqual(config.timeout, 10)

    def test_bool_variants(self):
        for raw, expected in [
            ("True", True),
            ("true", True),
            ("1", True),
            ("False", False),
            ("false", False),
            ("0", False),
            ("off", False),
        ]:
            self.assertEqual(apprise.parse_config(parameters(verify_tls=raw)).verify_tls, expected)

    def test_base_url_keeps_path_prefix(self):
        config = apprise.parse_config(parameters(base_url="https://h.example/apprise/"))
        self.assertEqual(apprise.build_url(config), "https://h.example/apprise/notify/checkmk")

    def test_invalid_values_raise_config_error(self):
        bad = [
            {"base_url": ""},
            {"config_id": ""},
            {"config_id": "a/b"},
            {"config_id": "a b"},
            {"config_id": "x" * 65},
            {"base_url": "foo"},
            {"base_url": "ftp://h.example"},
            {"base_url": "https://user:pw@h.example"},
            {"base_url": "https://user@h.example"},
            {"base_url": "https://h.example/?a=b"},
            {"base_url": "https://h.example/#frag"},
            {"base_url": "https://h.example:99999"},
            {"timeout": "0"},
            {"timeout": "121"},
            {"timeout": "abc"},
            {"verify_tls": "maybe"},
            {"message_format": "rtf"},
        ]
        for overrides in bad:
            with self.subTest(overrides=overrides), self.assertRaises(apprise.ConfigError):
                apprise.parse_config(parameters(**overrides))

    def test_error_messages_do_not_contain_the_value(self):
        with self.assertRaises(apprise.ConfigError) as ctx:
            apprise.parse_config(parameters(base_url="https://user:topsecret@h.example"))
        self.assertNotIn("topsecret", str(ctx.exception))


def explicit_password(value: str, password_id: str = "pw1") -> dict[str, str]:
    """Environment as Checkmk flattens ("cmk_postprocessed", "explicit_password", (id, value))."""
    return {
        "NOTIFY_PARAMETER_PASSWORD_1": "cmk_postprocessed",
        "NOTIFY_PARAMETER_PASSWORD_2": "explicit_password",
        "NOTIFY_PARAMETER_PASSWORD_3": f"{password_id}	{value}",
        "NOTIFY_PARAMETER_PASSWORD_3_1": password_id,
        "NOTIFY_PARAMETER_PASSWORD_3_2": value,
    }


def stored_password(store_id: str) -> dict[str, str]:
    return {
        "NOTIFY_PARAMETER_PASSWORD_1": "cmk_postprocessed",
        "NOTIFY_PARAMETER_PASSWORD_2": "stored_password",
        "NOTIFY_PARAMETER_PASSWORD_3": f"{store_id}	",
        "NOTIFY_PARAMETER_PASSWORD_3_1": store_id,
        "NOTIFY_PARAMETER_PASSWORD_3_2": "",
    }


def fake_password_store(extract):
    """Install a fake cmk.utils.password_store so no Checkmk is needed."""
    modules = {}
    for name in ("cmk", "cmk.utils", "cmk.utils.password_store"):
        modules[name] = types.ModuleType(name)
    modules["cmk.utils.password_store"].extract = extract
    modules["cmk"].utils = modules["cmk.utils"]
    modules["cmk.utils"].password_store = modules["cmk.utils.password_store"]
    return mock.patch.dict(sys.modules, modules)


class AuthenticationTest(unittest.TestCase):
    def test_no_credentials_by_default(self):
        config = apprise.parse_config(parameters())
        self.assertEqual((config.username, config.password), ("", ""))

    def test_explicit_password(self):
        env = {**parameters(username="alice"), **explicit_password("s3cr3t")}
        config = apprise.parse_config(env)
        self.assertEqual((config.username, config.password), ("alice", "s3cr3t"))

    def test_stored_password_is_resolved_via_password_store(self):
        seen = []

        def extract(store_id):
            seen.append(store_id)
            return "from-store"

        env = {**parameters(username="alice"), **stored_password("my_store_id")}
        with fake_password_store(extract):
            config = apprise.parse_config(env)
        self.assertEqual(seen, ["my_store_id"])
        self.assertEqual(config.password, "from-store")

    def test_stored_password_lookup_failure_is_permanent_and_silent(self):
        def extract(store_id):
            raise RuntimeError("leaky detail: /omd/sites/x/secret-path")

        env = {
            **fixture("service_critical"),
            **parameters(username="alice"),
            **stored_password("my_store_id"),
        }
        with fake_password_store(extract):
            code, out = run_main(env)
        self.assertEqual(code, 2)
        self.assertIn("password store", out)
        self.assertNotIn("leaky detail", out)

    def test_stored_password_without_checkmk_is_config_error(self):
        env = {**parameters(username="alice"), **stored_password("my_store_id")}
        with mock.patch.dict(
            sys.modules, {"cmk": None, "cmk.utils": None, "cmk.utils.password_store": None}
        ):
            with self.assertRaises(apprise.ConfigError):
                apprise.parse_config(env)

    def test_username_and_password_must_be_set_together(self):
        with self.assertRaises(apprise.ConfigError):
            apprise.parse_config(parameters(username="alice"))
        with self.assertRaises(apprise.ConfigError):
            apprise.parse_config({**parameters(), **explicit_password("x")})

    def test_username_with_colon_is_rejected(self):
        env = {**parameters(username="al:ice"), **explicit_password("x")}
        with self.assertRaises(apprise.ConfigError):
            apprise.parse_config(env)

    def test_password_is_not_in_repr(self):
        config = apprise.parse_config(
            {**parameters(username="alice"), **explicit_password("s3cr3t")}
        )
        self.assertNotIn("s3cr3t", repr(config))

    def test_basic_authorization_header_is_sent(self):
        with MockApprise(200) as server:
            env = {
                **fixture("service_critical"),
                **parameters(base_url=server.url, username="alice"),
                **explicit_password("p@ss:wörd"),
            }
            code, out = run_main(env)
        self.assertEqual(code, 0)
        expected = "Basic " + base64.b64encode("alice:p@ss:wörd".encode()).decode()
        self.assertEqual(server.requests[0]["headers"]["Authorization"], expected)
        self.assertIn("unencrypted HTTP", out)
        self.assertNotIn("p@ss", out)

    def test_401_is_permanent_and_never_prints_credentials(self):
        with MockApprise(401) as server:
            env = {
                **fixture("service_critical"),
                **parameters(base_url=server.url, username="alice"),
                **explicit_password("topsecret"),
            }
            code, out = run_main(env)
        self.assertEqual(code, 2)
        self.assertIn("check credentials", out)
        for forbidden in ("topsecret", "alice"):
            self.assertNotIn(forbidden, out)


class EventParsingTest(unittest.TestCase):
    def test_service_event(self):
        ev = event("service_critical")
        self.assertEqual(
            (ev.what, ev.service, ev.state), ("SERVICE", "CPU utilization", "CRITICAL")
        )

    def test_host_event_ignores_service_fields(self):
        env = {**fixture("host_down"), "NOTIFY_SERVICEDESC": "stale", "NOTIFY_SERVICESTATE": "OK"}
        ev = apprise.parse_event(env)
        self.assertEqual((ev.service, ev.state), ("", "DOWN"))

    def test_invalid_events(self):
        for env in [
            {},
            {"NOTIFY_WHAT": "HOST"},
            {"NOTIFY_WHAT": "SERVICE", "NOTIFY_HOSTNAME": "h"},
            {"NOTIFY_WHAT": "HOST", "NOTIFY_HOSTNAME": "h"},  # no NOTIFICATIONTYPE
        ]:
            with self.subTest(env=env), self.assertRaises(apprise.ConfigError):
                apprise.parse_event(env)

    def test_clean_text(self):
        self.assertEqual(apprise.clean_text("a\x00b\x1b[0mc\x7f"), "ab[0mc")
        self.assertEqual(apprise.clean_text("line1\\nline2"), "line1\nline2")
        long = apprise.clean_text("x" * 5000, 100)
        self.assertEqual(len(long), 100)
        self.assertTrue(long.endswith("…"))


class MappingTest(unittest.TestCase):
    def test_type_mapping(self):
        expected = {
            "service_critical": "failure",
            "service_warning": "warning",
            "service_unknown": "warning",
            "service_recovery": "success",
            "service_ack": "info",
            "service_downtime_start": "info",
            "service_downtime_cancelled": "warning",
            "service_flapping_start": "warning",
            "service_custom": "info",
            "host_down": "failure",
            "host_unreachable": "warning",
            "host_recovery": "success",
        }
        for name, apprise_type in expected.items():
            with self.subTest(name):
                self.assertEqual(apprise.map_type(event(name)), apprise_type)

    def test_event_type_wins_over_state(self):
        # an acknowledged CRITICAL service is "info", not "failure"
        self.assertEqual(event("service_ack").state, "CRITICAL")
        self.assertEqual(apprise.map_type(event("service_ack")), "info")

    def test_flapping_stop_and_disabled_are_info(self):
        for notification_type in ("FLAPPINGSTOP", "FLAPPINGDISABLED"):
            env = {**fixture("service_warning"), "NOTIFY_NOTIFICATIONTYPE": notification_type}
            self.assertEqual(apprise.map_type(apprise.parse_event(env)), "info")

    def test_all_fixture_types_are_valid_apprise_types(self):
        for path in FIXTURES.glob("*_*.json"):
            if path.stem == "parameters":
                continue
            ev = apprise.parse_event(json.loads(path.read_text(encoding="utf-8")))
            self.assertIn(apprise.map_type(ev), ("info", "success", "warning", "failure"))


class MessageTest(unittest.TestCase):
    def test_service_problem(self):
        ev = event("service_critical")
        self.assertEqual(apprise.build_title(ev), "CRITICAL: dc01.example.net - CPU utilization")
        self.assertEqual(
            apprise.build_body(ev),
            "Service: CPU utilization\n"
            "State: CRITICAL\n"
            "Output: CPU utilization: 97.8%\n"
            "\n"
            "Host: dc01.example.net\n"
            "Address: 10.10.20.11\n"
            "Site: prod\n"
            "Notification: PROBLEM",
        )

    def test_host_problem(self):
        ev = event("host_down")
        self.assertEqual(apprise.build_title(ev), "DOWN: router01.example.net")
        self.assertEqual(
            apprise.build_body(ev),
            "State: DOWN\n"
            "Output: Packet loss: 100%\n"
            "\n"
            "Host: router01.example.net\n"
            "Address: 10.10.1.1\n"
            "Site: prod\n"
            "Notification: PROBLEM",
        )

    def test_recovery_is_recognizable(self):
        self.assertEqual(
            apprise.build_title(event("service_recovery")),
            "RECOVERY: dc01.example.net - CPU utilization (OK)",
        )
        self.assertEqual(
            apprise.build_title(event("host_recovery")), "RECOVERY: router01.example.net (UP)"
        )

    def test_acknowledgement_includes_comment_and_author(self):
        ev = event("service_ack")
        self.assertEqual(
            apprise.build_title(ev),
            "ACKNOWLEDGEMENT: dc01.example.net - CPU utilization (CRITICAL)",
        )
        self.assertIn("Comment: Working on it (cmkadmin)", apprise.build_body(ev))

    def test_real_downtime_start_event_does_not_repeat_the_author(self):
        # variables as dumped from a real Checkmk 2.5 downtime start (host, with comment)
        ev = event("host_downtime_start")
        self.assertEqual(apprise.build_title(ev), "DOWNTIME START: www.google.de (UP)")
        self.assertEqual(apprise.map_type(ev), "info")
        body = apprise.build_body(ev)
        self.assertIn("Comment: Author (cmkadmin): 2H Downtime\n", body + "\n")
        self.assertEqual(body.count("cmkadmin"), 1)

    def test_author_is_appended_when_the_comment_lacks_it(self):
        ev = event("service_ack")
        self.assertIn("Comment: Working on it (cmkadmin)", apprise.build_body(ev))

    def test_other_event_titles(self):
        self.assertTrue(
            apprise.build_title(event("service_downtime_start")).startswith("DOWNTIME START: ")
        )
        self.assertTrue(
            apprise.build_title(event("service_downtime_cancelled")).startswith(
                "DOWNTIME CANCELLED: "
            )
        )
        self.assertTrue(
            apprise.build_title(event("service_flapping_start")).startswith("FLAPPING START: ")
        )
        self.assertTrue(apprise.build_title(event("service_custom")).startswith("CUSTOM: "))

    def test_missing_fields_are_omitted_not_faked(self):
        env = fixture("host_down")
        del env["NOTIFY_HOSTADDRESS"], env["NOTIFY_OMD_SITE"]
        body = apprise.build_body(apprise.parse_event(env))
        self.assertNotIn("Address", body)
        self.assertNotIn("Site", body)
        self.assertNotIn("unknown", body.lower())

    def test_long_output_section(self):
        env = {**fixture("service_critical"), "NOTIFY_LONGSERVICEOUTPUT": "line1\\nline2"}
        self.assertIn("\nDetails:\nline1\nline2", apprise.build_body(apprise.parse_event(env)))

    def test_long_output_identical_to_output_is_not_repeated(self):
        env = {**fixture("service_critical"), "NOTIFY_LONGSERVICEOUTPUT": "CPU utilization: 97.8%"}
        self.assertNotIn("Details", apprise.build_body(apprise.parse_event(env)))

    def test_deterministic(self):
        ev = event("service_critical")
        self.assertEqual(apprise.build_body(ev), apprise.build_body(ev))

    def test_output_is_bounded(self):
        env = {**fixture("service_critical"), "NOTIFY_SERVICEOUTPUT": "x" * 100000}
        ev = apprise.parse_event(env)
        self.assertLessEqual(len(ev.output), apprise.MAX_OUTPUT_CHARS)


class PayloadTest(unittest.TestCase):
    def payload(self, **overrides):
        config = apprise.parse_config(parameters(**overrides))
        return apprise.build_payload(config, event("service_critical"))

    def test_payload_fields(self):
        payload = self.payload()
        self.assertEqual(set(payload), {"title", "body", "type", "format"})
        self.assertEqual((payload["type"], payload["format"]), ("failure", "text"))

    def test_tag_only_when_configured(self):
        self.assertNotIn("tag", self.payload())
        self.assertNotIn("tag", self.payload(tag="  "))
        self.assertEqual(self.payload(tag="ops,network")["tag"], "ops,network")

    def test_format_passthrough(self):
        self.assertEqual(self.payload(message_format="html")["format"], "html")


class UrlAndTlsTest(unittest.TestCase):
    def test_config_id_is_quoted(self):
        config = apprise.Config("https://h.example", "a b/c", "", "text", True, 5)
        self.assertEqual(apprise.build_url(config), "https://h.example/notify/a%20b%2Fc")

    def test_tls_verification_default_on(self):
        context = apprise.build_ssl_context(True)
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(context.check_hostname)

    def test_tls_opt_out(self):
        context = apprise.build_ssl_context(False)
        self.assertEqual(context.verify_mode, ssl.CERT_NONE)
        self.assertFalse(context.check_hostname)


class StatusClassificationTest(unittest.TestCase):
    def test_matrix(self):
        expected = {
            200: 0,
            201: 2,
            202: 2,
            204: 2,
            408: 1,
            424: 1,
            429: 1,
            500: 1,
            502: 1,
            503: 1,
            504: 1,
            301: 2,
            302: 2,
            400: 2,
            401: 2,
            403: 2,
            404: 2,
            406: 2,
            409: 2,
            431: 2,
        }
        for status, code in expected.items():
            with self.subTest(status):
                self.assertEqual(apprise.classify_status(status), code)


class TransportTest(unittest.TestCase):
    def deliver(self, server: MockApprise, name: str = "service_critical", **params: str):
        env = {**fixture(name), **parameters(base_url=server.url, **params)}
        return run_main(env)

    def test_success_exit_0_and_request_shape(self):
        with MockApprise(200) as server:
            code, out = self.deliver(server, tag="ops")
        self.assertEqual(code, 0)
        self.assertIn("delivered (HTTP 200)", out)
        (request,) = server.requests
        self.assertEqual(request["path"], "/notify/checkmk")
        self.assertEqual(request["headers"]["Content-Type"], "application/json")
        self.assertNotIn("Authorization", request["headers"])
        self.assertEqual(request["body"]["tag"], "ops")
        self.assertEqual(request["body"]["type"], "failure")

    def test_status_to_exit_code(self):
        for status, expected in [
            (503, 1),
            (500, 1),
            (429, 1),
            (424, 1),
            (408, 1),
            (400, 2),
            (401, 2),
            (403, 2),
            (404, 2),
            (431, 2),
        ]:
            with self.subTest(status), MockApprise(status) as server:
                code, out = self.deliver(server)
                self.assertEqual(code, expected)
                self.assertIn(f"HTTP {status}", out)

    def test_redirect_is_not_followed(self):
        with MockApprise(302) as target:
            with MockApprise(302, location=target.url + "/elsewhere") as server:
                code, out = self.deliver(server)
        self.assertEqual(code, 2)
        self.assertIn("redirects are not followed", out)
        self.assertEqual([r.get("method") for r in target.requests], [])

    def test_timeout_is_temporary(self):
        with MockApprise(200, delay=3) as server:
            code, out = self.deliver(server, timeout="1")
        self.assertEqual(code, 1)
        self.assertIn("timeout", out)

    def test_connection_refused_is_temporary(self):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        code, out = run_main(
            {**fixture("service_critical"), **parameters(base_url=f"http://127.0.0.1:{port}")}
        )
        self.assertEqual(code, 1)
        self.assertIn("connection error", out)

    def test_dns_failure_is_temporary(self):
        env = {**fixture("service_critical"), **parameters(base_url="http://apprise.invalid")}
        with mock.patch("socket.getaddrinfo", side_effect=socket.gaierror(-2, "unknown")):
            code, out = run_main(env)
        self.assertEqual(code, 1)
        self.assertIn("DNS", out)

    def test_unicode_round_trip(self):
        with MockApprise(200) as server:
            code, _ = self.deliver(server, "service_unicode")
        self.assertEqual(code, 0)
        body = server.requests[0]["body"]
        self.assertIn("Füllstand Größe", body["title"])
        self.assertIn("Temperatur 95°C – zu heiß 🔥", body["body"])

    def test_output_never_contains_url_or_config_id(self):
        base = "http://127.0.0.1:1/very-private-prefix"
        env = {
            **fixture("service_critical"),
            **parameters(base_url=base, config_id="secret-config"),
        }
        code, out = run_main(env)
        self.assertEqual(code, 1)
        for forbidden in ("very-private-prefix", "secret-config", "127.0.0.1"):
            self.assertNotIn(forbidden, out)

    def test_invalid_config_exit_2_without_leaking(self):
        env = {
            **fixture("service_critical"),
            **parameters(base_url="https://user:topsecret@h.example"),
        }
        code, out = run_main(env)
        self.assertEqual(code, 2)
        self.assertIn("Apprise configuration invalid", out)
        self.assertNotIn("topsecret", out)

    def test_invalid_event_exit_2(self):
        code, out = run_main(parameters())
        self.assertEqual(code, 2)
        self.assertIn("Checkmk event invalid", out)

    def test_tls_opt_out_prints_visible_warning(self):
        env = {
            **fixture("service_critical"),
            **parameters(base_url="https://127.0.0.1:1", verify_tls="false"),
        }
        _, out = run_main(env)
        self.assertIn("WARNING: TLS certificate verification is disabled", out)

    def test_no_tls_warning_for_plain_http(self):
        env = {
            **fixture("service_critical"),
            **parameters(base_url="http://127.0.0.1:1", verify_tls="false"),
        }
        _, out = run_main(env)
        self.assertNotIn("TLS", out)


if __name__ == "__main__":
    unittest.main()
