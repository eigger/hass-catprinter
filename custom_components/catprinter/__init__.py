"""The cat printer BLE integration."""

from __future__ import annotations

import contextlib
import logging
from datetime import timedelta

from bleak_retry_connector import close_stale_connections_by_address
from blesession import SessionTrace, fallback_report
from homeassistant.components import bluetooth
from homeassistant.components.image import Image
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .catprinter_ble import BLEData, CatPrinterDevice
from .const import (
    CONF_INTERVAL_MS,
    CONF_KEEP_CONNECTION,
    CONF_MODEL,
    CONF_PACKET_SIZE_CAP,
    CONF_POLL_MINUTES,
    DEFAULT_INTERVAL_MS,
    DEFAULT_KEEP_CONNECTION,
    DEFAULT_PACKET_SIZE_CAP,
    DEFAULT_POLL_MINUTES,
    DOMAIN,
    EMPTY_PNG,
    EXPECTED_ERRORS,
    ImageAndBLEData,
)
from .data import CatPrinterConfigEntry, CatPrinterRuntimeData, get_print_lock
from .services import async_setup_services
from .session_report import build_session_report, redact_addresses, redact_report

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.IMAGE, Platform.BINARY_SENSOR]

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

#: How long unloading waits for a running operation before giving up on closing
#: its link.
UNLOAD_WAIT_S = 30.0


def _option(entry: ConfigEntry, key: str, default):
    return entry.options.get(key, entry.data.get(key, default))


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the domain services; they outlive any single config entry."""
    async_setup_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: CatPrinterConfigEntry) -> bool:
    """Set up a cat printer from a config entry."""
    address = entry.unique_id
    assert address is not None

    poll_minutes = float(_option(entry, CONF_POLL_MINUTES, DEFAULT_POLL_MINUTES))
    keep_connection = bool(
        _option(entry, CONF_KEEP_CONNECTION, DEFAULT_KEEP_CONNECTION)
    )
    interval_ms = int(_option(entry, CONF_INTERVAL_MS, DEFAULT_INTERVAL_MS))
    packet_size_cap = int(_option(entry, CONF_PACKET_SIZE_CAP, DEFAULT_PACKET_SIZE_CAP))

    await close_stale_connections_by_address(address)

    device = CatPrinterDevice(
        address,
        model_id=entry.data.get(CONF_MODEL),
        keep_connection=keep_connection,
        interval_ms=interval_ms or None,
        packet_size_cap=packet_size_cap,
    )

    def _publish_session_report(
        operation: str, trace: SessionTrace, outcome: BaseException | None
    ) -> None:
        """Freeze this session's report once and file it.

        ``radio_facts`` reads RSSI and path count live, so only the trace that
        just finished is rendered. A report that cannot be built is replaced
        by ``fallback_report`` so the session is still counted.
        """
        try:
            report = build_session_report(
                hass, address, operation=operation, trace=trace, exc=outcome
            )
        except Exception as err:  # noqa: BLE001 - diagnostics must not mask the outcome
            _LOGGER.debug("Building the session report failed: %s", err)
            report = fallback_report(operation, trace=trace, exc=outcome)
        device.reports.record(redact_report(report))

    device.callback_session = _publish_session_report

    async def _async_update_method() -> BLEData:
        ble_device = bluetooth.async_ble_device_from_address(hass, address)
        if ble_device is None:
            _LOGGER.debug("Printer is not currently visible; keeping last known data")
            return device.ble_data
        print_lock = get_print_lock(hass)
        if device.lock.locked() or print_lock.locked():
            # A print (or feed) holds this device, or another printer's job
            # holds the adapter / proxy slots. A print refreshes status itself
            # via the trailing A3, so queueing a connection behind it only adds
            # a reconnect right after the job. The lock is only looked at, not
            # taken: a printer that is off would hold it through the whole
            # connect attempt and stall every other printer's prints.
            _LOGGER.debug("Printer or the adapter is busy; skipping this poll")
            with contextlib.suppress(*EXPECTED_ERRORS):
                device.prepare(ble_device)  # names the entities without a connection
            return device.ble_data
        try:
            return await device.update_device(ble_device)
        except Exception as err:  # noqa: BLE001 - never let polling kill the entry
            _LOGGER.debug(
                "Unable to poll printer: %s; keeping last known data",
                redact_addresses(str(err)),
            )
            return device.ble_data

    coordinator: DataUpdateCoordinator[BLEData] = DataUpdateCoordinator(
        hass,
        _LOGGER,
        config_entry=entry,
        name=DOMAIN,
        update_method=_async_update_method,
        update_interval=timedelta(minutes=poll_minutes),
    )
    coordinator.data = device.ble_data
    try:
        await coordinator.async_refresh()
        if not coordinator.last_update_success:
            _LOGGER.warning(
                "Initial update failed; entities start unavailable: %s",
                redact_addresses(str(coordinator.last_exception)),
            )

        image_coordinator: DataUpdateCoordinator[ImageAndBLEData] = (
            DataUpdateCoordinator(hass, _LOGGER, config_entry=entry, name=DOMAIN)
        )
        image_coordinator.async_set_updated_data(
            (Image(content_type="image/png", content=EMPTY_PNG), coordinator.data)
        )

        entry.runtime_data = CatPrinterRuntimeData(
            coordinator=coordinator,
            image_coordinator=image_coordinator,
            device=device,
        )

        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except BaseException:
        # Failed or cancelled setup can leave a keep_connection link and
        # partially forwarded entities behind. Roll those back before HA
        # marks the entry failed; ordinary unload is not called in that path.
        try:
            await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
        except Exception as err:  # noqa: BLE001 - preserve the setup failure
            _LOGGER.debug(
                "Unable to roll back printer platforms: %s", redact_addresses(str(err))
            )
        finally:
            await _async_close_device(hass, entry, device)
        raise
    entry.async_on_unload(entry.add_update_listener(_async_update_options))
    return True


async def _async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload options using the public API available at the supported HA floor."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: CatPrinterConfigEntry) -> bool:
    """Unload a config entry."""
    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return False

    await _async_close_device(hass, entry, entry.runtime_data.device)
    return True


async def _async_close_device(
    hass: HomeAssistant, entry: CatPrinterConfigEntry, device: CatPrinterDevice
) -> None:
    """Release the link on both normal unload and failed/cancelled setup."""
    # An operation already running read keep_connection when it started and
    # may leave its link up. Wait for it (bounded), then close that link, so
    # an unloaded entry does not keep holding a proxy connection slot.
    if not await device.close(UNLOAD_WAIT_S):
        _LOGGER.warning(
            "A printer operation is still running; its link will be closed when it ends",
        )
        # Not an entry background task: those are cancelled the moment the
        # unload returns, before this one could get the lock.
        hass.async_create_background_task(
            device.close_when_idle(), f"{DOMAIN}_close_{entry.entry_id}"
        )
