#!/usr/bin/env python3
# Dump NOTIFY variables
#
# SPDX-License-Identifier: GPL-2.0-only
# Line 2 above is the title Checkmk shows in the notification method dropdown.
"""Diagnostic notification script: print the NOTIFY_* variables Checkmk hands to a script.

Use it on a *test* site to find out which variables an event type provides (for example
the end time of a downtime). It is a helper, not part of the MKP.

    cp scripts/notify_env_dump.py ~/local/share/check_mk/notifications/dump_env
    chmod +x ~/local/share/check_mk/notifications/dump_env
    # Setup > Events > Notifications: add a rule with the method "Dump NOTIFY variables",
    # trigger the event (for example schedule a downtime), then:
    grep -i "NOTIFY_" ~/var/log/notify.log | tail -n 120
    rm ~/local/share/check_mk/notifications/dump_env      # when finished

Parameters of notification methods (NOTIFY_PARAMETER_*) are never printed, because they can
contain credentials; values are shortened. The output still contains host and service names,
so do not paste it anywhere public without a look.
"""

import os
import sys

MAX_VALUE_CHARS = 120


def dump(env: dict[str, str]) -> list[str]:
    lines = []
    for key in sorted(env):
        if not key.startswith("NOTIFY_") or key.startswith("NOTIFY_PARAMETER"):
            continue
        value = env[key]
        if len(value) > MAX_VALUE_CHARS:
            value = value[:MAX_VALUE_CHARS] + "..."
        lines.append(f"{key}={value}")
    return lines


if __name__ == "__main__":
    print("\n".join(dump(dict(os.environ))))
    sys.exit(0)
