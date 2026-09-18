"""Constants for the cat printer BLE integration."""

from __future__ import annotations

import base64

from homeassistant.components.image import Image

from .catprinter_ble import BLEData

DOMAIN = "catprinter"

#: Domain-wide print lock, kept outside ``hass.data[DOMAIN]`` so that dict stays
#: a clean entry_id -> runtime mapping.
PRINT_LOCK = f"{DOMAIN}_print_lock"

#: Model chosen by hand when a printer's advertised name matches no profile.
CONF_MODEL = "model"

CONF_POLL_MINUTES = "poll_minutes"
CONF_KEEP_CONNECTION = "keep_connection"
CONF_INTERVAL_MS = "interval_ms"
CONF_PACKET_SIZE_CAP = "packet_size_cap"

#: The printer stays on and reachable for at least an hour while idle, so a
#: 15-minute status poll costs little battery and keeps the sensors fresh.
DEFAULT_POLL_MINUTES = 15
DEFAULT_KEEP_CONNECTION = False

#: 0 means "use the value from the device profile" (2-6 ms for most models).
DEFAULT_INTERVAL_MS = 0

#: Hard ceiling on packet size regardless of what the printer's profile says.
#: The profile MTU (63-183) and the negotiated MTU are the other two limits;
#: whichever is smallest wins.
DEFAULT_PACKET_SIZE_CAP = 180

#: 384x40 white PNG shown by the image entity until something is printed.
EMPTY_PNG: bytes = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAYAAAAAoAQAAAADfhBAlAAAANklEQVR4nO3QoREAMAzDwFT779xS"
    "Q4X2/FgmPnd2WPbTgYGqQgcGqgodGKgqdGCgqtCB8cNLD9m5AU9GnP9FAAAAAElFTkSuQmCC"
)

ImageAndBLEData = tuple[Image, BLEData]
