"""Exceptions for the cat printer BLE protocol layer."""

from __future__ import annotations

from enum import StrEnum

from blesession import BleSessionError, DeviceError


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


#: Codes a retry cannot change: the model or firmware is what it is.
_NOT_RETRYABLE = frozenset(
    {
        ErrorCode.UNKNOWN_DEVICE,
        ErrorCode.UNSUPPORTED_DEVICE,
        ErrorCode.SERVICE_NOT_FOUND,
        ErrorCode.PRINTER_ERROR,
    }
)


class CatPrinterError(BleSessionError):
    """Base error raised by the protocol layer.

    A ``BleSessionError`` is a ``ConnectionError``; failures raised by the
    connection layer itself (bleak) are not, so callers still catch both.
    """

    def __init__(self, code: ErrorCode, message: str) -> None:
        super().__init__(message, retryable=code not in _NOT_RETRYABLE)
        self.code = code


class PrinterError(CatPrinterError, DeviceError):
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
