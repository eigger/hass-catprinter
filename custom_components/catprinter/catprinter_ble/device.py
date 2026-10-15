"""Home Assistant facing adapter around CatPrinterClient.

Owns the connection, serialises access with a lock, and exposes the
coordinator-friendly ``BLEData`` snapshot.
"""

from __future__ import annotations

import asyncio
import contextlib
import dataclasses
import logging
import time
from collections.abc import AsyncIterator, Callable

from bleak import BleakClient
from bleak.exc import BleakError
from bleak.backends.device import BLEDevice
from blesession import (
    DISCONNECT_TIMEOUT_S,
    BleSessionError,
    SessionReports,
    SessionTrace,
    WriteTimeout,
    ble_session,
    is_proxy,
    stages,
)
from PIL import Image

from .client import CatPrinterClient
from .errors import CatPrinterError, ErrorCode, PrinterError, UnsupportedDeviceError
from .imaging import fit_to_printhead, to_raster
from .models import DEFAULT_DENSITY, DeviceProfile, find_profile_by_name, get_profile
from .protocol import (
    DeviceState,
    JobParams,
    PrintMode,
    battery_percent,
    build_print_job,
)

_LOGGER = logging.getLogger(__name__)

#: Pacing used when the link goes through a remote (ESPHome) Bluetooth proxy
#: and the user left the interval on "auto". The vendor profile values assume
#: a phone's direct BLE link; an ESP32 proxy silently drops write-without-
#: response packets when fed 177 bytes every 4 ms, which shows up as garbage
#: bands or a truncated print.
PROXY_INTERVAL_MS = 20
PROXY_PACKET_SIZE = 100

#: Our stage names -> blesession's shared vocabulary, so ``failed_stage`` reads
#: the same here as in every other integration.
STAGE_MAP = {
    "subscribe": stages.SESSION,
    "precheck": stages.SESSION,
    "query_info": stages.SESSION,
    "query_state": stages.SESSION,
    "raster": stages.TRANSFER,
    "feed": stages.TRANSFER,
}

#: Callback signature: ``(operation, trace, outcome)`` with ``outcome`` the
#: exception that ended the session, or None.
SessionCallback = Callable[[str, SessionTrace, BaseException | None], None]


@dataclasses.dataclass
class _Session:
    """What an ``_operation`` hands its body."""

    printer: CatPrinterClient
    trace: SessionTrace
    profile: DeviceProfile
    #: Set by the body when the caller will report the outcome itself after
    #: the link is closed (a stalled print is re-judged by ``_diagnose``).
    defer_commit: bool = False


@dataclasses.dataclass
class BLEData:
    """Snapshot of everything known about the printer."""

    name: str = ""
    address: str = ""
    identifier: str = ""
    model_id: str = ""
    device_type: str = ""
    sw_version: str = ""
    printhead_px: int = 384
    dpi: int = 200
    sensors: dict[str, str | int | float | None] = dataclasses.field(
        default_factory=lambda: {
            "battery": None,
            "status": None,
            "conditions": None,
            "label_sensor": None,
        }
    )


