"""X6h BLE GATT probe.

Checks whether the printer accepts the ``51 78`` protocol over BLE GATT.

    pip install bleak
    python probe_x6h.py            # scan for X6h-* and probe
    python probe_x6h.py D5:D0:0C:A0:2D:5D

Steps: connect -> dump services -> subscribe notify -> A8 getDevInfo ->
A3 getState -> A1 feed 48 dots. If paper moves, GATT works.
"""

from __future__ import annotations

import asyncio
import sys

from bleak import BleakClient, BleakScanner

CRC_TABLE = bytes(
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
    c = 0
    for b in data:
        c = CRC_TABLE[(c ^ b) & 0xFF]
    return c


def frame(cmd: int, payload: bytes) -> bytes:
    n = len(payload)
    return bytes([0x51, 0x78, cmd, 0x00, n & 0xFF, (n >> 8) & 0xFF]) + payload + bytes([crc8(payload), 0xFF])


GET_DEV_INFO = frame(0xA8, b"\x00")
GET_STATE = frame(0xA3, b"\x00")
FEED_48 = frame(0xA1, b"\x30\x00")

# Candidate GATT triples (service, write, notify) in preference order.
CANDIDATES = [
    ("0000ae30-0000-1000-8000-00805f9b34fb", "0000ae01-0000-1000-8000-00805f9b34fb", "0000ae02-0000-1000-8000-00805f9b34fb"),
    ("0000ae00-0000-1000-8000-00805f9b34fb", "0000ae01-0000-1000-8000-00805f9b34fb", None),
    ("0000ff00-0000-1000-8000-00805f9b34fb", "0000ff02-0000-1000-8000-00805f9b34fb", None),
    ("0000ab00-0000-1000-8000-00805f9b34fb", "0000ab01-0000-1000-8000-00805f9b34fb", None),
    ("0000ae80-0000-1000-8000-00805f9b34fb", "0000ae81-0000-1000-8000-00805f9b34fb", None),
    ("49535343-fe7d-4ae5-8fa9-9fafd205e455", "49535343-8841-43f4-a8d4-ecbe34729bb3", None),
]


async def find_address() -> str | None:
    print("scanning 8s for X6h-* ...")
    devices = await BleakScanner.discover(timeout=8.0)
    for d in devices:
        if d.name and d.name.upper().startswith("X6H-"):
            print(f"found {d.name} {d.address}")
            return d.address
    return None


async def main(address: str) -> None:
    got: list[bytes] = []

    def on_notify(_h, data: bytearray) -> None:
        print(f"  << {data.hex(' ')}")
        got.append(bytes(data))

    async with BleakClient(address, timeout=20.0) as client:
        print(f"connected, mtu={client.mtu_size}")
        print("services:")
        write_uuid = notify_uuid = None
        for svc in client.services:
            print(f"  {svc.uuid}")
            for ch in svc.characteristics:
                print(f"     {ch.uuid}  {','.join(ch.properties)}")
        for svc_uuid, w, n in CANDIDATES:
            svc = client.services.get_service(svc_uuid)
            if svc is None:
                continue
            write_uuid = w
            # First NOTIFY/INDICATE characteristic in the service.
            for ch in svc.characteristics:
                if "notify" in ch.properties or "indicate" in ch.properties:
                    notify_uuid = ch.uuid
                    break
            if n and notify_uuid is None:
                notify_uuid = n
            break
        if write_uuid is None:
            print("!! no known service found -- GATT path not usable")
            return
        print(f"using write={write_uuid} notify={notify_uuid}")

        if notify_uuid:
            await client.start_notify(notify_uuid, on_notify)

        for label, pkt in (("A8 getDevInfo", GET_DEV_INFO), ("A3 getState", GET_STATE)):
            print(f"  >> {label}: {pkt.hex(' ')}")
            await client.write_gatt_char(write_uuid, pkt, response=False)
            await asyncio.sleep(1.0)

        print("  >> A1 feed 48 dots -- watch the paper")
        await client.write_gatt_char(write_uuid, FEED_48, response=False)
        await asyncio.sleep(2.0)

        if notify_uuid:
            await client.stop_notify(notify_uuid)

    print()
    if any(b[:3] == b"\x51\x78\xa8" for b in got):
        print("RESULT: A8 answered over GATT -> protocol works on BLE")
    elif got:
        print("RESULT: got notifications but no A8 reply -- check output above")
    else:
        print("RESULT: no notifications. If the paper moved, writes work but notify UUID is wrong;")
        print("        if nothing moved, this model probably only listens on SPP.")


if __name__ == "__main__":
    addr = sys.argv[1] if len(sys.argv) > 1 else asyncio.run(find_address())
    if not addr:
        sys.exit("printer not found -- turn it on and make sure no phone is connected")
    asyncio.run(main(addr))
