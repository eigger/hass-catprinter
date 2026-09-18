"""BLE transport for one connected cat printer.

Owns a connected ``BleakClient`` but not its lifecycle -- ``CatPrinterDevice``
connects and disconnects. Writes go out as fixed-size chunks without response
with a fixed pause between them, and stop whenever the printer reports its
buffer full (``AE 10 70``) until it reports it drained (``AE 00 00``).
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from time import monotonic

from bleak import BleakClient

from .errors import CatPrinterError, ErrorCode, PrinterError
from .models import SERVICE_CANDIDATES, DeviceProfile
from .protocol import (
    CMD_FLOW,
    CMD_GET_INFO,
    CMD_GET_STATE,
    DeviceInfo,
    DeviceState,
    FrameParser,
    cmd_get_info,
    cmd_get_state,
    cmd_stop,
    decode_flow,
    decode_info,
    decode_state,
    feed_sequence,
)

_LOGGER = logging.getLogger(__name__)

QUERY_TIMEOUT = 5.0
#: How long to sit on a "buffer full" before giving the job up. A full buffer
#: prints in a few seconds; staying full this long means the printer has
#: stopped feeding (paper out, cover open) and pushing more bytes would only
#: corrupt what it prints once it resumes.
FLOW_RESUME_TIMEOUT = 15.0
#: Base wait for the trailing ``A3`` of a job, plus a per-row allowance.
PRINT_RESULT_BASE = 30.0
PRINT_RESULT_PER_ROW = 0.05
PRINT_RESULT_MAX = 600.0

ProgressFn = Callable[[int, int], None]


class CatPrinterClient:
    """Talks to one connected printer."""

    def __init__(
        self,
        client: BleakClient,
        profile: DeviceProfile,
        *,
        interval_ms: int | None = None,
        packet_size_cap: int = 180,
    ) -> None:
        self._client = client
        self._profile = profile
        self._interval = (interval_ms if interval_ms is not None else profile.interval_ms) / 1000
        self._packet_size_cap = packet_size_cap
        self._packet_size = 20
        self._write_uuid: str | None = None
        self._notify_uuid: str | None = None
        self._parser = FrameParser()
        self._flow_ok = asyncio.Event()
        self._flow_ok.set()
        self._pending: dict[int, asyncio.Future] = {}
        self._last_state: DeviceState | None = None
        self.on_state: Callable[[DeviceState], None] | None = None

    # ------------------------------------------------------------------
    # lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Locate the service, pick characteristics, subscribe."""
        services = self._client.services
        for service_uuid, write_uuid in SERVICE_CANDIDATES:
            service = services.get_service(service_uuid)
            if service is None:
                continue
            chars = {c.uuid.lower(): c for c in service.characteristics}
            if write_uuid not in chars:
                continue
            self._write_uuid = write_uuid
            # First NOTIFY/INDICATE characteristic in the service; AE30 -> AE02.
            for char in service.characteristics:
                if "notify" in char.properties or "indicate" in char.properties:
                    self._notify_uuid = char.uuid
                    break
            break
        if self._write_uuid is None:
            raise CatPrinterError(
                ErrorCode.SERVICE_NOT_FOUND,
                "None of the known printer GATT services are present on this device",
            )

        # Three caps: what the link negotiated, what the profile says the
        # firmware takes, and a ceiling for proxies with small MTUs.
        mtu = self._client.mtu_size or 23
        self._packet_size = max(
            20, min(mtu - 3, self._profile.packet_size, self._packet_size_cap)
        )
        _LOGGER.debug(
            "write=%s notify=%s mtu=%d packet=%d interval=%.0fms",
            self._write_uuid,
            self._notify_uuid,
            mtu,
            self._packet_size,
            self._interval * 1000,
        )

        self._parser = FrameParser()
        self._flow_ok.set()
        if self._notify_uuid:
            await self._client.start_notify(self._notify_uuid, self._on_notify)

    async def stop(self) -> None:
        """Unsubscribe. Safe to call more than once, and after a failed start."""
        uuid, self._notify_uuid = self._notify_uuid, None
        if uuid and self._client.is_connected:
            try:
                await self._client.stop_notify(uuid)
            except Exception:  # noqa: BLE001 - teardown must not mask the real error
                _LOGGER.debug("stop_notify(%s) failed", uuid, exc_info=True)
        for future in self._pending.values():
            if not future.done():
                future.cancel()
        self._pending.clear()

    @property
    def packet_size(self) -> int:
        return self._packet_size

    @property
    def last_state(self) -> DeviceState | None:
        return self._last_state

    # ------------------------------------------------------------------
    # writing
    # ------------------------------------------------------------------

    async def send(self, data: bytes, on_progress: ProgressFn | None = None) -> None:
        """Push ``data`` in packet-sized chunks, honouring flow control."""
        assert self._write_uuid is not None
        total = len(data)
        sent = 0
        while sent < total:
            if not self._flow_ok.is_set():
                _LOGGER.debug("Printer buffer full at %d/%d; waiting", sent, total)
                try:
                    await asyncio.wait_for(self._flow_ok.wait(), FLOW_RESUME_TIMEOUT)
                except TimeoutError:
                    raise CatPrinterError(
                        ErrorCode.STALLED,
                        f"Printer stopped taking data at {sent}/{total} bytes "
                        f"for {FLOW_RESUME_TIMEOUT:.0f}s",
                    ) from None
            chunk = data[sent : sent + self._packet_size]
            await self._client.write_gatt_char(self._write_uuid, chunk, response=False)
            sent += len(chunk)
            if on_progress:
                on_progress(sent, total)
            if self._interval:
                await asyncio.sleep(self._interval)

    async def print_job(
        self, job: bytes, rows: int, on_progress: ProgressFn | None = None
    ) -> DeviceState:
        """Send a job built by ``build_print_job`` and wait until it is consumed.

        The job ends with an ``A3``; the printer answers it only after the
        preceding raster has left the buffer, which is the closest thing this
        protocol has to a "done" signal. A fault flag in that reply (or in any
        status frame that arrives mid-job) raises ``PrinterError``.
        """
        waiter = self._add_waiter(CMD_GET_STATE)
        timeout = min(PRINT_RESULT_BASE + rows * PRINT_RESULT_PER_ROW, PRINT_RESULT_MAX)
        try:
            try:
                await self.send(job, on_progress)
            except CatPrinterError as err:
                if err.code == ErrorCode.STALLED:
                    await self._abort()
                raise
            deadline = monotonic() + timeout
            while True:
                if waiter.done():
                    state: DeviceState = waiter.result()
                    if state.fault:
                        raise PrinterError(state.fault)
                    return state
                if self._last_state and self._last_state.fault:
                    raise PrinterError(self._last_state.fault)
                if not self._client.is_connected:
                    raise CatPrinterError(
                        ErrorCode.NOT_CONNECTED, "Printer disconnected during the job"
                    )
                if monotonic() >= deadline:
                    await self._abort()
                    raise CatPrinterError(
                        ErrorCode.TIMEOUT,
                        f"Printer did not confirm the job within {timeout:.0f}s",
                    )
                await asyncio.wait({waiter}, timeout=0.5)
        finally:
            self._drop_waiter(CMD_GET_STATE, waiter)

    async def _abort(self) -> None:
        """Best-effort ``A6 05`` so a stalled printer drops the rest of the job."""
        if not self._client.is_connected or self._write_uuid is None:
            return
        try:
            await self._client.write_gatt_char(self._write_uuid, cmd_stop(), response=False)
        except Exception:  # noqa: BLE001 - the job is already lost
            _LOGGER.debug("Abort command failed", exc_info=True)

    async def feed(self, dots: int, step: int = 48) -> None:
        await self.send(feed_sequence(dots, step))

    # ------------------------------------------------------------------
    # queries
    # ------------------------------------------------------------------

    async def query_state(self) -> DeviceState | None:
        frame = await self._query(CMD_GET_STATE, cmd_get_state())
        return frame

    async def query_info(self) -> DeviceInfo | None:
        return await self._query(CMD_GET_INFO, cmd_get_info())

    async def _query(self, cmd: int, packet: bytes):
        waiter = self._add_waiter(cmd)
        try:
            await self.send(packet)
            return await asyncio.wait_for(waiter, QUERY_TIMEOUT)
        except TimeoutError:
            _LOGGER.debug("No reply to %02X within %.0fs", cmd, QUERY_TIMEOUT)
            return None
        finally:
            self._drop_waiter(cmd, waiter)

    # ------------------------------------------------------------------
    # notifications
    # ------------------------------------------------------------------

    def _on_notify(self, _sender: object, data: bytearray) -> None:
        for frame in self._parser.feed(bytes(data)):
            _LOGGER.debug("RX %s", frame.raw.hex(" "))
            if frame.cmd == CMD_FLOW:
                event = decode_flow(frame.payload)
                if event == "full":
                    self._flow_ok.clear()
                elif event == "empty":
                    self._flow_ok.set()
            elif frame.cmd == CMD_GET_STATE:
                state = decode_state(frame.payload)
                self._last_state = state
                if self.on_state:
                    self.on_state(state)
                self._resolve(CMD_GET_STATE, state)
            elif frame.cmd == CMD_GET_INFO:
                self._resolve(CMD_GET_INFO, decode_info(frame.payload))

    def _add_waiter(self, cmd: int) -> asyncio.Future:
        future: asyncio.Future = asyncio.get_running_loop().create_future()
        self._pending[cmd] = future
        return future

    def _drop_waiter(self, cmd: int, future: asyncio.Future) -> None:
        if self._pending.get(cmd) is future:
            del self._pending[cmd]

    def _resolve(self, cmd: int, value) -> None:
        future = self._pending.get(cmd)
        if future is not None and not future.done():
            future.set_result(value)
