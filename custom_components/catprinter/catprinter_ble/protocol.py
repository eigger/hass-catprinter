"""The ``51 78`` cat printer protocol: framing, commands, raster encoding.

See ``docs/protocol.md`` for the byte-level description.

Frame layout::

    51 78 CMD DIR LEN_LO LEN_HI PAYLOAD... CRC8 FF

``DIR`` is 0 towards the printer and 1 back from it. ``CRC8`` (poly 0x07,
init 0) covers the payload only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

# --------------------------------------------------------------------------
# framing
# --------------------------------------------------------------------------

MAGIC = b"\x51\x78"
TRAILER = 0xFF

#: CRC-8, polynomial 0x07, init 0.
_CRC_TABLE = bytes(
    [
        0x00, 0x07, 0x0E, 0x09, 0x1C, 0x1B, 0x12, 0x15, 0x38, 0x3F, 0x36, 0x31, 0x24, 0x23, 0x2A, 0x2D,
        0x70, 0x77, 0x7E, 0x79, 0x6C, 0x6B, 0x62, 0x65, 0x48, 0x4F, 0x46, 0x41, 0x54, 0x53, 0x5A, 0x5D,
        0xE0, 0xE7, 0xEE, 0xE9, 0xFC, 0xFB, 0xF2, 0xF5, 0xD8, 0xDF, 0xD6, 0xD1, 0xC4, 0xC3, 0xCA, 0xCD,
        0x90, 0x97, 0x9E, 0x99, 0x8C, 0x8B, 0x82, 0x85, 0xA8, 0xAF, 0xA6, 0xA1, 0xB4, 0xB3, 0xBA, 0xBD,
        0xC7, 0xC0, 0xC9, 0xCE, 0xDB, 0xDC, 0xD5, 0xD2, 0xFF, 0xF8, 0xF1, 0xF6, 0xE3, 0xE4, 0xED, 0xEA,
        0xB7, 0xB0, 0xB9, 0xBE, 0xAB, 0xAC, 0xA5, 0xA2, 0x8F, 0x88, 0x81, 0x86, 0x93, 0x94, 0x9D, 0x9A,
        0x27, 0x20, 0x29, 0x2E, 0x3B, 0x3C, 0x35, 0x32, 0x1F, 0x18, 0x11, 0x16, 0x03, 0x04, 0x0D, 0x0A,
        0x57, 0x50, 0x59, 0x5E, 0x4B, 0x4C, 0x45, 0x42, 0x6F, 0x68, 0x61, 0x66, 0x73, 0x74, 0x7D, 0x7A,
        0x89, 0x8E, 0x87, 0x80, 0x95, 0x92, 0x9B, 0x9C, 0xB1, 0xB6, 0xBF, 0xB8, 0xAD, 0xAA, 0xA3, 0xA4,
        0xF9, 0xFE, 0xF7, 0xF0, 0xE5, 0xE2, 0xEB, 0xEC, 0xC1, 0xC6, 0xCF, 0xC8, 0xDD, 0xDA, 0xD3, 0xD4,
        0x69, 0x6E, 0x67, 0x60, 0x75, 0x72, 0x7B, 0x7C, 0x51, 0x56, 0x5F, 0x58, 0x4D, 0x4A, 0x43, 0x44,
        0x19, 0x1E, 0x17, 0x10, 0x05, 0x02, 0x0B, 0x0C, 0x21, 0x26, 0x2F, 0x28, 0x3D, 0x3A, 0x33, 0x34,
        0x4E, 0x49, 0x40, 0x47, 0x52, 0x55, 0x5C, 0x5B, 0x76, 0x71, 0x78, 0x7F, 0x6A, 0x6D, 0x64, 0x63,
        0x3E, 0x39, 0x30, 0x37, 0x22, 0x25, 0x2C, 0x2B, 0x06, 0x01, 0x08, 0x0F, 0x1A, 0x1D, 0x14, 0x13,
        0xAE, 0xA9, 0xA0, 0xA7, 0xB2, 0xB5, 0xBC, 0xBB, 0x96, 0x91, 0x98, 0x9F, 0x8A, 0x8D, 0x84, 0x83,
        0xDE, 0xD9, 0xD0, 0xD7, 0xC2, 0xC5, 0xCC, 0xCB, 0xE6, 0xE1, 0xE8, 0xEF, 0xFA, 0xFD, 0xF4, 0xF3,
    ]
)


def crc8(data: bytes) -> int:
    value = 0
    for byte in data:
        value = _CRC_TABLE[(value ^ byte) & 0xFF]
    return value


def frame(cmd: int, payload: bytes) -> bytes:
    """Wrap ``payload`` in a host->printer frame."""
    length = len(payload)
    return (
        MAGIC
        + bytes((cmd, 0x00, length & 0xFF, (length >> 8) & 0xFF))
        + payload
        + bytes((crc8(payload), TRAILER))
    )


# --------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------

CMD_RETRACT = 0xA0
CMD_FEED = 0xA1
CMD_RAW_LINE = 0xA2
CMD_GET_STATE = 0xA3
CMD_QUALITY = 0xA4
CMD_CONTROL = 0xA6
CMD_GET_INFO = 0xA8
CMD_FLOW = 0xAE  # printer -> host only
CMD_ENERGY = 0xAF
CMD_GET_BATTERY = 0xBA
CMD_SPEED = 0xBD
CMD_MODE = 0xBE
CMD_RLE_LINE = 0xBF

PrintMode = Literal["image", "text"]

#: ``BE`` operands. 02 (tattoo) and 03 (label) exist but are not exposed.
_MODE_BYTE: dict[PrintMode, int] = {"image": 0x00, "text": 0x01}

#: A fresh speed command is inserted after this many raster rows.
SPEED_REFRESH_ROWS = 200

#: One ``A1`` per this many dots: 48 at 200 dpi, 72 at 300 dpi.
FEED_STEP = 48


def cmd_get_state() -> bytes:
    return frame(CMD_GET_STATE, b"\x00")


def cmd_get_info() -> bytes:
    return frame(CMD_GET_INFO, b"\x00")


def cmd_get_battery() -> bytes:
    return frame(CMD_GET_BATTERY, b"\x00")


def cmd_quality(level: int = 3) -> bytes:
    """``A4`` -- ASCII digit '1'..'5'."""
    level = min(max(level, 1), 5)
    return frame(CMD_QUALITY, bytes((0x30 + level,)))


def cmd_energy(energy: int) -> bytes:
    """``AF`` -- heater energy, 16-bit little-endian."""
    energy = min(max(energy, 0), 0xFFFF)
    return frame(CMD_ENERGY, bytes((energy & 0xFF, energy >> 8)))


def cmd_speed(speed: int) -> bytes:
    """``BD`` -- per-row delay. Smaller is faster."""
    return frame(CMD_SPEED, bytes((speed & 0xFF,)))


def cmd_mode(mode: PrintMode) -> bytes:
    """``BE`` -- 00 image, 01 text."""
    return frame(CMD_MODE, bytes((_MODE_BYTE[mode],)))


def cmd_feed(dots: int) -> bytes:
    """``A1`` -- advance ``dots`` rows, 16-bit little-endian."""
    dots = min(max(dots, 0), 0xFFFF)
    return frame(CMD_FEED, bytes((dots & 0xFF, dots >> 8)))


def cmd_retract(dots: int) -> bytes:
    """``A0`` -- reverse feed."""
    dots = min(max(dots, 0), 0xFFFF)
    return frame(CMD_RETRACT, bytes((dots & 0xFF, dots >> 8, 0x11)))


def cmd_stop() -> bytes:
    """``A6 05`` -- abort the current job."""
    return frame(CMD_CONTROL, b"\x05")


def feed_sequence(dots: int, step: int = FEED_STEP) -> bytes:
    """Split a feed into ``step``-dot chunks."""
    out = bytearray()
    while dots > 0:
        chunk = min(dots, step)
        out += cmd_feed(chunk)
        dots -= chunk
    return bytes(out)


# --------------------------------------------------------------------------
# raster encoding
# --------------------------------------------------------------------------

#: Bit-reverse table: MSB-first PIL packing -> LSB-first wire packing.
_BIT_REVERSE = bytes(int(f"{i:08b}"[::-1], 2) for i in range(256))

_RUN_MAX = 127


def rle_row(bits: bytes) -> bytes:
    """Run-length encode one row of 0/1 pixel values.

    Each output byte is ``color << 7 | length`` with ``length`` <= 127. Every
    pixel is covered, including all-white rows (which encode to a few bytes of
    white runs).
    """
    out = bytearray()
    if not bits:
        return b""
    color = bits[0]
    run = 0
    for px in bits:
        if px == color and run < _RUN_MAX:
            run += 1
            continue
        out.append((color << 7) | run)
        if px == color:
            run = 1
        else:
            color = px
            run = 1
    out.append((color << 7) | run)
    return bytes(out)


def _unpack_row(packed: bytes, width: int) -> bytes:
    bits = bytearray(width)
    for i in range(width):
        bits[i] = (packed[i >> 3] >> (7 - (i & 7))) & 1
    return bytes(bits)


def encode_row(packed_msb: bytes, width: int) -> bytes:
    """Encode one MSB-first packed row as a ``BF`` or ``A2`` frame.

    RLE wins when it is no longer than the raw row; otherwise the row goes out
    raw, LSB-first (pixel 0 in bit 0).
    """
    bytes_per_row = len(packed_msb)
    rle = rle_row(_unpack_row(packed_msb, width))
    if len(rle) <= bytes_per_row:
        return frame(CMD_RLE_LINE, rle)
    return frame(CMD_RAW_LINE, packed_msb.translate(_BIT_REVERSE))


# --------------------------------------------------------------------------
# job assembly
# --------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class JobParams:
    """Everything the encoder needs besides the raster."""

    mode: PrintMode = "image"
    energy: int | None = None  #: None -> omit the AF command
    speed: int = 30
    quality: int = 3
    feed_dots: int = 96  #: paper to advance after the last row
    feed_step: int = FEED_STEP
    copies: int = 1


def build_print_job(rows: list[bytes], width: int, params: JobParams) -> bytes:
    """Assemble the byte stream for one job.

    Per copy::

        A4 quality
        AF energy            (if energy is not None)
        BE mode
        BD speed
        rows...              (BD speed re-sent every 200 rows)
        BD 25
        A1 feed              (in 48-dot steps)

    followed by one ``A3`` whose reply marks the job as consumed.
    """
    out = bytearray()
    for _ in range(max(params.copies, 1)):
        out += cmd_quality(params.quality)
        if params.energy is not None and params.energy > 0:
            out += cmd_energy(params.energy)
        out += cmd_mode(params.mode)
        out += cmd_speed(params.speed)
        for index, row in enumerate(rows, start=1):
            out += encode_row(row, width)
            if index % SPEED_REFRESH_ROWS == 0:
                out += cmd_speed(params.speed)
        out += cmd_speed(25)
        out += feed_sequence(params.feed_dots, params.feed_step)
    out += cmd_get_state()
    return bytes(out)


# --------------------------------------------------------------------------
# responses
# --------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Frame:
    cmd: int
    direction: int
    payload: bytes
    raw: bytes


class FrameParser:
    """Reassemble frames from notification chunks.

    Scans for ``51 78`` and takes ``payload_len + 8`` bytes, ignoring anything
    in between. A partial frame is carried over to the next notification.
    """

    def __init__(self) -> None:
        self._buffer = bytearray()

    def feed(self, data: bytes) -> list[Frame]:
        self._buffer += data
        frames: list[Frame] = []
        while True:
            start = self._buffer.find(MAGIC)
            if start < 0:
                self._buffer.clear()
                break
            if start:
                del self._buffer[:start]
            if len(self._buffer) < 6:
                break
            length = self._buffer[4] | (self._buffer[5] << 8)
            total = length + 8
            if len(self._buffer) < total:
                break
            raw = bytes(self._buffer[:total])
            del self._buffer[:total]
            frames.append(Frame(raw[2], raw[3], raw[6 : 6 + length], raw))
        return frames


#: ``A3`` status bits.
STATUS_BITS: tuple[tuple[int, str], ...] = (
    (0x01, "out_of_paper"),
    (0x02, "cover_open"),
    (0x04, "overheating"),
    (0x08, "low_battery"),
    (0x10, "charging"),
    (0x80, "printing"),
)

FAULT_STATUSES = frozenset({"out_of_paper", "cover_open", "overheating"})


@dataclass(frozen=True, slots=True)
class DeviceState:
    flags: int
    conditions: tuple[str, ...]
    label_sensor: int | None
    battery_raw: int | None

    @property
    def fault(self) -> str | None:
        return next((c for c in self.conditions if c in FAULT_STATUSES), None)

    @property
    def is_printing(self) -> bool:
        return bool(self.flags & 0x80)


def decode_state(payload: bytes) -> DeviceState:
    flags = payload[0] if payload else 0
    conditions = tuple(name for bit, name in STATUS_BITS if flags & bit)
    return DeviceState(
        flags=flags,
        conditions=conditions,
        label_sensor=payload[1] if len(payload) > 1 else None,
        battery_raw=payload[2] if len(payload) > 2 else None,
    )


def battery_percent(raw: int | None, battery_model: int) -> int | None:
    """Turn the ``A3`` battery byte into a percentage.

    ``battery_model`` comes from the profile:

    * 0 -- the byte means nothing on this model;
    * 1 -- read the byte's hex spelling as a decimal (0x27 -> 27) and bucket
      23..28 into six bars;
    * 2 -- the byte plus one is already a percentage.
    """
    if raw is None or battery_model == 0:
        return None
    if battery_model == 2:
        return min(raw + 1, 100)
    try:
        value = int(f"{raw:02X}")
    except ValueError:
        return None
    if value >= 28:
        bars = 6
    elif value >= 23:
        bars = value - 22
    else:
        bars = 0
    return round(bars * 100 / 6)


@dataclass(frozen=True, slots=True)
class DeviceInfo:
    device_type: str
    firmware: str
    wifi_state: int | None
    extra: bytes = field(default=b"", repr=False)


def decode_info(payload: bytes) -> DeviceInfo:
    """``A8`` reply: type byte, unknown, wifi state, 7-byte GBK version."""
    device_type = f"XW00{payload[0]}" if payload else ""
    wifi = payload[2] if len(payload) > 2 else None
    version = payload[3:10].split(b"\x00", 1)[0].decode("gbk", errors="replace").strip()
    return DeviceInfo(device_type=device_type, firmware=version, wifi_state=wifi, extra=payload)


FlowEvent = Literal["full", "empty"]


def decode_flow(payload: bytes) -> FlowEvent | None:
    """``AE`` notification: ``10 70`` = buffer full, ``00 00`` = drained."""
    if len(payload) < 1:
        return None
    if payload[0] == 0x10:
        return "full"
    if payload[0] == 0x00:
        return "empty"
    return None
