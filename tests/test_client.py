"""Client transport tests against a fake BleakClient."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from catprinter_ble import client as client_mod
from catprinter_ble import protocol as p
from catprinter_ble.client import CatPrinterClient
from catprinter_ble.errors import CatPrinterError, ErrorCode, PrinterError
from catprinter_ble.models import find_profile_by_name

AE30 = "0000ae30-0000-1000-8000-00805f9b34fb"
AE01 = "0000ae01-0000-1000-8000-00805f9b34fb"
AE02 = "0000ae02-0000-1000-8000-00805f9b34fb"


def reply(cmd: int, payload: bytes) -> bytes:
    return p.MAGIC + bytes((cmd, 0x01, len(payload), 0)) + payload + bytes((p.crc8(payload), 0xFF))


class FakeClient:
    """Just enough of BleakClient for CatPrinterClient."""

    def __init__(self) -> None:
        self.is_connected = True
        self.mtu_size = 512
        self.writes: list[bytes] = []
        self._notify = None
        chars = [
            SimpleNamespace(uuid=AE01, properties=["write-without-response"]),
            SimpleNamespace(uuid=AE02, properties=["notify"]),
        ]
        service = SimpleNamespace(uuid=AE30, characteristics=chars)
        self.services = SimpleNamespace(get_service=lambda u: service if u == AE30 else None)

    async def write_gatt_char(self, uuid, data, response=False):
        self.writes.append(bytes(data))
        await asyncio.sleep(0)  # a real write yields to the loop

    async def start_notify(self, uuid, cb):
        self._notify = cb

    async def stop_notify(self, uuid):
        self._notify = None

    def push(self, data: bytes) -> None:
        self._notify(None, bytearray(data))


@pytest.fixture
def printer():
    fake = FakeClient()
    profile = find_profile_by_name("X6h-0000")
    return fake, CatPrinterClient(fake, profile, interval_ms=0)


def test_start_picks_ae30_and_caps_packet_size(printer):
    fake, c = printer
    asyncio.run(c.start())
    assert c.packet_size == 177  # min(512-3, 180-3, 180)
    assert fake._notify is not None


def test_query_state_roundtrip(printer):
    fake, c = printer

    async def run():
        await c.start()
        task = asyncio.ensure_future(c.query_state())
        await asyncio.sleep(0)
        fake.push(reply(0xA3, bytes.fromhex("00 0d 27")))
        return await task

    state = asyncio.run(run())
    assert fake.writes[0] == p.cmd_get_state()
    assert state.conditions == () and state.battery_raw == 0x27


def test_print_job_completes_on_trailing_state_reply(printer):
    fake, c = printer
    job = p.build_print_job([bytes(48)] * 10, 384, p.JobParams(energy=5000, speed=10, feed_dots=48))

    async def run():
        await c.start()
        task = asyncio.ensure_future(c.print_job(job, 10))
        while b"".join(fake.writes) != job:
            await asyncio.sleep(0)
        fake.push(reply(0xA3, bytes.fromhex("00 0d 27")))
        return await task

    state = asyncio.run(run())
    assert state.fault is None
    assert b"".join(fake.writes) == job


def test_print_job_reports_fault_from_trailing_reply(printer):
    fake, c = printer
    job = p.build_print_job([bytes(48)] * 2, 384, p.JobParams(energy=None, speed=10, feed_dots=0))

    async def run():
        await c.start()
        task = asyncio.ensure_future(c.print_job(job, 2))
        while b"".join(fake.writes) != job:
            await asyncio.sleep(0)
        fake.push(reply(0xA3, bytes.fromhex("01 00 27")))
        return await task

    with pytest.raises(PrinterError) as exc:
        asyncio.run(run())
    assert exc.value.status == "out_of_paper"


def test_stall_aborts_instead_of_pushing_on(printer, monkeypatch):
    """Buffer-full with no drain: stop sending, send A6 05, raise STALLED."""
    fake, c = printer
    monkeypatch.setattr(client_mod, "FLOW_RESUME_TIMEOUT", 0.05)
    job = p.build_print_job([bytes(48)] * 200, 384, p.JobParams(energy=None, speed=10, feed_dots=0))

    async def run():
        await c.start()
        task = asyncio.ensure_future(c.print_job(job, 200))
        while len(fake.writes) < 2:
            await asyncio.sleep(0)
        fake.push(reply(0xAE, bytes.fromhex("10 70")))  # buffer full, never drained
        return await task

    with pytest.raises(CatPrinterError) as exc:
        asyncio.run(run())
    assert exc.value.code == ErrorCode.STALLED
    sent = b"".join(w for w in fake.writes if w != p.cmd_stop())
    assert len(sent) < len(job), "kept pushing after the stall"
    assert fake.writes[-1] == p.cmd_stop()


def test_flow_control_resumes_after_drain(printer, monkeypatch):
    fake, c = printer
    monkeypatch.setattr(client_mod, "FLOW_RESUME_TIMEOUT", 1.0)
    job = p.build_print_job([bytes(48)] * 200, 384, p.JobParams(energy=None, speed=10, feed_dots=0))

    async def run():
        await c.start()
        task = asyncio.ensure_future(c.print_job(job, 200))
        while len(fake.writes) < 2:
            await asyncio.sleep(0)
        fake.push(reply(0xAE, bytes.fromhex("10 70")))
        await asyncio.sleep(0.02)
        frozen = len(fake.writes)
        await asyncio.sleep(0.02)
        assert len(fake.writes) == frozen, "wrote while buffer was full"
        fake.push(reply(0xAE, bytes.fromhex("00 00")))
        while b"".join(fake.writes) != job:
            await asyncio.sleep(0)
        fake.push(reply(0xA3, bytes.fromhex("00 0d 27")))
        return await task

    assert asyncio.run(run()).fault is None
