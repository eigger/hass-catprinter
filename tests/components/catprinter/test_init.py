"""Load and unload the actual integration and all declared platforms."""

from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import entity_registry as er


async def test_setup_and_unload(hass, loaded_entry, transport, entity_id):
    entry = loaded_entry
    assert entry.state is ConfigEntryState.LOADED
    assert hass.states.get(entity_id("battery")).state != "unknown"
    assert hass.states.get(entity_id("status")).state == "ok"
    assert hass.states.get(entity_id("out_of_paper", "binary_sensor")).state == "off"
    assert hass.states.get(entity_id("last_print", "image")) is not None
    entities = er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
    assert len({e.device_id for e in entities}) == 1
    assert transport.disconnects > 0
    device = entry.runtime_data.device
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED
    assert not device._printing_listeners
    assert not device._connection_listeners
    assert not device.is_connected


async def test_reload_closes_kept_connection(hass, loaded_entry, transport):
    original = loaded_entry.runtime_data.device
    original.keep_connection = True
    await loaded_entry.runtime_data.coordinator.async_refresh()
    assert original.is_connected
    assert await hass.config_entries.async_reload(loaded_entry.entry_id)
    await hass.async_block_till_done()
    assert not original.is_connected
    assert loaded_entry.runtime_data.device is not original


async def test_failed_poll_retains_state_and_recovers(
    hass, loaded_entry, transport, entity_id
):
    state = hass.states.get(entity_id("battery")).state
    transport.silent = True
    await loaded_entry.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(entity_id("battery")).state == state
    assert hass.states.get(entity_id("error_count")).state == "1"
    assert hass.states.get(entity_id("last_failure")).state not in (
        "unknown",
        "unavailable",
    )
    transport.silent = False
    transport.status = bytes.fromhex("01 00 27")
    await loaded_entry.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(entity_id("status")).state == "out_of_paper"
    assert hass.states.get(entity_id("out_of_paper", "binary_sensor")).state == "on"


async def test_initial_connection_failure_is_recoverable(
    hass, entry, advertisement, transport
):
    transport.fail_connect = True
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED
    assert entry.runtime_data.device.ble_data.sensors["status"] is None
    transport.fail_connect = False
    await entry.runtime_data.coordinator.async_refresh()
    assert entry.runtime_data.device.ble_data.sensors["status"] == "ok"


async def test_expected_poll_failures_are_quiet_and_redacted(
    hass, loaded_entry, transport, caplog, entity_id
):
    import logging

    from bleak.exc import BleakError

    async def denied(*args, **kwargs):
        raise BleakError("No route to AA:BB:CC:DD:EE:FF")

    transport.write_gatt_char = denied
    with caplog.at_level(logging.DEBUG, logger="custom_components.catprinter"):
        for _ in range(2):
            await loaded_entry.runtime_data.coordinator.async_refresh()
        await hass.async_block_till_done()
    own_logs = [r for r in caplog.records if r.name == "custom_components.catprinter"]
    assert not [r for r in own_logs if r.levelno >= logging.WARNING]
    assert all("AA:BB:CC:DD:EE:FF" not in r.getMessage() for r in own_logs)
    assert "AA:BB:CC:DD:EE:FF" not in str(
        hass.states.get(entity_id("last_failure")).attributes
    )


async def test_failed_platform_setup_releases_kept_link(
    hass, entry, advertisement, transport, monkeypatch
):
    from homeassistant.const import Platform

    from custom_components import catprinter

    hass.config_entries.async_update_entry(entry, options={"keep_connection": True})
    monkeypatch.setattr(
        catprinter,
        "PLATFORMS",
        [Platform.SENSOR, Platform.IMAGE, "invalid_catprinter_platform"],
    )
    assert not await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.SETUP_ERROR
    assert transport.connections == 1
    assert transport.disconnects == 1
    assert not transport.is_connected
    device = entry.runtime_data.device
    assert not device._connection_listeners
    assert not device._printing_listeners
    assert not entry.update_listeners


async def test_cancelled_setup_releases_kept_link(
    hass, entry, advertisement, transport
):
    import asyncio

    hass.config_entries.async_update_entry(entry, options={"keep_connection": True})
    started = asyncio.Event()
    original = transport.write_gatt_char

    async def wait_for_cancellation(uuid, data, response=False):
        started.set()
        await asyncio.Event().wait()
        await original(uuid, data, response)

    transport.write_gatt_char = wait_for_cancellation
    task = asyncio.create_task(hass.config_entries.async_setup(entry.entry_id))
    await started.wait()
    task.cancel()
    # HA versions may absorb setup cancellation into a failed setup result.
    try:
        await task
    except asyncio.CancelledError:
        pass
    await hass.async_block_till_done()
    assert transport.connections == 1
    assert transport.disconnects == 1
    assert not transport.is_connected
    assert not entry.update_listeners


async def test_gatt_service_change_recovers_on_fresh_connection(
    hass, loaded_entry, transport, entity_id
):
    device = loaded_entry.runtime_data.device
    device.keep_connection = True
    await loaded_entry.runtime_data.coordinator.async_refresh()
    assert device.is_connected
    original_services = transport.services
    transport.services = type(original_services)(get_service=lambda uuid: None)
    previous = hass.states.get(entity_id("battery")).state
    await loaded_entry.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(entity_id("battery")).state == previous
    assert hass.states.get(entity_id("error_count")).state == "1"
    assert not transport.is_connected
    transport.services = original_services
    transport.status = bytes.fromhex("01 00 27")
    await loaded_entry.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(entity_id("status")).state == "out_of_paper"
    assert transport.is_connected
    assert transport.connections >= 3


async def test_cancelled_print_releases_link_and_updates_entities(
    hass, loaded_entry, advertisement, transport, entity_id
):
    import asyncio

    import pytest
    from PIL import Image

    device = loaded_entry.runtime_data.device
    device.keep_connection = True
    started = asyncio.Event()

    async def stalled_write(uuid, data, response=False):
        started.set()
        await asyncio.Event().wait()

    transport.write_gatt_char = stalled_write
    task = asyncio.create_task(
        device.print_image(advertisement.device, Image.new("1", (384, 8)))
    )
    await started.wait()
    await hass.async_block_till_done()
    assert hass.states.get(entity_id("printing", "binary_sensor")).state == "on"
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    await hass.async_block_till_done()
    assert not device.is_printing
    assert not device.is_connected
    assert not device.lock.locked()
    assert hass.states.get(entity_id("printing", "binary_sensor")).state == "off"
    assert hass.states.get(entity_id("connection", "binary_sensor")).state == "off"
    assert hass.states.get(entity_id("error_count")).state == "0"
