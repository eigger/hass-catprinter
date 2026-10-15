"""Printer-specific sentences for a failed BLE session (no Home Assistant imports).

``blesession`` words the causes every BLE device shares (a proxy with no free
slot, a weak signal, a stack that stopped answering). What only a cat printer
can say lives here.
"""

from __future__ import annotations

from blesession import (
    Failure,
    GattMismatch,
    SessionDropped,
    WriteTimeout,
    generic_cause,
)

from .errors import CatPrinterError, ErrorCode, PrinterError

_PRINTER_FAULTS = {
    "out_of_paper": "The printer is out of paper. Load a roll and print again.",
    "cover_open": "The cover is open. Close it and print again.",
    "overheating": "The print head is too hot. Let it cool down and print again.",
}

_CODE_CAUSES = {
    ErrorCode.UNSUPPORTED_DEVICE: (
        "This printer model cannot be controlled from Home Assistant "
        "(it needs a vendor challenge or a flow control that is not implemented)."
    ),
    ErrorCode.UNKNOWN_DEVICE: (
        "The model could not be identified from its Bluetooth name. "
        "Pick the model in the integration options."
    ),
    ErrorCode.SERVICE_NOT_FOUND: (
        "The printer does not expose any known print service. It may be "
        "another model or firmware than the one selected."
    ),
    ErrorCode.STALLED: (
        "The printer stopped accepting data mid-job. Check paper and cover; "
        "a weak link can cause this too."
    ),
    ErrorCode.TIMEOUT: (
        "The printer did not confirm the job in time. The image may still "
        "have printed; check paper and the link."
    ),
    ErrorCode.NOT_CONNECTED: "The printer dropped the link during the job.",
}

_FALLBACK_CAUSE = "The session failed before the first stage was reached; see error."



def printer_cause(failure: Failure, operation: str) -> str | None:
    """The printer's own reading of a failure, or None where the shared one fits."""
    exc = failure.exc
    if isinstance(exc, PrinterError):
        return _PRINTER_FAULTS.get(exc.status, f"The printer reported a fault: {exc.status}.")
    # Link-level failures the library already words precisely (a hung write,
    # a dropped link, a missing characteristic): its sentence and key win.
    if isinstance(exc, (WriteTimeout, SessionDropped, GattMismatch)):
        return None
    if isinstance(exc, CatPrinterError) and exc.code in _CODE_CAUSES:
        return _CODE_CAUSES[exc.code]
    return None


def cause(failure: Failure, operation: str) -> str | None:
    """The ``cause`` callback for ``build_report``.

    The printer's sentence first. Where the shared sentence applies, ``None``
    lets ``build_report`` word it and attach ``likely_cause_key``; a failure
    neither covers still gets the fallback.
    """
    text = printer_cause(failure, operation)
    if text is not None:
        return text
    shared = generic_cause(
        failure.stage,
        failure.error,
        failure.facts,
        exc=failure.exc,
        noun="printer",
    )
    if shared is not None:
        return None
    if failure.stage:
        return f"The session failed during the {failure.stage} stage; see error."
    return _FALLBACK_CAUSE
