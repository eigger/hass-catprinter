"""The breakdown of one BLE session, as the diagnostic sensors publish it.

``SessionTrace`` records where the session spent its time and where it died.
``blesession`` turns that into the shared report: which radio the link went
over, and one sentence on what a failure most likely means (the printer's own
sentences are in ``catprinter_ble.causes``).
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from blesession import SessionTrace, build_report
from blesession.hass import radio_facts

from .catprinter_ble.causes import cause

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


def build_session_report(
    hass: HomeAssistant,
    address: str,
    *,
    operation: str,
    trace: SessionTrace | None,
    exc: BaseException | None,
) -> dict[str, Any]:
    """Assemble the attributes for one finished session.

    Outcome first, then the radio, then the stage timings, in the order
    ``blesession.build_report`` fixes so the same keys mean the same thing on
    every integration.
    """
    trace = trace if trace is not None else SessionTrace()
    return build_report(
        operation=operation,
        trace=trace,
        exc=exc,
        facts=radio_facts(hass, address, trace.link),
        cause=lambda failure: cause(failure, operation),
        noun="printer",
    )


_ADDRESS = re.compile(
    r"(?<![0-9a-f])(?:[0-9a-f]{2}[:_-]){5}[0-9a-f]{2}(?![0-9a-f])",
    re.IGNORECASE,
)


def redact_addresses(value: str) -> str:
    """Remove full Bluetooth addresses, including BlueZ device paths."""
    return _ADDRESS.sub("**REDACTED**", value)


def redact_report(value):
    """Sanitize nested session attributes before publishing them in HA."""
    if isinstance(value, str):
        return redact_addresses(value)
    if isinstance(value, dict):
        return {key: redact_report(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact_report(item) for item in value]
    return value
