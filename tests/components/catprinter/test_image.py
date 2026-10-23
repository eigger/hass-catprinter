"""Image platform state and bytes after a real preview action."""

import base64
import io

import pytest
from homeassistant.components.image.const import DATA_COMPONENT
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import service as service_helper
from PIL import Image


@pytest.fixture
def mock_recorder_before_hass(recorder_db_url):
    """Resolve the plugin's recorder database before its real hass fixture."""


async def test_preview_updates_image_without_bluetooth_writes(
    hass, loaded_entry, transport, entity_id
):
    image_id = entity_id("last_print", "image")
    image_entity = hass.data[DATA_COMPONENT].get_entity(image_id)
    initial = await image_entity.async_image()
    assert Image.open(io.BytesIO(initial)).size == (384, 40)
    before = len(transport.writes)
    hass.states.async_set("sensor.print_message", "Home Assistant")
    action = cv.SCRIPT_SCHEMA(
        [
            {
                "action": "catprinter.print",
                "target": {"entity_id": image_id},
                "data": {
                    "preview": True,
                    "height": 48,
                    "payload": [
                        {
                            "type": "text",
                            "value": "{{ states('sensor.print_message') }}",
                            "font": "rbm.ttf",
                            "x": 0,
                            "y": 0,
                        }
                    ],
                },
            }
        ]
    )[0]
    prepared = service_helper.async_prepare_call_from_config(hass, action)
    result = await hass.services.async_call(
        prepared["domain"],
        prepared["service"],
        prepared["service_data"],
        target=prepared["target"],
        blocking=True,
        return_response=True,
    )
    await hass.async_block_till_done()
    updated = await image_entity.async_image()
    assert updated == base64.b64decode(result["image"].split(",")[1])
    rendered = Image.open(io.BytesIO(updated))
    assert rendered.size == (384, 48)
    assert rendered.convert("L").getextrema() == (0, 255)
    assert updated != initial
    assert len(transport.writes) == before
    assert hass.states.get(image_id).state not in ("unknown", "unavailable")


async def test_plot_uses_real_recorder_history(recorder_mock, hass, loaded_entry):
    """Exercise the production history provider against HA's in-memory recorder."""
    from datetime import timedelta

    from homeassistant.util import dt as dt_util

    from custom_components.catprinter.render import _make_context

    hass.states.async_set(
        "sensor.plot_temperature", "21", {"unit_of_measurement": "°C"}
    )
    await hass.async_block_till_done()
    await recorder_mock.async_block_till_done()
    context = _make_context(hass, default_font="ppb.ttf", palette=["black", "white"])
    now = dt_util.utcnow()
    history = await hass.async_add_executor_job(
        context.history,
        ["sensor.plot_temperature"],
        now - timedelta(hours=1),
        now + timedelta(seconds=1),
    )
    assert history["sensor.plot_temperature"][0].state == "21"
    result = await hass.services.async_call(
        "catprinter",
        "print",
        {
            "preview": True,
            "height": 96,
            "payload": [
                {
                    "type": "plot",
                    "data": [{"entity": "sensor.plot_temperature"}],
                    "x_start": 5,
                    "y_start": 5,
                    "x_end": 370,
                    "y_end": 90,
                }
            ],
        },
        blocking=True,
        return_response=True,
    )
    rendered = Image.open(io.BytesIO(base64.b64decode(result["image"].split(",")[1])))
    assert rendered.size == (384, 96)
    assert rendered.convert("L").getextrema() == (0, 255)