class CatPrinterDevice:
    """Connection owner and print entry point for one printer."""

    def __init__(
        self,
        address: str,
        *,
        model_id: str | None = None,
        keep_connection: bool = False,
        interval_ms: int | None = None,
        packet_size_cap: int = 180,
    ) -> None:
        self.address = address
        self.forced_model_id = model_id
        self.keep_connection = keep_connection
        self._interval_ms = interval_ms
        self._packet_size_cap = packet_size_cap
        self._proxy = False

        self.lock = asyncio.Lock()
        self.reports = SessionReports()
        #: Called once per finished session worth reporting (see ``_commit_session``).
        self.callback_session: SessionCallback | None = None
        self.client: BleakClient | None = None
        self.profile: DeviceProfile | None = None
        self.ble_data = BLEData(
            address=address,
            name="Cat Printer",
            identifier=address.replace(":", "")[-6:],
        )

        self._connection_listeners: set[Callable[[], None]] = set()
        self._printing_listeners: set[Callable[[], None]] = set()
        self._is_printing = False
        self._print_start: float | None = None
        self._print_end: float | None = None

    def add_connection_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        self._connection_listeners.add(listener)
        return lambda: self._connection_listeners.discard(listener)

    def add_printing_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        self._printing_listeners.add(listener)
        return lambda: self._printing_listeners.discard(listener)

    # ------------------------------------------------------------------
    # state
    # ------------------------------------------------------------------

    @property
    def is_connected(self) -> bool:
        return self.client is not None and self.client.is_connected

    @property
    def is_printing(self) -> bool:
        return self._is_printing

    @property
    def print_duration(self) -> float:
        if self._print_start is None:
            return 0.0
        if self._is_printing:
            return time.time() - self._print_start
        if self._print_end is not None:
            return self._print_end - self._print_start
        return 0.0

    def _notify_connection(self) -> None:
        for listener in list(self._connection_listeners):
            listener()

    def _notify_printing(self) -> None:
        for listener in list(self._printing_listeners):
            listener()

    # ------------------------------------------------------------------
    # connection
    # ------------------------------------------------------------------

    def _resolve_profile(self, ble_device: BLEDevice) -> DeviceProfile:
        if self.profile is not None:
            return self.profile

        if self.forced_model_id:
            profile = get_profile(self.forced_model_id)
            if profile is None:
                raise CatPrinterError(
                    ErrorCode.UNKNOWN_DEVICE, f"Unknown model {self.forced_model_id!r}"
                )
        else:
            profile = find_profile_by_name(ble_device.name)
        if profile is None:
            raise CatPrinterError(
                ErrorCode.UNKNOWN_DEVICE,
                f"No profile matches the BLE name {ble_device.name!r}",
            )
        if not profile.supported:
            raise UnsupportedDeviceError(
                ble_device.name or profile.model_id, profile.unsupported_reason
            )

        self.profile = profile
        self.ble_data.model_id = profile.model_id
        self.ble_data.printhead_px = profile.printhead_px
        self.ble_data.dpi = profile.dpi
        return profile

    @contextlib.asynccontextmanager
    async def _operation(
        self, ble_device: BLEDevice, operation: str
    ) -> AsyncIterator[_Session]:
        """One BLE operation: resolve the model, connect, subscribe, run the
        body, unsubscribe, disconnect, then file the report.

        Callers hold ``self.lock``. ``ble_session`` owns the connect, reusing
        a ``keep_connection`` link, the drop watch and the bounded disconnect.
        """
        trace = SessionTrace(stage_map=STAGE_MAP)
        outcome: BaseException | None = None
        session: _Session | None = None
        try:
            profile = self._resolve_profile(ble_device)
            async with ble_session(
                ble_device,
                trace=trace,
                name=ble_device.address,
                client=self.client,
                keep=self.keep_connection,
                use_services_cache=False,
            ) as client:
                if client is not self.client:
                    self.client = client
                    self._notify_connection()
                self._proxy = is_proxy(ble_device)
                if self._proxy:
                    _LOGGER.debug(
                        "%s reached via Bluetooth proxy; using proxy pacing", ble_device.address
                    )
                printer = self._make_client(client, profile)
                session = _Session(printer, trace, profile)
                try:
                    with trace.timed("subscribe"):
                        await printer.start()
                    yield session
                finally:
                    await printer.stop()
        except BaseException as exc:
            outcome = exc
            raise
        finally:
            if self.client is not None and (
                not self.keep_connection or not self.client.is_connected
            ):
                self.client = None
                self._notify_connection()
            if session is None or not session.defer_commit:
                self._commit_session(operation, trace, outcome)

    def _commit_session(
        self, operation: str, trace: SessionTrace, outcome: BaseException | None
    ) -> None:
        """Hand a finished session to ``callback_session``.

        A cancelled session is not an outcome. Prints and feeds are always
        reported; a poll only when it failed in a way that counts, so a
        printer that is off or asleep between jobs does not climb the error
        count on every scan interval.
        """
        if isinstance(outcome, asyncio.CancelledError) or self.callback_session is None:
            return
        if operation == "diagnose":
            return
        if operation == "poll" and (outcome is None or not self._counts_as_failure(trace, outcome)):
            return
        try:
            self.callback_session(operation, trace, outcome)
        except Exception:  # noqa: BLE001 - diagnostics must not mask the outcome
            _LOGGER.debug("Reporting the %s session failed", operation, exc_info=True)

    @staticmethod
    def _counts_as_failure(trace: SessionTrace, outcome: BaseException) -> bool:
        """Whether a failed *poll* belongs on the failure sensors.

        Not when the printer could not be reached (off, asleep, out of range)
        and not when the model is permanently unusable: both repeat on every
        poll and would push the last real failure off the sensor.
        """
        if trace.failed_primary in (stages.CONNECT, stages.UNREACHABLE):
            return False
        return not (
            isinstance(outcome, CatPrinterError)
            and outcome.code in (ErrorCode.UNKNOWN_DEVICE, ErrorCode.UNSUPPORTED_DEVICE)
        )

    def _make_client(self, client: BleakClient, profile: DeviceProfile) -> CatPrinterClient:
        interval = self._interval_ms
        cap = self._packet_size_cap
        if self._proxy:
            if interval is None:
                interval = max(profile.interval_ms, PROXY_INTERVAL_MS)
            cap = min(cap, PROXY_PACKET_SIZE)
        printer = CatPrinterClient(
            client,
            profile,
            interval_ms=interval,
            packet_size_cap=cap,
        )
        printer.on_state = self._apply_state
        return printer

    def _apply_state(self, state: DeviceState) -> None:
        profile = self.profile
        sensors = self.ble_data.sensors
        sensors["status"] = state.fault or ("printing" if state.is_printing else "ok")
        sensors["conditions"] = ", ".join(state.conditions) or "none"
        sensors["label_sensor"] = state.label_sensor
        if profile is not None:
            battery = battery_percent(state.battery_raw, profile.battery_model)
            if battery is not None:
                sensors["battery"] = battery

    async def disconnect(self) -> None:
        if self.client and self.client.is_connected:
            try:
                # A proxy that stopped answering must not hold the locks.
                async with asyncio.timeout(DISCONNECT_TIMEOUT_S):
                    await self.client.disconnect()
            except Exception:  # noqa: BLE001
                _LOGGER.debug("Disconnect failed", exc_info=True)
                # Do not reuse a link that would not close; connect afresh.
                self.client = None
            self._notify_connection()

    # ------------------------------------------------------------------
    # polling
    # ------------------------------------------------------------------

    def prepare(self, ble_device: BLEDevice) -> DeviceProfile:
        """Resolve the model and fill in name / address from the advertisement.

        Needs no connection, so a poll that is skipped because the adapter is
        busy still gives the entities their name.
        """
        profile = self._resolve_profile(ble_device)
        if not self.ble_data.name or self.ble_data.name == "Cat Printer":
            self.ble_data.name = ble_device.name or profile.model_id
        if not self.ble_data.address:
            self.ble_data.address = ble_device.address
        return profile

    async def update_device(self, ble_device: BLEDevice) -> BLEData:
        """Refresh the BLEData snapshot."""
        async with self.lock:
            self.prepare(ble_device)

            async with self._operation(ble_device, "poll") as session:
                printer, trace = session.printer, session.trace
                if not self.ble_data.sw_version:
                    with trace.timed("query_info"):
                        info = await printer.query_info(required=False)
                    if info is not None:
                        self.ble_data.device_type = info.device_type
                        self.ble_data.sw_version = info.firmware
                with trace.timed("query_state"):
                    await printer.query_state()

            _LOGGER.debug("Obtained BLEData: %s", self.ble_data)
            return self.ble_data

    # ------------------------------------------------------------------
    # printing
    # ------------------------------------------------------------------

    async def print_image(
        self,
        ble_device: BLEDevice,
        image: Image.Image,
        *,
        mode: PrintMode = "image",
        density: int = DEFAULT_DENSITY,
        energy: int | None = None,
        speed: int | None = None,
        feed_dots: int | None = None,
        copies: int = 1,
        on_progress: Callable[[int, int], None] | None = None,
    ) -> dict:
        """Render and print one image."""
        async with self.lock:
            self._is_printing = True
            self._print_start = time.time()
            self._print_end = None
            self._notify_printing()
            stalled: BaseException | None = None
            try:
                try:
                    profile = self._resolve_profile(ble_device)
                except CatPrinterError as err:
                    # Nothing to connect to, but the failure still belongs on
                    # the diagnostic sensors.
                    self._commit_session("print", SessionTrace(stage_map=STAGE_MAP), err)
                    raise
                fitted = fit_to_printhead(image, profile.printhead_px)
                bitmap = to_raster(fitted)
                params = JobParams(
                    mode=mode,
                    energy=energy if energy is not None else profile.energy_for(mode, density),
                    speed=speed if speed is not None else profile.speed_for(mode),
                    feed_dots=feed_dots if feed_dots is not None else profile.default_feed_dots,
                    feed_step=profile.feed_step,
                    copies=copies,
                )
                rows = [bitmap.row(i) for i in range(bitmap.height)]
                job = build_print_job(rows, bitmap.width, params)
                _LOGGER.debug(
                    "Print %dx%d mode=%s energy=%s speed=%d feed=%d copies=%d -> %d bytes",
                    bitmap.width, bitmap.height, params.mode, params.energy,
                    params.speed, params.feed_dots, copies, len(job),
                )

                async with self._operation(ble_device, "print") as session:
                    printer, trace = session.printer, session.trace
                    trace.note(width=bitmap.width, height=bitmap.height, job_bytes=len(job))

                    # Ask before sending: a fault now means the raster would only
                    # be discarded, and the error surfaces immediately instead of
                    # after the whole job has been pushed.
                    with trace.timed("precheck"):
                        state = await printer.query_state(required=False)
                    if state is not None and state.fault:
                        raise PrinterError(state.fault)
                    try:
                        with trace.timed("raster"):
                            await printer.print_job(job, bitmap.height * copies, on_progress)
                    except (CatPrinterError, WriteTimeout) as err:
                        if isinstance(err, CatPrinterError) and err.code not in (
                            ErrorCode.STALLED,
                            ErrorCode.TIMEOUT,
                        ):
                            raise
                        # The printer went quiet mid-job. It does not push status
                        # on its own, and a stalled command queue does not answer
                        # queries either, so close this link, reconnect and ask on
                        # a clean one to name the cause. The report waits for that.
                        stalled = err
                        session.defer_commit = True

                if stalled is not None:
                    outcome: BaseException = stalled
                    # A cancel during the diagnosis still reports: the stall happened.
                    try:
                        fault = await self._diagnose(ble_device)
                        if fault:
                            outcome = PrinterError(fault)
                            outcome.__cause__ = stalled
                    finally:
                        self._commit_session("print", trace, outcome)
                    raise outcome
            finally:
                self._print_end = time.time()
                self._is_printing = False
                self._notify_printing()

        return {
            "status": "ok",
            "duration": round(self.print_duration, 1),
            "width": bitmap.width,
            "height": bitmap.height,
            "copies": copies,
            "bytes": len(job),
            "energy": params.energy,
            "speed": params.speed,
        }

    async def _diagnose(self, ble_device: BLEDevice) -> str | None:
        """Drop any kept connection, reconnect and read the status once."""
        await self.disconnect()
        try:
            async with self._operation(ble_device, "diagnose") as session:
                with session.trace.timed("query_state"):
                    state = await session.printer.query_state(required=False)
        except Exception:  # noqa: BLE001 - diagnosis is best effort
            _LOGGER.debug("Could not read status after a stalled job", exc_info=True)
            return None
        return state.fault if state is not None else None

    async def feed(self, ble_device: BLEDevice, dots: int) -> None:
        """Advance the paper without printing."""
        async with self.lock:
            async with self._operation(ble_device, "feed") as session:
                profile, printer, trace = session.profile, session.printer, session.trace
                with trace.timed("feed"):
                    await printer.feed(dots, profile.feed_step)
                try:
                    with trace.timed("query_state"):
                        await printer.query_state(required=False)
                except (BleSessionError, BleakError, RuntimeError):
                    # The paper has moved; a lost status read is not a failed feed.
                    _LOGGER.debug("Status read after feed failed", exc_info=True)
