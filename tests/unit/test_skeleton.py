# SPDX-License-Identifier: GPL-2.0-only
"""M0.2 skeleton tests: stub behaviour, ruleset wiring and reproducible MKP."""

import ast
import gzip
import importlib.util
import io
import json
import os
import subprocess
import sys
import tarfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "src/local/share/check_mk/notifications/apprise"
RULESET = REPO / "src/local/lib/python3/cmk_addons/plugins/apprise/rulesets/notification.py"


def _load_builder():
    spec = importlib.util.spec_from_file_location("build_mkp", REPO / "scripts/build_mkp.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class NotificationStubTest(unittest.TestCase):
    def test_second_line_is_checkmk_title(self):
        # Checkmk uses line 2 ("# <title>") as the method name in the rule dropdown.
        lines = SCRIPT.read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines[0], "#!/usr/bin/env python3")
        self.assertEqual(lines[1], "# Apprise")
        self.assertNotIn("bulk", lines[2].lower())

    def test_missing_parameters_is_permanent_failure_without_traceback(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("NOTIFY_")}
        proc = subprocess.run(
            [sys.executable, str(SCRIPT)], env=env, capture_output=True, text=True, timeout=30
        )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("Apprise configuration invalid", proc.stdout)
        self.assertNotIn("Traceback", proc.stderr)


class RulesetWiringTest(unittest.TestCase):
    """cmk is not installable here, so the ruleset is checked statically."""

    def setUp(self):
        self.tree = ast.parse(RULESET.read_text(encoding="utf-8"))

    def test_rule_spec_named_apprise(self):
        found = {}
        for node in self.tree.body:
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                target = node.targets[0].id
                kwargs = {k.arg: k.value for k in node.value.keywords}
                if getattr(node.value.func, "id", "") == "NotificationParameters":
                    found[target] = kwargs
        self.assertEqual(len(found), 1)
        ((variable, kwargs),) = found.items()
        self.assertTrue(variable.startswith("rule_spec_"))
        self.assertEqual(kwargs["name"].value, SCRIPT.name)

    def test_validator_messages_are_message_objects(self):
        # A plain str crashes the Checkmk GUI with "'str' object has no attribute 'localize'".
        calls = [
            n
            for n in ast.walk(self.tree)
            if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "MatchRegex"
        ]
        self.assertTrue(calls)
        for call in calls:
            self.assertEqual(len(call.args), 2)
            self.assertEqual(getattr(call.args[1].func, "id", ""), "Message")

    def test_password_uses_password_store_capable_formspec(self):
        # Parameter keys reach the script as NOTIFY_PARAMETER_<KEY>; the script relies on these.
        source = RULESET.read_text(encoding="utf-8")
        for key in (
            "base_url",
            "config_id",
            "tag",
            "username",
            "password",
            "message_format",
            "verify_tls",
            "timeout",
        ):
            self.assertIn(f'"{key}": DictElement(', source)
        self.assertIn("parameter_form=Password(", source)

    def test_no_legacy_registry(self):
        self.assertNotIn("notification_parameter_registry", RULESET.read_text(encoding="utf-8"))


class MkpBuildTest(unittest.TestCase):
    def test_build_is_reproducible_and_contains_expected_parts(self):
        builder = _load_builder()
        name, first = builder.build_mkp()
        _, second = builder.build_mkp()
        self.assertEqual(first, second)
        self.assertEqual(name, f"apprise-{builder.PACKAGE_VERSION}.mkp")

        outer = tarfile.open(fileobj=io.BytesIO(gzip.decompress(first)))
        self.assertEqual(
            sorted(outer.getnames()),
            ["cmk_addons_plugins.tar", "info", "info.json", "notifications.tar"],
        )
        manifest = json.load(outer.extractfile("info.json"))
        self.assertEqual(
            manifest["files"],
            {
                "notifications": ["apprise"],
                "cmk_addons_plugins": ["apprise/rulesets/notification.py"],
            },
        )
        self.assertEqual(ast.literal_eval(outer.extractfile("info").read().decode()), manifest)

        inner = tarfile.open(fileobj=io.BytesIO(outer.extractfile("notifications.tar").read()))
        self.assertEqual(inner.getmember("apprise").mode, 0o755)


if __name__ == "__main__":
    unittest.main()
