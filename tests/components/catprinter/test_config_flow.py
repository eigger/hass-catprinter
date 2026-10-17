"""Exercise the actual HA flow manager and duplicate validation."""

from homeassistant.config_entries import SOURCE_BLUETOOTH, SOURCE_USER
from homeassistant.data_entry_flow import FlowResultType


async def test_bluetooth_confirmation(hass, advertisement, transport):
    result = await hass.config_entries.flow.async_init(
        "catprinter",
        context={"source": SOURCE_BLUETOOTH},
        data=advertisement,
    )
    if (
        result["type"] is FlowResultType.ABORT
        and result["reason"] == "already_in_progress"
    ):
        # Older HA automatically starts the same discovery flow when the scan
        # arrives. Continue that real prompt rather than duplicating it.
        progress = hass.config_entries.flow.async_progress_by_handler("catprinter")
        assert len(progress) == 1
        result = await hass.config_entries.flow.async_configure(progress[0]["flow_id"])
    assert result["type"] is FlowResultType.FORM, result
    assert result["step_id"] == "bluetooth_confirm"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "poll_minutes": 5,
            "keep_connection": False,
        },
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id == advertisement.address
    assert result["result"].runtime_data.device.ble_data.sensors["status"] == "ok"


async def test_bluetooth_duplicate(hass, entry, advertisement):
    result = await hass.config_entries.flow.async_init(
        "catprinter",
        context={"source": SOURCE_BLUETOOTH},
        data=advertisement,
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_unsupported_discovery(hass, enable_bluetooth, advertisement):
    from time import monotonic

    from bleak.backends.device import BLEDevice
    from bleak.backends.scanner import AdvertisementData
    from homeassistant.components.bluetooth import BluetoothServiceInfoBleak

    info = BluetoothServiceInfoBleak.from_scan(
        "00:00:00:00:00:01",
        BLEDevice("00:11:22:33:44:55", "Unknown", {}, rssi=-60),
        AdvertisementData(
            local_name="Unknown",
            manufacturer_data={},
            service_data={},
            service_uuids=[],
            tx_power=None,
            rssi=-60,
            platform_data=(),
        ),
        monotonic(),
        True,
    )
    result = await hass.config_entries.flow.async_init(
        "catprinter",
        context={"source": SOURCE_BLUETOOTH},
        data=info,
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "not_supported"


async def test_manual_invalid_and_duplicate_address(hass, enable_bluetooth, entry):
    result = await hass.config_entries.flow.async_init(
        "catprinter", context={"source": SOURCE_USER}
    )
    assert result["step_id"] == "manual"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "address": "AA:broken",
            "model": "X6h",
            "poll_minutes": 5,
            "keep_connection": False,
        },
    )
    assert result["errors"] == {"address": "invalid_address"}
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "address": entry.unique_id.lower(),
            "model": "X6h",
            "poll_minutes": 5,
            "keep_connection": False,
        },
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_options_reload(hass, loaded_entry):
    original = loaded_entry.runtime_data.device
    result = await hass.config_entries.options.async_init(loaded_entry.entry_id)
    assert result["step_id"] == "init"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            "poll_minutes": 10,
            "keep_connection": True,
            "interval_ms": 20,
            "packet_size_cap": 100,
        },
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert loaded_entry.runtime_data.device is not original
    assert loaded_entry.runtime_data.device.keep_connection
    assert loaded_entry.options["packet_size_cap"] == 100


async def test_repeated_option_reload_has_one_listener(hass, loaded_entry):
    for minutes in (6, 7):
        result = await hass.config_entries.options.async_init(loaded_entry.entry_id)
        await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                "poll_minutes": minutes,
                "keep_connection": False,
                "interval_ms": 0,
                "packet_size_cap": 180,
            },
        )
        await hass.async_block_till_done()
        assert len(loaded_entry.update_listeners) == 1
    assert await hass.config_entries.async_unload(loaded_entry.entry_id)
    assert not loaded_entry.update_listeners
