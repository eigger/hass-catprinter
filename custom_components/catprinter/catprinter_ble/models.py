"""Device profiles and the name-prefix registry.

Printers advertise as ``<model>-<hex>``; the advertised name is the one signal
for picking a profile, since the ``A8`` reply carries a device type but not
the model.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from .models_data import MODELS

#: GATT service candidates in preference order, with the write characteristic
#: for each. The notify characteristic is the first one in the matched service
#: with the NOTIFY property.
SERVICE_CANDIDATES: tuple[tuple[str, str], ...] = (
    ("0000ae30-0000-1000-8000-00805f9b34fb", "0000ae01-0000-1000-8000-00805f9b34fb"),
    ("0000ae00-0000-1000-8000-00805f9b34fb", "0000ae01-0000-1000-8000-00805f9b34fb"),
    ("0000ff00-0000-1000-8000-00805f9b34fb", "0000ff02-0000-1000-8000-00805f9b34fb"),
    ("0000ab00-0000-1000-8000-00805f9b34fb", "0000ab01-0000-1000-8000-00805f9b34fb"),
    ("0000ae80-0000-1000-8000-00805f9b34fb", "0000ae81-0000-1000-8000-00805f9b34fb"),
    ("49535343-fe7d-4ae5-8fa9-9fafd205e455", "49535343-8841-43f4-a8d4-ecbe34729bb3"),
)

#: UUIDs seen in advertisements. AF30 is what the AE30-service printers put in
#: the air (X6h confirmed); the rest are the GATT services themselves.
ADVERTISED_SERVICE_UUIDS: frozenset[str] = frozenset(
    {"0000af30-0000-1000-8000-00805f9b34fb"} | {svc for svc, _ in SERVICE_CANDIDATES}
)

#: Density slider centre; energy scales +/-15 % per step away from it.
DEFAULT_DENSITY = 4
DENSITY_MIN = 1
DENSITY_MAX = 7

_UNSUPPORTED_REASONS = {
    "auth": (
        "this model requires a D1 challenge with a per-model secret before it "
        "will print"
    ),
    "window": "this model uses a credit-window flow control that is not implemented",
}


@dataclass(frozen=True, slots=True)
class DeviceProfile:
    """Everything the client needs to talk to one model."""

    model_id: str
    name_prefix: str
    printhead_px: int
    dpi: int
    mtu: int
    can_change_mtu: bool
    interval_ms: int
    img_speed: int
    text_speed: int
    energy_thin: int
    energy_mid: int
    energy_deep: int
    energy_text: int
    rle: bool
    paper_num: int
    battery_model: int
    app_uses_spp: bool
    unsupported_reason: str = ""

    @property
    def supported(self) -> bool:
        return not self.unsupported_reason

    @property
    def packet_size(self) -> int:
        """Bytes per write, before the negotiated MTU is taken into account."""
        return (self.mtu if self.can_change_mtu else 23) - 3

    @property
    def feed_step(self) -> int:
        """Dots per ``A1``: 48 at 200 dpi, 72 at 300 dpi."""
        return 72 if self.dpi == 300 else 48

    @property
    def default_feed_dots(self) -> int:
        """Paper advanced after a job: ``paper_num`` feed steps."""
        return max(self.paper_num, 1) * self.feed_step

    def energy_for(self, mode: str, density: int) -> int | None:
        """Heater energy for a mode and 1..7 density, or None to skip ``AF``.

        Base energy scaled by 15 % per step away from the default density. A
        zero base means no energy command is sent and the printer uses its
        own default.
        """
        base = self.energy_text if mode == "text" else self.energy_mid
        if base <= 0:
            return None
        density = min(max(density, DENSITY_MIN), DENSITY_MAX)
        return int(base + (density - DEFAULT_DENSITY) * 0.15 * base)

    def speed_for(self, mode: str) -> int:
        return self.text_speed if mode == "text" else self.img_speed


def _from_row(row: tuple) -> DeviceProfile:
    (
        model_no, prefix, width, dpi, mtu, can_change_mtu, interval,
        img_speed, text_speed, e_thin, e_mid, e_deep, e_text,
        rle, paper_num, battery_model, spp, reason,
    ) = row
    return DeviceProfile(
        model_id=model_no,
        name_prefix=prefix,
        printhead_px=width,
        dpi=dpi,
        mtu=mtu,
        can_change_mtu=can_change_mtu,
        interval_ms=interval,
        img_speed=img_speed,
        text_speed=text_speed,
        energy_thin=e_thin,
        energy_mid=e_mid,
        energy_deep=e_deep,
        energy_text=e_text,
        rle=rle,
        paper_num=paper_num,
        battery_model=battery_model,
        app_uses_spp=spp,
        unsupported_reason=_UNSUPPORTED_REASONS.get(reason, reason),
    )


_PROFILES: list[DeviceProfile] = [_from_row(row) for row in MODELS]
#: Longest prefix first so "GB03SH-" beats "GB03-" and "X6h-" beats "X6-".
_PREFIX_INDEX: list[tuple[str, DeviceProfile]] = sorted(
    ((p.name_prefix, p) for p in _PROFILES),
    key=lambda pair: len(pair[0]),
    reverse=True,
)


def find_profile_by_name(name: str | None) -> DeviceProfile | None:
    """Resolve an advertised BLE name to a profile, or None if unrecognised.

    Case-sensitive first: ``X6h`` and ``X6H`` (likewise ``X5h``/``X5H``,
    ``SC03h``/``SC03H``, ...) are separate models with different energy
    settings. A case-insensitive pass follows so an unexpected spelling still
    lands on the right family.
    """
    if not name:
        return None
    for prefix, profile in _PREFIX_INDEX:
        if name.startswith(prefix):
            return profile
    upper = name.upper()
    for prefix, profile in _PREFIX_INDEX:
        if upper.startswith(prefix.upper()):
            return profile
    return None


def get_profile(model_id: str) -> DeviceProfile | None:
    return next((p for p in _PROFILES if p.model_id == model_id), None)


def registered_profiles() -> list[DeviceProfile]:
    return list(_PROFILES)


def all_name_prefixes() -> list[str]:
    return [profile.name_prefix for profile in _PROFILES]


def advertisement_contradicts(advertised_uuids: Iterable[str]) -> bool:
    """True when a populated UUID list contains none of ours.

    An empty list proves nothing (many peripherals omit services from the
    advertisement), so only a non-empty list without any known UUID counts
    against a name match.
    """
    advertised = {uuid.lower() for uuid in advertised_uuids}
    if not advertised:
        return False
    return not (advertised & ADVERTISED_SERVICE_UUIDS)
