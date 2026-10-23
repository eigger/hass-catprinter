"""Binary sensor updates through the actual coordinator and BLE replies."""


async def test_simultaneous_conditions_and_recovery(
    hass, loaded_entry, transport, entity_id
):
    conditions = (
        "out_of_paper",
        "cover_open",
        "overheating",
        "low_battery",
        "charging",
    )
    transport.status = bytes.fromhex("1f 0d 27")
    await loaded_entry.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()
    for condition in conditions:
        assert hass.states.get(entity_id(condition, "binary_sensor")).state == "on"
    assert hass.states.get(entity_id("status")).state == "out_of_paper"

    transport.status = bytes.fromhex("00 0d 27")
    await loaded_entry.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()
    for condition in conditions:
        assert hass.states.get(entity_id(condition, "binary_sensor")).state == "off"


async def test_connection_state_tracks_kept_link_and_unload(
    hass, loaded_entry, entity_id
):
    connection = entity_id("connection", "binary_sensor")
    printing = entity_id("printing", "binary_sensor")
    assert hass.states.get(connection).state == "off"
    assert hass.states.get(printing).state == "off"
    device = loaded_entry.runtime_data.device
    device.keep_connection = True
    await loaded_entry.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(connection).state == "on"
    assert hass.states.get(connection).attributes["device_class"] == "connectivity"
    assert await hass.config_entries.async_unload(loaded_entry.entry_id)
    await hass.async_block_till_done()
    assert not device.is_connected
    assert hass.states.get(connection).state == "unavailable"
