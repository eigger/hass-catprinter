"""Generate Home Assistant brand images for Cat Printer.

The artwork is an original geometric brand mark on a dark navy rounded square:
a centered cat-eared pocket thermal printer with a printed receipt strip bearing
a crisp Bluetooth rune symbol and thick print lines. Drawn from geometric
primitives at 4x scale and downsampled, so no source image, external font file,
or network access is needed. Run with Pillow 12.3.0 for reproducible PNGs.
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BRAND = Path(__file__).resolve().parents[1] / "custom_components/catprinter/brand"
SIZE = 512
SCALE = 4
NAVY = "#1b2a41"
CYAN = "#38bdf8"
WHITE = "#ffffff"
YELLOW = "#ffd23f"
GOLD = "#f2a900"
CORAL = "#ff6b8b"
WORDMARK = "#0ea5e9"


def _rounded_polygon(
    points: list[tuple[float, float]],
    radii: list[float] | float,
    steps: int = 20,
) -> list[tuple[float, float]]:
    """Return polygon vertices with mathematically rounded corners."""
    n = len(points)
    if isinstance(radii, (int, float)):
        radii = [float(radii)] * n
    poly_pts: list[tuple[float, float]] = []
    for i in range(n):
        r = radii[i]
        if r <= 0:
            poly_pts.append(points[i])
            continue
        p_prev = points[(i - 1) % n]
        p_curr = points[i]
        p_next = points[(i + 1) % n]

        v1 = (p_prev[0] - p_curr[0], p_prev[1] - p_curr[1])
        v2 = (p_next[0] - p_curr[0], p_next[1] - p_curr[1])
        l1 = math.hypot(*v1)
        l2 = math.hypot(*v2)
        u1 = (v1[0] / l1, v1[1] / l1)
        u2 = (v2[0] / l2, v2[1] / l2)

        dot = max(-1.0, min(1.0, u1[0] * u2[0] + u1[1] * u2[1]))
        half_ang = math.acos(dot) / 2.0
        dist = min(r / math.tan(half_ang), l1 * 0.45, l2 * 0.45)
        eff_r = dist * math.tan(half_ang)
        t1 = (p_curr[0] + u1[0] * dist, p_curr[1] + u1[1] * dist)
        t2 = (p_curr[0] + u2[0] * dist, p_curr[1] + u2[1] * dist)

        bis = (u1[0] + u2[0], u1[1] + u2[1])
        bl = math.hypot(*bis)
        ub = (bis[0] / bl, bis[1] / bl)
        c_dist = eff_r / math.sin(half_ang)
        center = (p_curr[0] + ub[0] * c_dist, p_curr[1] + ub[1] * c_dist)

        a1 = math.atan2(t1[1] - center[1], t1[0] - center[0])
        a2 = math.atan2(t2[1] - center[1], t2[0] - center[0])
        da = a2 - a1
        while da <= -math.pi:
            da += 2 * math.pi
        while da > math.pi:
            da -= 2 * math.pi

        for s_idx in range(steps + 1):
            a = a1 + da * s_idx / steps
            poly_pts.append(
                (center[0] + eff_r * math.cos(a), center[1] + eff_r * math.sin(a))
            )
    return poly_pts


def _draw_thick_polyline(
    draw: ImageDraw.ImageDraw,
    pts: list[tuple[float, float]],
    width: float,
    color: str,
) -> None:
    """Draw a thick polyline with perfectly round caps and joins."""
    r = width / 2.0
    for x, y in pts:
        draw.ellipse([x - r, y - r, x + r, y + r], fill=color)
    for (x1, y1), (x2, y2) in zip(pts, pts[1:], strict=False):
        dx = x2 - x1
        dy = y2 - y1
        length = math.hypot(dx, dy)
        if length == 0:
            continue
        nx = -dy / length * r
        ny = dx / length * r
        draw.polygon(
            [
                (x1 + nx, y1 + ny),
                (x2 + nx, y2 + ny),
                (x2 - nx, y2 - ny),
                (x1 - nx, y1 - ny),
            ],
            fill=color,
        )


def _draw_bluetooth_rune(
    draw: ImageDraw.ImageDraw,
    cx: float,
    cy: float,
    half_h: float,
    w_right: float,
    w_left: float,
    stroke: float,
    color: str,
    s: int,
) -> None:
    """Draw a clean geometric Bluetooth rune centered at (cx, cy)."""
    _draw_thick_polyline(
        draw,
        [(cx * s, (cy - half_h) * s), (cx * s, (cy + half_h) * s)],
        stroke * s,
        color,
    )
    _draw_thick_polyline(
        draw,
        [
            (cx * s, (cy - half_h) * s),
            ((cx + w_right) * s, (cy - half_h * 0.5) * s),
            ((cx - w_left) * s, (cy + half_h * 0.5) * s),
        ],
        stroke * s,
        color,
    )
    _draw_thick_polyline(
        draw,
        [
            (cx * s, (cy + half_h) * s),
            ((cx + w_right) * s, (cy + half_h * 0.5) * s),
            ((cx - w_left) * s, (cy - half_h * 0.5) * s),
        ],
        stroke * s,
        color,
    )


def draw_icon() -> Image.Image:
    """Draw the 512px RGBA app icon."""
    s = SCALE
    image = Image.new("RGBA", (SIZE * s, SIZE * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(image)

    def box(x0: float, y0: float, x1: float, y1: float) -> list[float]:
        return [x0 * s, y0 * s, x1 * s, y1 * s]

    # 1. Dark navy rounded square background.
    d.rounded_rectangle(box(0, 0, SIZE - 1, SIZE - 1), radius=104 * s, fill=NAVY)

    # 2. Centered geometric cat ears (cyan outer shell + gold inner ear triangles).
    left_ear = [(108 * s, 210 * s), (126 * s, 68 * s), (236 * s, 146 * s)]
    right_ear = [(404 * s, 210 * s), (386 * s, 68 * s), (276 * s, 146 * s)]
    d.polygon(_rounded_polygon(left_ear, [8 * s, 14 * s, 8 * s]), fill=CYAN)
    d.polygon(_rounded_polygon(right_ear, [8 * s, 14 * s, 8 * s]), fill=CYAN)

    left_inner = [(132 * s, 182 * s), (142 * s, 104 * s), (206 * s, 150 * s)]
    right_inner = [(380 * s, 182 * s), (370 * s, 104 * s), (306 * s, 150 * s)]
    d.polygon(_rounded_polygon(left_inner, 6 * s), fill=YELLOW)
    d.polygon(_rounded_polygon(right_inner, 6 * s), fill=YELLOW)

    # 3. Centered pocket printer outer shell (cyan) and inner faceplate (white).
    d.rounded_rectangle(box(86, 134, 426, 378), radius=76 * s, fill=CYAN)
    d.rounded_rectangle(box(108, 156, 404, 356), radius=58 * s, fill=WHITE)

    # 4. Cat face details on the printer faceplate (heterochromia eyes + nose).
    # Left eye (cyan ring + navy pupil + white highlight)
    d.ellipse(box(154, 198, 220, 264), fill=NAVY)
    d.ellipse(box(162, 206, 212, 256), fill=CYAN)
    d.ellipse(box(173, 217, 201, 245), fill=NAVY)
    d.ellipse(box(169, 213, 183, 227), fill=WHITE)

    # Right eye (gold ring + navy pupil + white highlight)
    d.ellipse(box(292, 198, 358, 264), fill=NAVY)
    d.ellipse(box(300, 206, 350, 256), fill=GOLD)
    d.ellipse(box(311, 217, 339, 245), fill=NAVY)
    d.ellipse(box(307, 213, 321, 227), fill=WHITE)

    # Cute geometric cat nose
    nose_pts = [(238 * s, 252 * s), (274 * s, 252 * s), (256 * s, 274 * s)]
    d.polygon(_rounded_polygon(nose_pts, 5 * s), fill=CORAL)

    # 5. Thermal paper exit slot & printed receipt strip emerging downward.
    d.rounded_rectangle(box(144, 304, 368, 332), radius=14 * s, fill=NAVY)

    # Paper strip with navy knockout border so it stands cleanly over the shell.
    d.rounded_rectangle(box(156, 312, 356, 458), radius=18 * s, fill=NAVY)
    d.rounded_rectangle(box(170, 320, 342, 444), radius=10 * s, fill=WHITE)

    # 6. Crisp Bluetooth rune + printed lines on the thermal receipt.
    _draw_bluetooth_rune(
        d,
        cx=206.0,
        cy=382.0,
        half_h=34.0,
        w_right=22.0,
        w_left=20.0,
        stroke=9.0,
        color=NAVY,
        s=s,
    )
    d.rounded_rectangle(box(246, 348, 320, 368), radius=8 * s, fill=GOLD)
    d.rounded_rectangle(box(246, 378, 320, 396), radius=8 * s, fill=NAVY)
    d.rounded_rectangle(box(246, 406, 300, 424), radius=8 * s, fill=CYAN)

    return image.resize((SIZE, SIZE), Image.Resampling.LANCZOS)


def main() -> None:
    """Write icon.png, icon@2x.png, logo.png and logo@2x.png."""
    BRAND.mkdir(parents=True, exist_ok=True)
    icon = draw_icon()
    icon.save(BRAND / "icon@2x.png", optimize=True)
    icon.resize((256, 256), Image.Resampling.LANCZOS).save(
        BRAND / "icon.png", optimize=True
    )

    # Pillow bundles Aileron Regular, so regeneration needs no system fonts.
    font = ImageFont.load_default(size=296)
    bounds = font.getbbox("Cat Printer")
    wordmark = Image.new("RGBA", (bounds[2] - bounds[0], bounds[3] - bounds[1]))
    ImageDraw.Draw(wordmark).text(
        (-bounds[0], -bounds[1]), "Cat Printer", font=font, fill=WORDMARK
    )
    wordmark = wordmark.crop(wordmark.getbbox())
    gap = 96 + ((SIZE + 96 + wordmark.width) % 2)
    logo = Image.new("RGBA", (SIZE + gap + wordmark.width, SIZE))
    logo.alpha_composite(icon, (0, 0))
    logo.alpha_composite(wordmark, (SIZE + gap, (SIZE - wordmark.height) // 2))
    logo = logo.crop(logo.getbbox())
    logo.save(BRAND / "logo@2x.png", optimize=True)
    logo.resize((logo.width // 2, logo.height // 2), Image.Resampling.LANCZOS).save(
        BRAND / "logo.png", optimize=True
    )


if __name__ == "__main__":
    main()
