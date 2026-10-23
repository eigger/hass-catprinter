"""Services of the cat printer integration: ``catprinter.print`` and ``catprinter.feed``."""

from __future__ import annotations

import base64
import io

import voluptuous as vol
from homeassistant.components import bluetooth
from homeassistant.components.image import Image
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import ATTR_AREA_ID, ATTR_DEVICE_ID, ATTR_ENTITY_ID
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
    callback,
)
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .catprinter_ble import CatPrinterDevice
from .const import DOMAIN, EXPECTED_ERRORS
from .data import CatPrinterConfigEntry, get_print_lock
from .render import render_image

SERVICE_PRINT = "print"
SERVICE_FEED = "feed"

# Keep device-specific options and target fields unchanged. imagespec validates
# the contents of the native element list used by the action editor.
PRINT_SCHEMA = vol.Schema(
    {
        vol.Optional("payload"): list,
        vol.Optional("preview"): cv.boolean,
    },
    extra=vol.ALLOW_EXTRA,
)


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Register the services. Called once from ``async_setup``."""

    async def print_service(service: ServiceCall) -> ServiceResponse:
        entries = _resolve_target_entries(hass, service)
        results = [await _print_on_entry(hass, entry, service) for entry in entries]
        if len(results) == 1:
            return results[0]
        return {"results": results}

    async def feed_service(service: ServiceCall) -> None:
        for entry in _resolve_target_entries(hass, service):
            await _feed_on_entry(hass, entry, int(service.data.get("dots", 96)))

    hass.services.async_register(
        DOMAIN,
        SERVICE_PRINT,
        print_service,
        schema=PRINT_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(DOMAIN, SERVICE_FEED, feed_service)


def _require_loaded(entry: CatPrinterConfigEntry) -> None:
    """Refuse a printer that was unloaded while an earlier target was running."""
    if entry.state is not ConfigEntryState.LOADED:
        raise HomeAssistantError(f"Printer {entry.title} is no longer loaded")


def _ble_device_for(hass: HomeAssistant, device: CatPrinterDevice):
    ble_device = bluetooth.async_ble_device_from_address(hass, device.address)
    if ble_device is None:
        raise HomeAssistantError(
            f"Could not find printer {device.address} on your Bluetooth network"
        )
    return ble_device


async def _print_on_entry(
    hass: HomeAssistant, entry: CatPrinterConfigEntry, service: ServiceCall
) -> dict:
    """Render and print one image on one configured printer."""
    _require_loaded(entry)
    runtime = entry.runtime_data
    coordinator = runtime.coordinator
    device = runtime.device

    try:
        image = await hass.async_add_executor_job(
            render_image, entry.entry_id, service, hass, device.ble_data.printhead_px
        )
    except Exception as err:
        raise ServiceValidationError(f"Failed to create image: {err}") from err

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    png = buffer.getvalue()
    runtime.image_coordinator.async_set_updated_data(
        (Image(content_type="image/png", content=png), coordinator.data)
    )
    image_data = f"data:image/png;base64,{base64.b64encode(png).decode('ascii')}"

    if service.data.get("preview"):
        return {"image": image_data}

    ble_device = _ble_device_for(hass, device)
    data = service.data
    async with get_print_lock(hass):
        try:
            result = await device.print_image(
                ble_device,
                image,
                mode=data.get("mode", "image"),
                density=int(data.get("density", 4)),
                energy=int(data["energy"]) if "energy" in data else None,
                speed=int(data["speed"]) if "speed" in data else None,
                feed_dots=int(data["feed"]) if "feed" in data else None,
                copies=int(data.get("copies", 1)),
            )
        except EXPECTED_ERRORS as err:
            raise HomeAssistantError(f"Failed to print: {err}") from err
        finally:
            # The job (or its failure diagnosis) refreshed the status; show it
            # whether or not the print went through.
            coordinator.async_set_updated_data(device.ble_data)

    result["image"] = image_data
    return result


async def _feed_on_entry(
    hass: HomeAssistant, entry: CatPrinterConfigEntry, dots: int
) -> None:
    _require_loaded(entry)
    runtime = entry.runtime_data
    device = runtime.device
    ble_device = _ble_device_for(hass, device)
    async with get_print_lock(hass):
        try:
            await device.feed(ble_device, dots)
        except EXPECTED_ERRORS as err:
            raise HomeAssistantError(f"Failed to feed: {err}") from err
        finally:
            # The feed reads the status afterwards; show it like a print does.
            runtime.coordinator.async_set_updated_data(device.ble_data)


def _as_id_list(value) -> list[str]:
    if not value:
        return []
    if isinstance(value, str):
        return [value]
    return list(value)


def _resolve_target_entries(
    hass: HomeAssistant, service: ServiceCall
) -> list[CatPrinterConfigEntry]:
    """Work out which loaded printers a service call is aimed at."""
    loaded: dict[str, CatPrinterConfigEntry] = {
        entry.entry_id: entry
        for entry in hass.config_entries.async_loaded_entries(DOMAIN)
    }
    if not loaded:
        raise ServiceValidationError("No cat printer is configured")

    device_registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)

    device_ids = set(_as_id_list(service.data.get(ATTR_DEVICE_ID)))
    for area_id in _as_id_list(service.data.get(ATTR_AREA_ID)):
        device_ids.update(
            device.id for device in dr.async_entries_for_area(device_registry, area_id)
        )
    for entity_id in _as_id_list(service.data.get(ATTR_ENTITY_ID)):
        if (entity := entity_registry.async_get(entity_id)) and entity.device_id:
            device_ids.add(entity.device_id)

    entry_ids = [
        entry_id
        for device_id in sorted(device_ids)
        if (registry_entry := device_registry.async_get(device_id))
        for entry_id in registry_entry.config_entries
        if entry_id in loaded
    ]

    if entry_ids:
        return [loaded[entry_id] for entry_id in dict.fromkeys(entry_ids)]
    if len(loaded) == 1:
        return list(loaded.values())
    raise ServiceValidationError(
        "Select which printer to print on -- more than one is configured"
    )
