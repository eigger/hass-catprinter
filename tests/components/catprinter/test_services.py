"""Real registered HA actions, image rendering and BLE writes."""

import base64
import io

import pytest
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.setup import async_setup_component
from PIL import Image


async def test_services_without_printer(hass, enable_bluetooth):
    assert await async_setup_component(hass, "catprinter", {})
    with pytest.raises(ServiceValidationError, match="No cat printer"):
        await hass.services.async_call("catprinter", "feed", {}, blocking=True)


async def test_preview_and_print(hass, loaded_entry, transport, entity_id):
    entity = entity_id("last_print", "image")
    before = len(transport.writes)
    result = await hass.services.async_call(
        "catprinter",
        "print",
        {
            "preview": True,
            "height": 32,
            "payload": [{"type": "text", "value": "Hello HA", "x": 0, "y": 0}],
        },
        blocking=True,
        return_response=True,
    )
    assert len(transport.writes) == before
    image = Image.open(io.BytesIO(base64.b64decode(result["image"].split(",")[1])))
    assert image.size == (384, 32)
    assert image.convert("L").getextrema()[0] < 255
    await hass.async_block_till_done()
    assert hass.states.get(entity).state not in ("unknown", "unavailable")
    result = await hass.services.async_call(
        "catprinter",
        "print",
        {"height": 8, "payload": [], "entity_id": entity},
        blocking=True,
        return_response=True,
    )
    assert result["status"] == "ok"
    assert len(transport.writes) > before
    assert not loaded_entry.runtime_data.device.is_printing
    assert hass.states.get(entity_id("printing", "binary_sensor")).state == "off"


async def test_feed_and_transport_error(hass, loaded_entry, transport, entity_id):
    await hass.services.async_call("catprinter", "feed", {"dots": 48}, blocking=True)
    assert transport.writes
    transport.fail_connect = True
    with pytest.raises(HomeAssistantError, match="Failed to feed"):
        await hass.services.async_call("catprinter", "feed", {}, blocking=True)
    assert hass.states.get(entity_id("error_count")).state == "1"
    assert not loaded_entry.runtime_data.device.is_connected


async def test_invalid_render_payload(hass, loaded_entry):
    with pytest.raises(ServiceValidationError, match="Failed to create image"):
        await hass.services.async_call(
            "catprinter",
            "print",
            {"preview": True, "height": -1, "payload": []},
            blocking=True,
        )


async def test_preview_renders_datamatrix_extra(hass, loaded_entry):
    result = await hass.services.async_call(
        "catprinter",
        "print",
        {
            "preview": True,
            "height": 96,
            "payload": [
                {"type": "datamatrix", "x": 0, "y": 0, "data": "HA test", "width": 64}
            ],
        },
        blocking=True,
        return_response=True,
    )
    image = Image.open(io.BytesIO(base64.b64decode(result["image"].split(",")[1])))
    assert image.size == (384, 96)
    assert image.convert("L").getextrema() == (0, 255)
