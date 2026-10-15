"""Runtime data shared by the platforms and the services."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .catprinter_ble import BLEData, CatPrinterDevice
from .const import PRINT_LOCK, ImageAndBLEData


@dataclass
class CatPrinterRuntimeData:
    """Everything one loaded config entry owns."""

    coordinator: DataUpdateCoordinator[BLEData]
    image_coordinator: DataUpdateCoordinator[ImageAndBLEData]
    device: CatPrinterDevice


type CatPrinterConfigEntry = ConfigEntry[CatPrinterRuntimeData]


def get_print_lock(hass: HomeAssistant) -> asyncio.Lock:
    """Return the domain-wide print lock, creating it on first use.

    One lock for every printer: overlapping BLE jobs contend for the same
    adapter and for an ESP32 proxy's three connection slots.
    """
    return hass.data.setdefault(PRINT_LOCK, asyncio.Lock())
