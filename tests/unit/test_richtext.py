# SPDX-License-Identifier: GPL-2.0-only
"""Rich text (HTML input) tests: exact bodies, escaping and Apprise's own conversion."""

import json
import unittest

from test_core import FIXTURES, apprise, event, fixture, parameters

try:  # only used for an optional cross-check; Apprise is never a dependency of the plugin
    from apprise.conversion import convert_between
except ImportError:
    convert_between = None


def html_body(name: str = "service_critical", **env_overrides: str) -> str:
    env = {**fixture(name), **env_overrides}
    return apprise.build_body(apprise.parse_event(env), "html")


def all_fixture_events():
    for path in sorted(FIXTURES.glob("*_*.json")):
        env = json.loads(path.read_text(encoding="utf-8"))
        yield path.stem, apprise.parse_event(env)


class HtmlBodyTest(unittest.TestCase):
    def test_exact_service_body(self):
        self.assertEqual(
            html_body(),
            "<b>Service:</b> CPU utilization<br>"
            "<b>State:</b> CRITICAL<br>"
            "<b>Output:</b> CPU utilization: 97.8%"
            "<br><br>"
            "<b>Host:</b> dc01.example.net<br>"
            "<b>Address:</b> 10.10.20.11<br>"
            "<b>Site:</b> prod<br>"
            "<b>Notification:</b> PROBLEM",
        )

    def test_exact_host_body(self):
        self.assertEqual(
            html_body("host_down"),
            "<b>State:</b> DOWN<br>"
            "<b>Output:</b> Packet loss: 100%"
            "<br><br>"
            "<b>Host:</b> router01.example.net<br>"
            "<b>Address:</b> 10.10.1.1<br>"
            "<b>Site:</b> prod<br>"
            "<b>Notification:</b> PROBLEM",
        )

    def test_multiline_details(self):
        body = html_body(NOTIFY_LONGSERVICEOUTPUT="line1\\nline2")
        self.assertIn("<b>Details:</b><br>line1<br>line2", body)

    def test_comment_with_author(self):
        self.assertIn("<b>Comment:</b> Working on it (cmkadmin)", html_body("service_ack"))

    def test_markup_in_monitoring_data_is_escaped(self):
        body = html_body(
            NOTIFY_SERVICEOUTPUT="<script>alert(1)</script> a & b [x](http://evil) *y* _z_"
        )
        self.assertNotIn("<script>", body)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt; a &amp; b", body)
        # Markdown syntax is irrelevant in HTML input and stays literal
        self.assertIn("[x](http://evil) *y* _z_", body)

    def test_host_name_with_markup_characters(self):
        env = {**fixture("host_down"), "NOTIFY_HOSTNAME": "my_host<01>"}
        self.assertIn(
            "<b>Host:</b> my_host&lt;01&gt;", apprise.build_body(apprise.parse_event(env), "html")
        )

    def test_titles_stay_plain_text(self):
        env = {**fixture("host_down"), "NOTIFY_HOSTNAME": "my_host&01"}
        self.assertEqual(apprise.build_title(apprise.parse_event(env)), "DOWN: my_host&01")

    def test_text_body_is_unchanged(self):
        ev = event("service_critical")
        self.assertEqual(apprise.build_body(ev), apprise.build_body(ev, "text"))
        self.assertNotIn("<", apprise.build_body(ev, "text"))

    def test_payload_body_depends_on_format(self):
        ev = event("service_critical")
        for fmt, marker in (("html", "<b>State:</b>"), ("text", "State:")):
            config = apprise.parse_config(parameters(message_format=fmt))
            self.assertIn(marker, apprise.build_payload(config, ev)["body"])

    def test_markdown_is_no_longer_supported(self):
        with self.assertRaises(apprise.ConfigError):
            apprise.parse_config(parameters(message_format="markdown"))


@unittest.skipIf(convert_between is None, "apprise is not installed (optional cross-check)")
class AppriseConversionTest(unittest.TestCase):
    """Cross-check against Apprise's own converters (run locally with apprise installed)."""

    def test_html_input_becomes_the_plain_text_layout_on_text_targets(self):
        for name, ev in all_fixture_events():
            with self.subTest(name):
                converted = convert_between("html", "text", apprise.build_body(ev, "html"))
                self.assertEqual(converted, apprise.build_body(ev, "text"))

    def test_html_input_becomes_bold_labels_on_markdown_targets(self):
        ev = event("service_critical")
        converted = convert_between("html", "markdown", apprise.build_body(ev, "html"))
        self.assertIn("**State:** CRITICAL", converted)
        self.assertNotIn("<b>", converted)


if __name__ == "__main__":
    unittest.main()
