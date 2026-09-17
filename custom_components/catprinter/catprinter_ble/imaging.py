"""Image -> 1bpp raster conversion.

PIL does the heavy lifting: ``convert("1")`` applies Floyd-Steinberg dithering
and ``tobytes()`` on a mode ``"1"`` image yields MSB-first rows padded to byte
boundaries. The wire format wants LSB-first rows, but that is the encoder's
concern (see ``protocol.encode_rows``); the raster itself stays MSB-first so it
can be inspected and round-tripped with PIL.
"""

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image, ImageOps


@dataclass(frozen=True, slots=True)
class Bitmap1bpp:
    """A packed monochrome raster.

    Bit set (1) means black/ink, MSB is the leftmost pixel, every row starts on
    a byte boundary and is exactly ``bytes_per_row`` long.
    """

    data: bytes
    width: int
    height: int
    bytes_per_row: int

    def __post_init__(self) -> None:
        expected = self.bytes_per_row * self.height
        if len(self.data) != expected:
            raise ValueError(
                f"raster is {len(self.data)} bytes, expected {expected} "
                f"({self.bytes_per_row} x {self.height})"
            )

    def row(self, index: int) -> bytes:
        start = index * self.bytes_per_row
        return self.data[start : start + self.bytes_per_row]


def to_raster(
    image: Image.Image,
    *,
    dither: bool = True,
    threshold: int = 128,
) -> Bitmap1bpp:
    """Convert a PIL image into a printer-ready 1bpp raster."""
    # Invert first so that dark source pixels become high values, then mode "1"
    # packs "high" as a set bit -- i.e. 1 = ink.
    gray = ImageOps.invert(image.convert("L"))
    if dither:
        bw = gray.convert("1")
    else:
        cutoff = 255 - threshold
        bw = gray.point(lambda p: 255 if p > cutoff else 0, mode="1")

    return Bitmap1bpp(
        data=bw.tobytes(),
        width=bw.width,
        height=bw.height,
        bytes_per_row=-(-bw.width // 8),
    )


def fit_to_printhead(image: Image.Image, printhead_px: int) -> Image.Image:
    """Make an image exactly ``printhead_px`` wide.

    The wire protocol has no width field: every row is ``printhead_px / 8``
    bytes and the firmware simply counts bytes. A narrower image is therefore
    padded on the right with white, a wider one is scaled down keeping aspect.
    """
    if image.width == printhead_px:
        return image
    if image.width > printhead_px:
        height = max(1, round(image.height * printhead_px / image.width))
        return image.resize((printhead_px, height), Image.LANCZOS)
    canvas = Image.new("RGB", (printhead_px, image.height), "white")
    canvas.paste(image.convert("RGB"), (0, 0))
    return canvas
