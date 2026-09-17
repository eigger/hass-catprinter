"""Print a test strip through the catprinter_ble package, no Home Assistant.

    pip install bleak bleak-retry-connector pillow
    python tools/print_test.py                      # scan by known prefixes
    python tools/print_test.py D5:D0:0C:A0:2D:5D    # or by address
    python tools/print_test.py <addr> --text        # text mode profile
    python tools/print_test.py <addr> --image photo.png
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from bleak import BleakScanner
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components" / "catprinter"))

from catprinter_ble import CatPrinterDevice, find_profile_by_name  # noqa: E402


def test_strip(width: int) -> Image.Image:
    img = Image.new("RGB", (width, 160), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 28)
    except OSError:
        font = ImageFont.load_default()
    draw.text((8, 8), "hass-catprinter", fill="black", font=font)
    draw.text((8, 44), "X6h over BLE GATT", fill="black", font=font)
    draw.rectangle((8, 90, width - 9, 150), outline="black", width=3)
    for x in range(16, width - 16, 24):
        draw.line((x, 96, x + 12, 144), fill="black", width=2)
    # 1-px border to check the head edges
    draw.rectangle((0, 0, width - 1, 159), outline="black")
    return img


async def find_address() -> str | None:
    print("scanning 8s ...")
    for d in await BleakScanner.discover(timeout=8.0):
        if find_profile_by_name(d.name):
            print(f"found {d.name} {d.address}")
            return d.address
    return None


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("address", nargs="?")
    ap.add_argument("--text", action="store_true", help="text mode")
    ap.add_argument("--image", help="print this image file instead of the strip")
    ap.add_argument("--density", type=int, default=4)
    ap.add_argument("--feed", type=int, default=None)
    ap.add_argument("-v", action="store_true")
    args = ap.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.v else logging.INFO, format="%(levelname)s %(message)s")

    address = args.address or await find_address()
    if not address:
        sys.exit("printer not found")

    ble_device = await BleakScanner.find_device_by_address(address, timeout=10.0)
    if ble_device is None:
        sys.exit(f"{address} not visible")
    print(f"device {ble_device.name} -> profile {find_profile_by_name(ble_device.name)}")

    device = CatPrinterDevice(address)
    data = await device.update_device(ble_device)
    print("info:", data)

    image = Image.open(args.image) if args.image else test_strip(data.printhead_px)

    def progress(sent: int, total: int) -> None:
        print(f"\r  {sent}/{total} bytes", end="", flush=True)

    result = await device.print_image(
        ble_device,
        image,
        mode="text" if args.text else "image",
        density=args.density,
        feed_dots=args.feed,
        on_progress=progress,
    )
    print("\nresult:", result)
    print("state after job:", data.sensors)


if __name__ == "__main__":
    asyncio.run(main())
