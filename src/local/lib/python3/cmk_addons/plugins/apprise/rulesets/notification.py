#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Checkmk Setup form for the ``apprise`` notification method (Ruleset API v1).

The ``name`` of the NotificationParameters rule spec must equal the notification
script name (``~/local/share/check_mk/notifications/apprise``). Each dictionary
key below reaches the script as ``NOTIFY_PARAMETER_<UPPERCASE_KEY>``.
"""

from cmk.rulesets.v1 import Help, Message, Title
from cmk.rulesets.v1.form_specs import (
    BooleanChoice,
    DefaultValue,
    DictElement,
    Dictionary,
    Integer,
    SingleChoice,
    SingleChoiceElement,
    String,
)
from cmk.rulesets.v1.form_specs.validators import MatchRegex, NumberInRange
from cmk.rulesets.v1.rule_specs import NotificationParameters, Topic


def _parameter_form() -> Dictionary:
    return Dictionary(
        title=Title("Apprise"),
        help_text=Help(
            "Send notifications to an Apprise API server using a saved "
            "configuration (POST /notify/{config_id}). Downstream providers "
            "are configured in Apprise, not in Checkmk."
        ),
        elements={
            "base_url": DictElement(
                required=True,
                parameter_form=String(
                    title=Title("Apprise API base URL"),
                    help_text=Help(
                        "Base URL of the Apprise API server, for example "
                        "https://apprise.example.net. Do not append /notify/..."
                    ),
                    custom_validate=(
                        MatchRegex(
                            r"^https?://[^\s/?#@]+(:[0-9]+)?(/[^\s?#]*)?$",
                            Message("Enter an http(s) URL without credentials, query or fragment."),
                        ),
                    ),
                ),
            ),
            "config_id": DictElement(
                required=True,
                parameter_form=String(
                    title=Title("Apprise configuration ID"),
                    help_text=Help("Key of the saved Apprise configuration."),
                    custom_validate=(
                        MatchRegex(
                            r"^[A-Za-z0-9_-]{1,64}$",
                            Message("Use 1-64 letters, digits, underscores or hyphens."),
                        ),
                    ),
                ),
            ),
            "tag": DictElement(
                required=False,
                parameter_form=String(
                    title=Title("Routing tag expression"),
                    help_text=Help(
                        "Optional Apprise tag expression passed through unchanged. "
                        "Omitted from the request when empty."
                    ),
                ),
            ),
            "message_format": DictElement(
                required=True,
                parameter_form=SingleChoice(
                    title=Title("Message format"),
                    elements=[
                        SingleChoiceElement(name="markdown", title=Title("Markdown")),
                        SingleChoiceElement(name="text", title=Title("Plain text")),
                    ],
                    prefill=DefaultValue("markdown"),
                ),
            ),
            "verify_tls": DictElement(
                required=True,
                parameter_form=BooleanChoice(
                    title=Title("Verify TLS certificate"),
                    help_text=Help("Disable only in controlled environments."),
                    prefill=DefaultValue(True),
                ),
            ),
            "timeout": DictElement(
                required=True,
                parameter_form=Integer(
                    title=Title("Request timeout"),
                    unit_symbol="s",
                    prefill=DefaultValue(10),
                    custom_validate=(NumberInRange(min_value=1, max_value=120),),
                ),
            ),
        },
    )


rule_spec_apprise_notification = NotificationParameters(
    name="apprise",
    title=Title("Apprise"),
    topic=Topic.NOTIFICATIONS,
    parameter_form=_parameter_form,
)
