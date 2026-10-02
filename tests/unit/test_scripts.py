# SPDX-License-Identifier: GPL-2.0-only
"""Tests for the helper scripts in scripts/."""

import importlib.util
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class NotifyEnvDumpTest(unittest.TestCase):
    def test_title_is_on_line_two(self):
        lines = (REPO / "scripts/notify_env_dump.py").read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines[1], "# Dump NOTIFY variables")

    def test_only_notify_variables_without_parameters(self):
        dump = load("notify_env_dump").dump
        env = {
            "NOTIFY_WHAT": "HOST",
            "NOTIFY_PARAMETER_PASSWORD_3_2": "topsecret",
            "NOTIFY_PARAMETER_USERNAME": "alice",
            "PATH": "/usr/bin",
            "HOME": "/omd/sites/x",
            "NOTIFY_SHORTDATETIME": "2026-10-02 10:00",
        }
        lines = dump(env)
        self.assertEqual(lines, ["NOTIFY_SHORTDATETIME=2026-10-02 10:00", "NOTIFY_WHAT=HOST"])
        self.assertNotIn("topsecret", "\n".join(lines))

    def test_long_values_are_shortened(self):
        module = load("notify_env_dump")
        (line,) = module.dump({"NOTIFY_LONGSERVICEOUTPUT": "x" * 1000})
        self.assertLess(len(line), 200)
        self.assertTrue(line.endswith("..."))


if __name__ == "__main__":
    unittest.main()
