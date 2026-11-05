<!-- hass-standards:header:start -->
# Cat Printer for Home Assistant

A Home Assistant custom integration that prints text, QR codes and images on Bluetooth thermal cat printers using Home Assistant Bluetooth and ESPHome proxies.

**English** | [한국어](README.ko.md)

<!-- hass-standards:badges:start -->
[![Release](https://img.shields.io/github/v/release/eigger/hass-catprinter?style=flat)](https://github.com/eigger/hass-catprinter/releases)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5?style=flat)](#installation)
[![Home Assistant minimum](https://img.shields.io/badge/HA-%E2%89%A5%202025.2.0-41BDF5?style=flat)](hacs.json)
[![Tests](https://img.shields.io/github/actions/workflow/status/eigger/hass-catprinter/tests.yml?branch=main&style=flat&label=Tests)](https://github.com/eigger/hass-catprinter/actions/workflows/tests.yml)
[![Validate](https://img.shields.io/github/actions/workflow/status/eigger/hass-catprinter/validate.yml?branch=main&style=flat&label=Validate)](https://github.com/eigger/hass-catprinter/actions/workflows/validate.yml)
[![License](https://img.shields.io/github/license/eigger/hass-catprinter?style=flat)](LICENSE)
[![Downloads](https://img.shields.io/github/downloads/eigger/hass-catprinter/latest/total?style=flat&color=41BDF5&label=Downloads)](https://github.com/eigger/hass-catprinter/releases)
<!-- hass-standards:badges:end -->
<!-- hass-standards:header:end -->

![Cat Printer](custom_components/catprinter/brand/logo.png)

## Features

- `catprinter.print` renders [imagespec](https://github.com/eigger/imagespec) layouts; `catprinter.feed` advances paper. Status, battery, last image and session diagnostics are exposed as entities.
- Existing hardware confirmation: **X6h, firmware 3.0.5D**, with a local adapter and ESPHome proxy. Other protocol profiles are **untested**; see [models and limitations](docs/user-guide.md#supported-models).

## Requirements

- **Home Assistant:** 2025.2.0 or later.
- **Bluetooth:** A working Home Assistant Bluetooth adapter or proxy with GATT connections enabled.
- **Device:** A [supported BLE printer](docs/user-guide.md#supported-models).

## Installation

<!-- hass-standards:installation:start -->
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=eigger&repository=hass-catprinter&category=integration)
<!-- hass-standards:installation:end -->

1. Click the badge above to open the repository in Marketplace.
2. If you need to add it yourself, go to **Settings → Marketplace → Add from link** and enter <https://github.com/eigger/hass-catprinter>. Connect GitHub if prompted.
3. Select **Install**. Restart Home Assistant if prompted, then continue to [Configuration](#configuration).

## Configuration

1. Wake the printer, load paper and close the cover. Disconnect phone and vendor apps.
2. Open **Settings → Devices & services** and confirm the discovered printer, or choose **Add integration → Cat Printer**. If discovery fails, enter the printer address and model.

For remote Bluetooth, see the [proxy setup guide](https://github.com/eigger/blesession/blob/main/docs/bluetooth.md) for boards such as the XIAO W5500 V1.2 and the USB-A M5Stack AtomS3U. These are general recommendations. See the Features section for the existing printer verification.

## Quick start

From **Developer tools → Actions**, select your printer device:

```yaml
action: catprinter.print
target:
  device_id: YOUR_PRINTER_DEVICE_ID
data:
  payload:
    - type: text
      value: Hello Home Assistant!
      x: 8
      y: 8
      size: 40
  height: 80
```

## Important limitations

- Model names are case-sensitive (`X6h` and `X6H` are different). A discovered advertisement alone cannot establish whether GATT printing works.
- Models requiring a vendor `D1` secret or incompatible flow control, A4 and Wi-Fi printers, and Bluetooth Classic SPP are unsupported.
- Existing hardware verification is listed above. The standards adoption did not include new physical-printer or Home Assistant frontend tests.

## Documentation

| Topic | English | 한국어 |
|---|---|---|
| Models, entities, actions, examples and tuning | [User guide](docs/user-guide.md) | [사용 안내](docs/ko/user-guide.md) |
| Power, connection, paper and session failures | [Troubleshooting](docs/troubleshooting.md) | [문제 해결](docs/troubleshooting.ko.md) |
| Payload action examples, rendering and output settings | [Payload guide](docs/payload.md) | [payload 안내](docs/payload.ko.md) |
| Real HA tests, dependencies and contribution | [Development (Korean)](docs/development.md) | [개발 안내](docs/development.md) |
| Frame format, CRC and model profiles | [Protocol](docs/protocol.md) | [프로토콜 원문 (영어)](docs/protocol.md) |
| Adopted standard and verification evidence | [Standards (Korean)](STANDARDS.md) | [적용 체크리스트](ADOPTION_CHECKLIST.md) |

Include sanitized diagnostics from the troubleshooting guide when reporting a bug.

<!-- hass-standards:support:start -->
## Support

- [Issues](https://github.com/eigger/hass-catprinter/issues): Report bugs or request features.
- [Discussions](https://github.com/eigger/hass-catprinter/discussions): Ask questions and share your experience.
<!-- hass-standards:support:end -->

<!-- hass-standards:related-projects:start -->
<!-- hass-standards:related-projects:end -->

<!-- hass-standards:license:start -->
## License

Released under the [MIT License](LICENSE).
<!-- hass-standards:license:end -->
