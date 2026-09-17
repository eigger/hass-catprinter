"""Shared entity plumbing."""

from __future__ import annotations

from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH
from homeassistant.helpers.entity import DeviceInfo

from .catprinter_ble import BLEData


def device_name(ble_data: BLEData) -> str:
    return f"{ble_data.name} {ble_data.identifier}"


def build_device_info(ble_data: BLEData) -> DeviceInfo:
    """Build the shared DeviceInfo so every platform registers one device."""
    return DeviceInfo(
        connections={(CONNECTION_BLUETOOTH, ble_data.address)},
        name=device_name(ble_data),
        manufacturer="Cat Printer",
        model=ble_data.model_id,
        model_id=ble_data.device_type or None,
        sw_version=ble_data.sw_version,
    )
