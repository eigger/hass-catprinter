# Cat Printer brand assets

An original cat-eared pocket thermal printer icon drawn by
`scripts/generate_brand.py` on a dark navy rounded square, with a matching sky
blue `Cat Printer` wordmark for the landscape logo. No third-party artwork is
used.

| File | Size | Purpose |
| --- | --- | --- |
| `icon.png` | 256 × 256 | Home Assistant and HACS icon |
| `icon@2x.png` | 512 × 512 | High-resolution icon |
| `logo.png` | 993 × 256 | Landscape integration logo; README artwork |
| `logo@2x.png` | 1986 × 512 | High-resolution landscape logo |

All images are RGBA PNGs with transparent outer corners and backgrounds. These
sizes follow the [HA brand image guidelines](https://contributors.home-assistant.io/core/integrations/brands/).
Home Assistant 2026.3 and later serves these assets from the integration's local
`brand/` directory. The sky blue wordmark works against light and dark
backgrounds, so separate dark variants are not required.

## Source and permission

The icon is drawn from geometric primitives in this repository's
`scripts/generate_brand.py` and is covered by the repository's MIT license
(Copyright (c) 2026 eigger). The wordmark is rendered with Pillow's bundled
Aileron Regular via
[`ImageFont.load_default`](https://pillow.readthedocs.io/en/stable/reference/ImageFont.html#PIL.ImageFont.load_default).
[Aileron](https://dotcolon.net/font/aileron/) permits commercial use and is
released with no rights reserved. No font file is redistributed or loaded from
the system.

## Reproduce

Use Python 3.10 or newer and Pillow 12.3.0 (also supplied by HA 2026.10.2):

```sh
python -m pip install Pillow==12.3.0
python scripts/generate_brand.py
```

The script needs no network access and produces the same PNG bytes on every
run with that Pillow version.

SHA256 (Pillow 12.3.0):

- `icon@2x.png`: `3cfdffea4fb3d7065fa91d309fc0aacc3fd9ade68c08977d7b8703eaec1b0dea`
- `icon.png`: `2478640eb49f311697112d3c95749f714ea82ba7b0c272a5ec8f654fb8c8463e`
- `logo@2x.png`: `2704bbd335edd3ba379ccd359a6551146ae1bc566e5a0c1e0439f3f85f5367bd`
- `logo.png`: `1547479bd521f3da854f06612f8f9565b72ea981039b30327a884e2abb92bcce`

The local `brand/icon.png` is used by the
[HACS brands check](https://hacs.xyz/docs/publish/include/#check-brands).
These files do not imply inclusion in the HACS default list or HA brands
repository. README pages use `custom_components/catprinter/brand/logo.png`.
