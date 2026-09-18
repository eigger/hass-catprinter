"""Home Assistant facing adapter around CatPrinterClient.

Owns the connection, serialises access with a lock, and exposes the
coordinator-friendly ``BLEData`` snapshot.
"""

from __future__ import annotations

import asyncio
import dataclasses
import logging
import time
from collections.abc import Callable

from bleak import BleakClient
from bleak.backends.device import BLEDevice
from bleak_retry_connector import establish_connection
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

        self.lock = asyncio.Lock()
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

    async def _ensure_connected(self, ble_device: BLEDevice) -> BleakClient:
        if self.is_connected:
            assert self.client is not None
            return self.client

        self.client = await establish_connection(
            BleakClient,
            ble_device,
            ble_device.address,
            use_services_cache=False,
        )
        if not self.client.is_connected:
            raise CatPrinterError(ErrorCode.NOT_CONNECTED, "Could not connect to the printer")
        self._notify_connection()
        return self.client

    def _make_client(self, client: BleakClient, profile: DeviceProfile) -> CatPrinterClient:
        printer = CatPrinterClient(
            client,
            profile,
            interval_ms=self._interval_ms,
            packet_size_cap=self._packet_size_cap,
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
                await self.client.disconnect()
            except Exception:  # noqa: BLE001
                _LOGGER.debug("Disconnect failed", exc_info=True)
            self._notify_connection()

    # ------------------------------------------------------------------
    # polling
    # ------------------------------------------------------------------

    async def update_device(self, ble_device: BLEDevice) -> BLEData:
        """Refresh the BLEData snapshot."""
        async with self.lock:
            profile = self._resolve_profile(ble_device)

            if not self.ble_data.name or self.ble_data.name == "Cat Printer":
                self.ble_data.name = ble_device.name or profile.model_id
            if not self.ble_data.address:
                self.ble_data.address = ble_device.address

            client = await self._ensure_connected(ble_device)
            printer = self._make_client(client, profile)

            try:
                await printer.start()
                if not self.ble_data.sw_version:
                    info = await printer.query_info()
                    if info is not None:
                        self.ble_data.device_type = info.device_type
                        self.ble_data.sw_version = info.firmware
                await printer.query_state()
            finally:
                await printer.stop()
                if not self.keep_connection:
                    await self.disconnect()

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
            profile = self._resolve_profile(ble_device)
            client = await self._ensure_connected(ble_device)
            printer = self._make_client(client, profile)

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

            self._is_printing = True
            self._print_start = time.time()
            self._print_end = None
            self._notify_printing()

            try:
                await printer.start()
                # Ask before sending: a fault now means the raster would only
                # be discarded, and the error surfaces immediately instead of
                # after the whole job has been pushed.
                state = await printer.query_state()
                if state is not None and state.fault:
                    raise PrinterError(state.fault)
                try:
                    await printer.print_job(job, bitmap.height * copies, on_progress)
                except CatPrinterError as err:
                    if err.code not in (ErrorCode.STALLED, ErrorCode.TIMEOUT):
                        raise
                    # The printer went quiet mid-job. It does not push status
                    # on its own, and a stalled command queue does not answer
                    # queries either, so reconnect and ask on a clean link to
                    # name the cause.
                    await printer.stop()
                    fault = await self._diagnose(ble_device)
                    if fault:
                        raise PrinterError(fault) from err
                    raise
            finally:
                await printer.stop()
                self._print_end = time.time()
                self._is_printing = False
                self._notify_printing()
                if not self.keep_connection:
                    await self.disconnect()

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
        """Drop the connection, reconnect and read the status once."""
        await self.disconnect()
        try:
            client = await self._ensure_connected(ble_device)
            printer = self._make_client(client, self.profile)  # type: ignore[arg-type]
            try:
                await printer.start()
                state = await printer.query_state()
            finally:
                await printer.stop()
        except Exception:  # noqa: BLE001 - diagnosis is best effort
            _LOGGER.debug("Could not read status after a stalled job", exc_info=True)
            return None
        return state.fault if state is not None else None

    async def feed(self, ble_device: BLEDevice, dots: int) -> None:
        """Advance the paper without printing."""
        async with self.lock:
            profile = self._resolve_profile(ble_device)
            client = await self._ensure_connected(ble_device)
            printer = self._make_client(client, profile)
            try:
                await printer.start()
                await printer.feed(dots, profile.feed_step)
                await printer.query_state()
            finally:
                await printer.stop()
                if not self.keep_connection:
                    await self.disconnect()
