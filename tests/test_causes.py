"""Printer-specific failure sentences and the reports built from them."""

from __future__ import annotations

from datetime import UTC, datetime

from blesession import (
    ConnectFailed,
    SessionReports,
    SessionTrace,
    WriteTimeout,
    build_report,
    stages,
)

from catprinter_ble.causes import cause
from catprinter_ble.device import STAGE_MAP
from catprinter_ble.errors import CatPrinterError, ErrorCode, PrinterError


def _report(exc, operation="print", stage_name=None):
    trace = SessionTrace(stage_map=STAGE_MAP)
    try:
        with trace.timed(stage_name or "raster"):
            raise exc
    except type(exc):
        pass
    return build_report(
        operation=operation,
        trace=trace,
        exc=exc,
        cause=lambda failure: cause(failure, operation),
        noun="printer",
    )


def test_printer_fault_gets_its_own_sentence():
    report = _report(PrinterError("cover_open"))
    assert report["success"] is False
    assert report["failed_stage"] == stages.TRANSFER
    assert "cover is open" in report["likely_cause"]
    assert "likely_cause_key" not in report  # our sentence, not the library's


def test_every_fault_status_is_worded():
    for status in ("out_of_paper", "cover_open", "overheating"):
        assert status not in _report(PrinterError(status))["likely_cause"]


def test_stall_and_timeout_are_worded():
    stalled = _report(CatPrinterError(ErrorCode.STALLED, "stopped"))
    assert "stopped accepting data" in stalled["likely_cause"]
    timeout = _report(CatPrinterError(ErrorCode.TIMEOUT, "no confirm"))
    assert "did not confirm" in timeout["likely_cause"]


def test_library_sentence_wins_for_a_hung_write():
    report = _report(WriteTimeout(10, step="raster"))
    assert report["likely_cause_key"]


def test_poll_that_cannot_connect_reads_as_asleep():
    report = _report(ConnectFailed("asleep"), operation="poll", stage_name="connect")
    assert "off or asleep" in report["likely_cause"]


def test_unknown_failure_still_gets_a_sentence():
    report = _report(RuntimeError("boom"), stage_name="subscribe")
    assert report["likely_cause"]


def test_print_failure_is_kept_after_a_later_success():
    reports = SessionReports()
    failure = _report(PrinterError("out_of_paper"))
    reports.record(failure, now=datetime(2026, 1, 1, tzinfo=UTC))
    reports.record({"operation": "print", "success": True})
    assert reports.failures == 1
    assert reports.last_failure is failure
    assert reports.of("print")["success"] is True

