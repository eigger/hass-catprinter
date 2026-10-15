"""Turn a finished BLE session into the attributes the diagnostic sensors show."""

from __future__ import annotations

from typing import Any

from blesession import SessionTrace, build_report
from blesession.hass import radio_facts
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
        noun="printer",
    )
