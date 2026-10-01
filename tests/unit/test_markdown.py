# SPDX-License-Identifier: GPL-2.0-only
"""M3 message formatting tests: Markdown escaping and deterministic bodies."""

import unittest

from test_core import apprise, event, fixture, parameters


def markdown_body(name: str = "service_critical", **env_overrides: str) -> str:
    env = {**fixture(name), **env_overrides}
    return apprise.build_body(apprise.parse_event(env), "markdown")


class MarkdownBodyTest(unittest.TestCase):
    def test_exact_markdown_service_body(self):
        self.assertEqual(
            markdown_body(),
            "**Service:** CPU utilization  \n"
            "**State:** CRITICAL  \n"
            "**Output:** CPU utilization: 97.8%\n"
            "\n"
            "**Host:** dc01.example.net  \n"
            "**Address:** 10.10.20.11  \n"
            "**Site:** prod  \n"
            "**Notification:** PROBLEM",
        )

    def test_exact_markdown_host_body(self):
        self.assertEqual(
            markdown_body("host_down"),
            "**State:** DOWN  \n"
            "**Output:** Packet loss: 100%\n"
            "\n"
            "**Host:** router01.example.net  \n"
            "**Address:** 10.10.1.1  \n"
            "**Site:** prod  \n"
            "**Notification:** PROBLEM",
        )

    def test_text_format_is_plain(self):
        ev = event("service_critical")
        self.assertEqual(apprise.build_body(ev), apprise.build_body(ev, "text"))
        self.assertNotIn("**", apprise.build_body(ev, "text"))

    def test_multiline_details_keep_line_breaks(self):
        body = markdown_body(NOTIFY_LONGSERVICEOUTPUT="line1\\nline2")
        self.assertIn("**Details:**  \nline1  \nline2", body)

    def test_titles_are_plain_text(self):
        env = {**fixture("host_down"), "NOTIFY_HOSTNAME": "my_host_01"}
        ev = apprise.parse_event(env)
        self.assertEqual(apprise.build_title(ev), "DOWN: my_host_01")
        self.assertIn("**Host:** my\\_host\\_01", apprise.build_body(ev, "markdown"))

    def test_link_and_html_injection_is_neutralized(self):
        body = markdown_body(NOTIFY_SERVICEOUTPUT="[click me](http://evil.example) <script>")
        self.assertNotIn("[click me]", body)
        self.assertNotIn("<script>", body)
        self.assertIn("\\[click me\\]", body)

    def test_payload_body_depends_on_format(self):
        ev = event("service_critical")
        for fmt, marker in (("markdown", "**State:**"), ("text", "State:")):
            config = apprise.parse_config(parameters(message_format=fmt))
            self.assertIn(marker, apprise.build_payload(config, ev)["body"])

    def test_html_format_is_not_supported(self):
        with self.assertRaises(apprise.ConfigError):
            apprise.parse_config(parameters(message_format="html"))


class EscapeMarkdownTest(unittest.TestCase):
    def test_inline_specials(self):
        cases = {
            "my_host_01": "my\\_host\\_01",
            "*bold* `code`": "\\*bold\\* \\`code\\`",
            "a\\b": "a\\\\b",
            "a|b #1 ~s~": "a\\|b \\#1 \\~s\\~",
            "[x](y)": "\\[x\\](y)",
            "<b>": "\\<b\\>",
        }
        for raw, expected in cases.items():
            with self.subTest(raw):
                self.assertEqual(apprise.escape_markdown(raw), expected)

    def test_line_start_list_markers(self):
        self.assertEqual(
            apprise.escape_markdown("- item\n+ other\n1. first"),
            "\\- item\n\\+ other\n1\\. first",
        )

    def test_markers_inside_a_line_are_untouched(self):
        self.assertEqual(apprise.escape_markdown("a - b 2. c"), "a - b 2. c")

    def test_plain_text_is_unchanged(self):
        text = "CPU utilization: 97.8% (Größe 95°C) 🔥"
        self.assertEqual(apprise.escape_markdown(text), text)


if __name__ == "__main__":
    unittest.main()
