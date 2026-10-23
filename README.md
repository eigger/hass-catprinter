# hass-catprinter

<!-- hass-standards:badges:start -->
[![Release](https://img.shields.io/github/v/release/eigger/hass-catprinter?style=flat)](https://github.com/eigger/hass-catprinter/releases)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5?style=flat)](#installation)
[![Home Assistant minimum](https://img.shields.io/badge/HA-%E2%89%A5%202025.2.0-41BDF5?style=flat)](hacs.json)
[![Tests](https://img.shields.io/github/actions/workflow/status/eigger/hass-catprinter/tests.yml?branch=main&style=flat&label=Tests)](https://github.com/eigger/hass-catprinter/actions/workflows/tests.yml)
[![Validate](https://img.shields.io/github/actions/workflow/status/eigger/hass-catprinter/validate.yml?branch=main&style=flat&label=Validate)](https://github.com/eigger/hass-catprinter/actions/workflows/validate.yml)
[![License](https://img.shields.io/github/license/eigger/hass-catprinter?style=flat)](LICENSE)
[![Downloads](https://img.shields.io/github/downloads/eigger/hass-catprinter/total?style=flat&color=41BDF5&label=Downloads)](https://github.com/eigger/hass-catprinter/releases)
<!-- hass-standards:badges:end -->

**English** | [한국어](README.ko.md)

A HACS custom integration that prints text, QR codes and images on inexpensive Bluetooth thermal “cat” printers using Home Assistant's Bluetooth stack and ESPHome proxies.

## Features and requirements

- `catprinter.print` renders [imagespec](https://github.com/eigger/imagespec) layouts; `catprinter.feed` advances paper. Status, battery, last image and session diagnostics are exposed as entities.
- Existing hardware confirmation: **X6h, firmware 3.0.5D**, with a local adapter and ESPHome proxy. Other protocol profiles are **untested**; see [models and limitations](docs/user-guide.md#supported-models).
- Home Assistant **2025.2.0+**, a supported BLE printer and a working HA Bluetooth adapter or proxy. A proxy needs GATT connections enabled. Keep the printer awake and disconnect other apps before printing.

## Installation

1. Add `https://github.com/eigger/hass-catprinter` to **HACS → Custom repositories → Integration**, or copy `custom_components/catprinter` into your HA configuration's `custom_components/` directory.
2. Restart Home Assistant.
3. Open **Settings → Devices & services** and confirm the discovered printer, or choose **Add integration → Cat Printer**. If no supported printer is discovered, enter its address and model manually.

Prepare your proxy using [Bluetooth proxy setup](https://github.com/eigger/hass-repo-standards/blob/main/docs/bluetooth.md), including XIAO W5500 V1.2 and the USB-A dongle-form M5Stack AtomS3U. This is general guidance, not a claim that each board was tested with this printer.

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

## Important limits

Model names are case-sensitive (`X6h` differs from `X6H`). A discovered advertisement does not prove GATT printing works. Models requiring a vendor `D1` secret, incompatible flow control, A4 and Wi-Fi printers are unsupported; Bluetooth Classic SPP is not used. Close phone/vendor app connections; load paper and close the cover. This adoption does not include new physical-printer or HA frontend checks.

## Documentation

| Topic | English | 한국어 |
|---|---|---|
| Models, entities, actions, examples and tuning | [User guide](docs/user-guide.md) | [사용 안내](docs/ko/user-guide.md) |
| Power, connection, paper and session failures | [Troubleshooting](docs/troubleshooting.md) | [문제 해결](docs/ko/troubleshooting.md) |
| Real HA tests, dependencies and contribution | [Development (Korean)](docs/development.md) | [개발 안내](docs/development.md) |
| Frame format, CRC and model profiles | [Protocol](docs/protocol.md) | [프로토콜 원문 (영어)](docs/protocol.md) |
| Adopted standard and verification evidence | [Standards (Korean)](STANDARDS.md) | [적용 체크리스트](ADOPTION_CHECKLIST.md) |

The Usage badge counts installations participating in HA Analytics, not all installations or people. Missing data or a failed request does not mean zero installs.

## Support and license

Report bugs in [Issues](https://github.com/eigger/hass-catprinter/issues) with sanitized evidence from the troubleshooting guide. Use [Discussions](https://github.com/eigger/hass-catprinter/discussions) for questions and ideas.

Released under the [MIT License](LICENSE).
