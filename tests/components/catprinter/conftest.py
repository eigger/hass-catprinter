"""Real HA entries and deterministic external Bluetooth transport."""

from time import monotonic

import pytest
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from habluetooth import get_manager
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.catprinter.catprinter_ble import client as client_module
from custom_components.catprinter.catprinter_ble import protocol

from .test_client import FakeClient, reply

ADDRESS = "AA:BB:CC:DD:EE:FF"


class PrinterTransport(FakeClient):
    """Emulate only the device GATT boundary, keeping session/protocol code real."""

    def __init__(self):
        super().__init__()
        self.is_connected = False
        self.connections = 0
        self.disconnects = 0
        self.silent = False
        self.fail_connect = False
        self.status = bytes.fromhex("00 0d 27")

    async def connect(self, *_args, **_kwargs):
        if self.fail_connect:
            from blesession import ConnectFailed

            raise ConnectFailed("test printer unavailable")
        self.connections += 1
        self.is_connected = True
        return self

    async def disconnect(self):
        self.disconnects += 1
        self.is_connected = False

    async def write_gatt_char(self, uuid, data, response=False):
        await super().write_gatt_char(uuid, data, response)
        if self.silent:
            return
        packet = bytes(data)
        if packet == protocol.cmd_get_state() or packet.endswith(
            protocol.cmd_get_state()
        ):
            self.push(reply(0xA3, self.status))


@pytest.fixture
def transport(monkeypatch):
    device = PrinterTransport()
    monkeypatch.setattr("blesession.session.establish_connection", device.connect)
    monkeypatch.setattr(client_module, "QUERY_TIMEOUT", 0.01)
    return device


@pytest.fixture
async def advertisement(hass, enable_bluetooth):
    """Feed a scan result through the actual HA Bluetooth manager."""
    device = BLEDevice(
        ADDRESS, "X6h-0000", {"path": "/org/bluez/hci0/dev_AA"}, rssi=-55
    )
    advertisement_data = AdvertisementData(
        local_name="X6h-0000",
        manufacturer_data={},
        service_data={},
        service_uuids=["0000ae30-0000-1000-8000-00805f9b34fb"],
        tx_power=None,
        rssi=-55,
        platform_data=(),
    )
    info = BluetoothServiceInfoBleak.from_scan(
        "00:00:00:00:00:01", device, advertisement_data, monotonic(), True
    )
    get_manager().scanner_adv_received(info)
    await hass.async_block_till_done()
    return info


@pytest.fixture
def entry(hass):
    config = MockConfigEntry(
        domain="catprinter",
        unique_id=ADDRESS,
        title="X6h-0000",
        data={"address": ADDRESS, "model": "X6h", "interval_ms": 0},
    )
    config.add_to_hass(hass)
    return config


@pytest.fixture
async def loaded_entry(hass, entry, transport, advertisement):
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


@pytest.fixture
def entity_id(hass):
    from homeassistant.helpers import entity_registry as er

    def lookup(suffix, domain="sensor"):
        entities = er.async_entries_for_config_entry(
            er.async_get(hass),
            next(e.entry_id for e in hass.config_entries.async_entries("catprinter")),
        )
        return next(
            e.entity_id
            for e in entities
            if e.domain == domain and e.unique_id.endswith("_" + suffix)
        )

    return lookup
