"""Exceptions for the cat printer BLE protocol layer."""

from __future__ import annotations

from enum import StrEnum


class ErrorCode(StrEnum):
    """Machine-readable cause of a CatPrinterError."""

    UNKNOWN_DEVICE = "unknown_device"
    UNSUPPORTED_DEVICE = "unsupported_device"
    SERVICE_NOT_FOUND = "service_not_found"
    NOT_CONNECTED = "not_connected"
    PRINT_FAILED = "print_failed"
    TIMEOUT = "timeout"
    STALLED = "stalled"
    PRINTER_ERROR = "printer_error"


class CatPrinterError(Exception):
    """Base error raised by the protocol layer."""

    def __init__(self, code: ErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code


class PrinterError(CatPrinterError):
    """The printer reported a fault (out of paper, cover open, overheating)."""

    def __init__(self, status: str, raw: bytes = b"") -> None:
        super().__init__(ErrorCode.PRINTER_ERROR, f"Printer error: {status}")
        self.status = status
        self.raw = raw


class UnsupportedDeviceError(CatPrinterError):
    """The model is known but this integration cannot drive it.

    Either the printer requires a ``D1`` challenge with a per-model secret
    before it answers anything, or (YMS-BT01) it uses a credit-window flow
    control that has not been implemented.
    """

    def __init__(self, model_id: str, reason: str) -> None:
        super().__init__(
            ErrorCode.UNSUPPORTED_DEVICE,
            f"{model_id} cannot be controlled from Home Assistant: {reason}",
        )
        self.model_id = model_id
        self.reason = reason
