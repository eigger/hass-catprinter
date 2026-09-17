"""Cat printer (``51 78`` protocol) BLE layer. See ``docs/protocol.md``."""

from __future__ import annotations

from .client import CatPrinterClient
from .device import BLEData, CatPrinterDevice
from .errors import CatPrinterError, ErrorCode, PrinterError, UnsupportedDeviceError
from .imaging import Bitmap1bpp, fit_to_printhead, to_raster
from .models import (
    DEFAULT_DENSITY,
    DENSITY_MAX,
    DENSITY_MIN,
    DeviceProfile,
    advertisement_contradicts,
    all_name_prefixes,
    find_profile_by_name,
    get_profile,
    registered_profiles,
)
from .protocol import FAULT_STATUSES, STATUS_BITS, DeviceState, JobParams, PrintMode

__all__ = [
    "BLEData",
    "Bitmap1bpp",
    "CatPrinterClient",
    "CatPrinterDevice",
    "CatPrinterError",
    "DEFAULT_DENSITY",
    "DENSITY_MAX",
    "DENSITY_MIN",
    "DeviceProfile",
    "DeviceState",
    "ErrorCode",
    "FAULT_STATUSES",
    "JobParams",
    "PrintMode",
    "PrinterError",
    "STATUS_BITS",
    "UnsupportedDeviceError",
    "advertisement_contradicts",
    "all_name_prefixes",
    "find_profile_by_name",
    "fit_to_printhead",
    "get_profile",
    "registered_profiles",
    "to_raster",
]
