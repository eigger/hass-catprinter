"""Sensors for cat printers."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import timedelta

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .catprinter_ble import BLEData, CatPrinterDevice
from .data import CatPrinterConfigEntry
from .entity import build_device_info, device_name

_LOGGER = logging.getLogger(__name__)

SENSORS: dict[str, SensorEntityDescription] = {
    "battery": SensorEntityDescription(
        key="battery",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "status": SensorEntityDescription(
        key="status",
        translation_key="status",
        icon="mdi:printer-alert",
        device_class=SensorDeviceClass.ENUM,
        options=["ok", "printing", "out_of_paper", "cover_open", "overheating"],
    ),
    "conditions": SensorEntityDescription(
        key="conditions",
        translation_key="conditions",
        icon="mdi:list-status",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "label_sensor": SensorEntityDescription(
        key="label_sensor",
        translation_key="label_sensor",
        icon="mdi:eye-outline",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CatPrinterConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up CatPrinter sensors."""
    coordinator = entry.runtime_data.coordinator
    device = entry.runtime_data.device

    entities: list[SensorEntity] = [
        CatPrinterSensor(coordinator, description)
        for key, description in SENSORS.items()
        if key in coordinator.data.sensors
    ]
    entities.append(CatPrinterPrintDurationSensor(coordinator, device))
    entities.append(CatPrinterLastFailureSensor(coordinator, device))
    entities.append(CatPrinterErrorCountSensor(coordinator, device))

    async_add_entities(entities)


class CatPrinterSensor(CoordinatorEntity[DataUpdateCoordinator[BLEData]], SensorEntity):
    """A value read straight from the BLEData snapshot."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[BLEData],
        entity_description: SensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = entity_description
        ble_data = coordinator.data
        self._attr_unique_id = f"{device_name(ble_data)}_{entity_description.key}"
        self._attr_device_info = build_device_info(ble_data)

    @property
    def native_value(self) -> StateType:
        return self.coordinator.data.sensors.get(self.entity_description.key)


class CatPrinterPrintDurationSensor(
    CoordinatorEntity[DataUpdateCoordinator[BLEData]], SensorEntity
):
    """How long the current or last print job took."""

    _attr_has_entity_name = True
    _attr_translation_key = "print_duration"
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[BLEData],
        device: CatPrinterDevice,
    ) -> None:
        super().__init__(coordinator)
        self._device = device
        self._unsub_timer = None
        self._unsub_printing = None
        ble_data = coordinator.data
        self._attr_unique_id = f"{device_name(ble_data)}_print_duration"
        self._attr_device_info = build_device_info(ble_data)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._unsub_printing = self._device.add_printing_listener(
            self._handle_printing_update
        )

    async def async_will_remove_from_hass(self) -> None:
        await super().async_will_remove_from_hass()
        if self._unsub_printing is not None:
            self._unsub_printing()
            self._unsub_printing = None
        self._stop_timer()

    def _start_timer(self) -> None:
        if self._unsub_timer is None:
            self._unsub_timer = async_track_time_interval(
                self.hass, self._tick, timedelta(seconds=1)
            )

    def _stop_timer(self) -> None:
        if self._unsub_timer is not None:
            self._unsub_timer()
            self._unsub_timer = None

    @callback
    def _tick(self, _now=None) -> None:
        self.async_write_ha_state()

    @callback
    def _handle_printing_update(self) -> None:
        if self._device.is_printing:
            self._start_timer()
        else:
            self._stop_timer()
        self.async_write_ha_state()

    @property
    def native_value(self) -> float:
        return round(self._device.print_duration, 1)

    @property
    def extra_state_attributes(self) -> dict:
        """Elapsed time, plus the last print's BLE session breakdown.

        The breakdown (outcome, radio, per-stage timings, likely_cause on
        failure) is left out while a job runs so the ticking state is not
        paired with the previous job.
        """
        duration = self._device.print_duration
        attrs: dict = {
            "formatted": f"{int(duration // 60):02d}:{int(duration % 60):02d}",
            "is_printing": self._device.is_printing,
        }
        report = self._device.reports.of("print")
        if not self._device.is_printing and report:
            attrs.update(report)
        return attrs


class _SessionReportSensor(
    CoordinatorEntity[DataUpdateCoordinator[BLEData]], SensorEntity
):
    """Base for sensors that follow ``device.reports`` rather than the poll."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _key: str

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[BLEData],
        device: CatPrinterDevice,
    ) -> None:
        super().__init__(coordinator)
        self._device = device
        self._remove_listener: Callable[[], None] = lambda: None
        ble_data = coordinator.data
        self._attr_unique_id = f"{device_name(ble_data)}_{self._key}"
        self._attr_device_info = build_device_info(ble_data)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._remove_listener = self._device.reports.add_listener(self._handle_report)

    async def async_will_remove_from_hass(self) -> None:
        await super().async_will_remove_from_hass()
        self._remove_listener()
        self._remove_listener = lambda: None

    @callback
    def _handle_report(self) -> None:
        self.async_write_ha_state()


class CatPrinterLastFailureSensor(_SessionReportSensor):
    """When a BLE session last failed, with that session's breakdown.

    Kept until the next failure so a later success does not erase the
    evidence. A status poll that never connects is left out: the printer is
    often off or asleep, and counting it would replace the last real failure
    on every scan.
    """

    _key = "last_failure"
    _attr_translation_key = "last_failure"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:clock-alert-outline"

    @property
    def native_value(self):
        return self._device.reports.last_failure_at

    @property
    def extra_state_attributes(self) -> dict | None:
        return self._device.reports.last_failure


class CatPrinterErrorCountSensor(_SessionReportSensor):
    """How many BLE sessions have failed since this entry was loaded.

    Starts over (at 0) on every reload; the recorder treats that as a counter
    reset. A poll that fails before the link is up is not counted; a print failure, or a
    poll that connected and then failed, is.
    """

    _key = "error_count"
    _attr_translation_key = "error_count"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:alert-circle-outline"

    @property
    def native_value(self) -> int:
        return self._device.reports.failures
