"""Real HA entries and deterministic external Bluetooth transport."""

# <!-- hass-standards:domain-fixtures:start -->
# Use pytest_homeassistant_custom_component.common.MockConfigEntry for
# mock_config_entry when the integration uses config entries.
# Define mock_client only when an external communication client is present.
# Mock external communication boundaries, never Home Assistant core modules.
# Keep integration-specific fixtures below this managed block.
# <!-- hass-standards:domain-fixtures:end -->

from functools import partial
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
def mock_client(monkeypatch):
    device = PrinterTransport()
    monkeypatch.setattr("blesession.session.establish_connection", device.connect)
    monkeypatch.setattr(client_module, "QUERY_TIMEOUT", 0.01)
    return device


@pytest.fixture
def transport(mock_client):
    """Keep the existing transport fixture interface for regression tests."""
    return mock_client


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
def mock_config_entry(hass):
    config = MockConfigEntry(
        domain="catprinter",
        unique_id=ADDRESS,
        title="X6h-0000",
        data={"address": ADDRESS, "model": "X6h", "interval_ms": 0},
    )
    config.add_to_hass(hass)
    return config


@pytest.fixture
def entry(mock_config_entry):
    """Keep the existing entry fixture interface for regression tests."""
    return mock_config_entry


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


@pytest.fixture
async def payload_example_setup(hass, loaded_entry, entity_id):
    """Load the real printer and give its registered image the documented ID."""
    from homeassistant.helpers import entity_registry as er

    registry = er.async_get(hass)
    image_id = entity_id("last_print", "image")
    if image_id != "image.cat_printer_last_print":
        registry.async_update_entity(
            image_id, new_entity_id="image.cat_printer_last_print"
        )
        await hass.async_block_till_done()
    assert hass.services.has_service("catprinter", "print")
    return loaded_entry


@pytest.fixture
def payload_example_adapter():
    """Bind the production renderer after actual HA service preparation."""

    def prepare(hass, example_metadata, normalized_action, schema_data):
        from inspect import signature

        from hass_standards_payload import PreparedPayload
        from homeassistant.core import ServiceCall

        from custom_components.catprinter.render import _make_context, render_image
        from custom_components.catprinter.services import _resolve_target_entries

        # HA added the owning hass argument after the supported minimum.
        service = ServiceCall(
            domain="catprinter",
            service="print",
            data=schema_data,
            **({"hass": hass} if "hass" in signature(ServiceCall).parameters else {}),
        )
        entry = _resolve_target_entries(hass, service)[0]
        width = entry.runtime_data.device.ble_data.printhead_px
        return PreparedPayload(
            payload=service.data.get("payload", ""),
            context=_make_context(
                hass, default_font="ppb.ttf", palette=["black", "white"]
            ),
            render_options={
                "width": width,
                "height": service.data.get("height", 240),
                "rotate": service.data.get("rotate", 0),
                "rotate_mode": "canvas",
                "background": service.data.get("background", "white"),
                "dither": False,
            },
            prepare=partial(render_image, entry.entry_id, service, hass, width),
        )

    return prepare
