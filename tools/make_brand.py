"""Draw the brand images: a cat-eared printer with a strip of paper.

    python tools/make_brand.py

Writes icon.png (256), icon@2x.png (512), logo.png (256 tall), logo@2x.png
(512 tall) into custom_components/catprinter/brand/. Everything is drawn at
high resolution and downsampled, so edges stay smooth.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[1] / "custom_components" / "catprinter" / "brand"

BODY = (250, 250, 250)
OUTLINE = (60, 60, 60)
EAR = (255, 170, 180)
EYE_L = (72, 150, 235)   # blue
EYE_R = (240, 170, 40)   # amber
PUPIL = (30, 30, 30)
PAPER = (255, 255, 255)
INK = (60, 60, 60)
TEXT = (54, 54, 54)


def draw_icon(size: int) -> Image.Image:
    s = size * 4  # supersample
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    u = s / 100  # 100-unit grid
    w = int(3 * u)  # outline width

    # ears
    for pts in (
        [(14 * u, 40 * u), (17 * u, 8 * u), (42 * u, 24 * u)],
        [(86 * u, 40 * u), (83 * u, 8 * u), (58 * u, 24 * u)],
    ):
        d.polygon(pts, fill=BODY, outline=OUTLINE, width=w)
    d.polygon([(21 * u, 35 * u), (23 * u, 18 * u), (36 * u, 27 * u)], fill=EAR)
    d.polygon([(79 * u, 35 * u), (77 * u, 18 * u), (64 * u, 27 * u)], fill=EAR)

    # soft, squarish body -- the device itself
    d.rounded_rectangle(
        (8 * u, 22 * u, 92 * u, 86 * u), radius=24 * u, fill=BODY, outline=OUTLINE, width=w
    )
    d.rounded_rectangle((8 * u + w, 22 * u + w, 92 * u - w, 86 * u - w), radius=22 * u, fill=BODY)

    # cheeks
    d.ellipse((18 * u, 50 * u, 30 * u, 58 * u), fill=(255, 205, 210))
    d.ellipse((70 * u, 50 * u, 82 * u, 58 * u), fill=(255, 205, 210))

    # odd eyes
    for (x, iris) in ((36 * u, EYE_L), (64 * u, EYE_R)):
        d.ellipse((x - 8 * u, 36 * u, x + 8 * u, 54 * u), fill=iris, outline=OUTLINE, width=w)
        d.ellipse((x - 3.5 * u, 41.5 * u, x + 3.5 * u, 50 * u), fill=PUPIL)
        d.ellipse((x - 5.5 * u, 39 * u, x - 2 * u, 42.5 * u), fill=(255, 255, 255))

    # nose: solid pink rounded triangle, thin line down to a small "w" mouth
    nose = (255, 140, 160)
    d.polygon([(44.5 * u, 52.5 * u), (55.5 * u, 52.5 * u), (50 * u, 59.5 * u)], fill=nose)
    d.ellipse((48.2 * u, 56.2 * u, 51.8 * u, 60 * u), fill=nose)
    d.ellipse((44.5 * u, 51.3 * u, 47 * u, 53.8 * u), fill=nose)
    d.ellipse((53 * u, 51.3 * u, 55.5 * u, 53.8 * u), fill=nose)
    t = int(1.6 * u)
    d.line((50 * u, 59.5 * u, 50 * u, 62.5 * u), fill=OUTLINE, width=t)
    d.arc((44.5 * u, 59 * u, 50.2 * u, 65.5 * u), 10, 180, fill=OUTLINE, width=t)
    d.arc((49.8 * u, 59 * u, 55.5 * u, 65.5 * u), 0, 170, fill=OUTLINE, width=t)

    # paper slot on the front, paper coming out and down
    d.rounded_rectangle((22 * u, 66 * u, 78 * u, 71 * u), radius=2.5 * u, fill=OUTLINE)
    d.rounded_rectangle((28 * u, 69 * u, 72 * u, 97 * u), radius=3 * u, fill=PAPER, outline=OUTLINE, width=w)
    d.rectangle((28 * u, 69 * u, 72 * u, 71 * u), fill=OUTLINE)
    for y in (78, 84, 90):
        d.rounded_rectangle((36 * u, y * u, 64 * u, (y + 2.5) * u), radius=1.5 * u, fill=INK)

    return im.resize((size, size), Image.LANCZOS)


def draw_logo(height: int) -> Image.Image:
    icon = draw_icon(height)
    try:
        font = ImageFont.truetype("arialbd.ttf", int(height * 0.42))
    except OSError:
        font = ImageFont.load_default()
    text = "Cat Printer"
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    box = probe.textbbox((0, 0), text, font=font)
    tw, th = box[2] - box[0], box[3] - box[1]
    gap = int(height * 0.12)
    im = Image.new("RGB", (height + gap + tw, height), "white")
    im.paste(icon, (0, 0), icon)
    ImageDraw.Draw(im).text(
        (height + gap - box[0], (height - th) // 2 - box[1]), text, fill=TEXT, font=font
    )
    return trim(im)


def trim(im: Image.Image) -> Image.Image:
    bg = Image.new(im.mode, im.size, im.getpixel((0, 0)))
    bbox = ImageChops.difference(im, bg).getbbox()
    return im.crop(bbox) if bbox else im


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    trim(draw_icon(256)).resize((256, 256), Image.LANCZOS).save(OUT / "icon.png")
    trim(draw_icon(512)).resize((512, 512), Image.LANCZOS).save(OUT / "icon@2x.png")
    # Render the logo once at 2x and halve it so the pair is pixel-consistent.
    logo2x = draw_logo(512)
    logo2x = logo2x.crop((0, 0, logo2x.width - logo2x.width % 2, logo2x.height - logo2x.height % 2))
    logo2x.save(OUT / "logo@2x.png")
    logo2x.resize((logo2x.width // 2, logo2x.height // 2), Image.LANCZOS).save(OUT / "logo.png")
    for p in sorted(OUT.iterdir()):
        with Image.open(p) as im:
            print(p.name, im.size)


if __name__ == "__main__":
    main()
