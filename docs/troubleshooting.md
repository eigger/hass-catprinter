# Cat Printer troubleshooting

[Home](../README.md) | [한국어](ko/troubleshooting.md)

Start with the [Bluetooth proxy setup](https://github.com/eigger/hass-repo-standards/blob/main/docs/bluetooth.md#troubleshooting). Proxy firmware settings and Cat Printer integration options are separate. The shared guide includes XIAO W5500 Ethernet Adapter **V1.2** (Ethernet/PoE/external antenna) and **M5Stack AtomS3U**, a USB-A dongle-form device, with purchase links. These are shared recommendations, not newly verified printer/board combinations.

## 1. Prepare this printer

- Turn it on, charge it and wake it using the model's own controls. Sleep timers vary; the older X6h observation of an hour of idle availability is not a guarantee for other printers.
- Load compatible paper, close the cover and let an overheated head cool. `out_of_paper`, `cover_open` and `overheating` require physical attention before another job.
- Disconnect vendor/phone apps and other Bluetooth centrals. The original setup guidance says not to pair it in the phone's Bluetooth settings while testing. No universal pairing/reset sequence is known for all profiles.
- Select the correct, case-sensitive model. `X6h` and `X6H` differ. `D1` challenge-secret models and models marked unsupported are rejected; the integration has no secret-entry authentication flow. Do not invent a key or repeatedly reconnect to bypass it.
- Discovery requires advertising; printing additionally requires a usable GATT service and characteristic. Classic SPP is not the transport used here, even for “h” models. Manual address/model setup cannot add a missing GATT implementation.

## 2. Identify where it failed

| Symptom | Check and next action |
|---|---|
| No discovery / unreachable | Wake the printer; check battery, proxy online state and distance. Inspect its advertised model name. An unknown name can use manual setup only if the selected supported profile actually matches. |
| Found but cannot connect | Enable `bluetooth_proxy.active` for GATT connections, free proxy slots and disconnect other apps. Check proxy power and network before retrying. `esp32_ble_tracker.scan_parameters.active` requests scan responses and is a different setting; passive scanning alone does not prove connections impossible. |
| Connected but no reply | Check selected model/firmware and the print service. The printer may be busy/asleep. `NotificationTimeout` means a reply did not arrive after connection/subscription, not necessarily a pairing failure. |
| Missing bands / early stop | Confirm paper/cover and radio path. Automatic proxy pacing is at least 20 ms, packets at most 100 bytes; local automatic pacing comes from the model. Increase packet interval in Configure if needed. This does not change proxy firmware settings. |
| Link loss / write timeout | Check actual path, battery, proxy restart/power/network and simultaneous traffic. A write that never returned differs from waiting for a printer reply. The integration drops a hung kept link so the next operation reconnects. |
| Job completion timeout | Look at the paper before retrying: the image may already have printed. Repeating the action can produce duplicate labels and consume paper. |
| Intermittent success | Compare the last failure with the latest print; success does not erase `last_failure`. Check connection retention and slot usage. The default is connect–query–disconnect; Keep connection is off. |

Automatic connection recovery and printer-specific diagnosis do not promise every failed print will be retried. This integration does not expose BLE ESL's Retry Count, Debounce or guarded-write actions.

## 3. Read the actual diagnostic entities

Under **Settings → Devices & services → Cat Printer → your device**, open the diagnostic entities or inspect their attributes under **Developer tools → States**. Actual entity IDs depend on your registry names; search for the entity suffix below.

- `sensor.*_print_duration`: seconds for the current/last print. After completion its attributes include the last print's session report. While printing, a previous report is omitted so it cannot be confused with the current duration.
- `sensor.*_last_failure`: last counted failure timestamp and its report attributes; retained until another failure. A successful job does not clear it.
- `sensor.*_error_count`: counted BLE session failures since entry load, reset by reload. A status poll that fails before connecting is excluded; this is not a lifetime failure total.
- `sensor.*_status`, `sensor.*_conditions` and paper/cover/heat binary sensors: distinguish a device fault from a transport failure. `binary_sensor.*_connection` is live connection state; off between jobs can be normal.

Use report attributes actually present for this operation: `failed_stage`, `failed_detail`, `error`, `likely_cause`, and radio facts such as `via`, `via_type`, `rssi`, `paths`, `via_unconfirmed`. Optional keys are not guaranteed on every failure. An unconfirmed/best advertisement path is not proof of the radio used for the connection; RSSI alone does not establish the cause.

The device maps `subscribe`, `precheck`, `query_info` and `query_state` into the shared `session` stage; `raster` and `feed` map into `transfer`. Connection/link errors use the shared blesession stages/details. Inspect the accompanying error and cause to distinguish a paper fault from link or protocol failure. No integration `diagnostics.py` download is provided; use these real entity attributes and action traces instead.

## 4. Report a reproducible problem

Include HA/integration versions, installed blesession/imagespec versions when known, printer model/firmware, local adapter or proxy model/revision/ESPHome version, failure time, sanitized attributes, action YAML and whether paper actually printed. Separate last success from last failure and identify unverified paths.

For a short reproduction, enable only the actual integration logger and turn it off afterwards:

```yaml
logger:
  logs:
    custom_components.catprinter: debug
```

Before posting in [Issues](https://github.com/eigger/hass-catprinter/issues), remove Bluetooth/MAC/device addresses, internal IPs/hostnames, tokens, keys and private print payloads/images from logs, attributes and traces. Use [Discussions](https://github.com/eigger/hass-catprinter/discussions) for setup questions.

Existing repository hardware confirmation is X6h firmware 3.0.5D with a local adapter and ESPHome proxy. This standards migration runs automated HA/transport tests; it does not add physical-model, proxy-board, radio-performance or frontend validation. See [adoption evidence](../ADOPTION_CHECKLIST.md).
