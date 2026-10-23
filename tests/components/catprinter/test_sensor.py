"""Sensor states and registry metadata from the loaded HA platform."""

from homeassistant.helpers import entity_registry as er


async def test_status_and_battery_follow_device_poll(
    hass, loaded_entry, transport, entity_id
):
    battery_id = entity_id("battery")
    battery = hass.states.get(battery_id)
    assert battery.state == "83"
    assert battery.attributes["device_class"] == "battery"
    assert battery.attributes["unit_of_measurement"] == "%"
    assert battery.attributes["state_class"] == "measurement"
    registry = er.async_get(hass)
    assert registry.async_get(battery_id).config_entry_id == loaded_entry.entry_id
    assert (
        registry.async_get(entity_id("label_sensor")).disabled_by
        is er.RegistryEntryDisabler.INTEGRATION
    )

    transport.status = bytes.fromhex("02 0d 28")
    await loaded_entry.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(battery_id).state == "100"
    assert hass.states.get(entity_id("status")).state == "cover_open"
    assert hass.states.get(entity_id("conditions")).state == "cover_open"


async def test_session_failure_sensor_recovers_without_losing_diagnostics(
    hass, loaded_entry, transport, entity_id
):
    assert hass.states.get(entity_id("error_count")).state == "0"
    transport.fail_connect = True
    import pytest
    from homeassistant.exceptions import HomeAssistantError

    with pytest.raises(HomeAssistantError, match="Failed to feed"):
        await hass.services.async_call("catprinter", "feed", {}, blocking=True)
    await hass.async_block_till_done()
    failure = hass.states.get(entity_id("last_failure"))
    assert failure.state not in ("unknown", "unavailable")
    assert failure.attributes["device_class"] == "timestamp"
    assert hass.states.get(entity_id("error_count")).state == "1"

    transport.fail_connect = False
    await hass.services.async_call("catprinter", "feed", {}, blocking=True)
    await hass.async_block_till_done()
    assert hass.states.get(entity_id("last_failure")).state == failure.state
    assert hass.states.get(entity_id("error_count")).state == "1"
