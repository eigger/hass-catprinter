# Cat Printer troubleshooting

[Home](../README.md) | **English** | [한국어](troubleshooting.ko.md)

## Common troubleshooting

Start with the [common Bluetooth troubleshooting](https://github.com/eigger/blesession/blob/main/docs/troubleshooting.md) and [Bluetooth proxy setup](https://github.com/eigger/blesession/blob/main/docs/bluetooth.md). Proxy firmware settings and Cat Printer integration options are separate. The shared guide includes XIAO W5500 Ethernet Adapter **V1.2** (Ethernet/PoE/external antenna) and **M5Stack AtomS3U**, a USB-A dongle-form device, with purchase links. These are shared recommendations, not newly verified printer/board combinations.

## Device-specific checks

- Turn it on, charge it and wake it using the model's own controls. Sleep timers vary; the older X6h observation of an hour of idle availability is not a guarantee for other printers.
- Load compatible paper, close the cover and let an overheated head cool. `out_of_paper`, `cover_open` and `overheating` require physical attention before another job.
- Disconnect vendor/phone apps and other Bluetooth centrals. The original setup guidance says not to pair it in the phone's Bluetooth settings while testing. No universal pairing/reset sequence is known for all profiles.
- Select the correct, case-sensitive model. `X6h` and `X6H` differ. `D1` challenge-secret models and models marked unsupported are rejected; the integration has no secret-entry authentication flow. Do not invent a key or repeatedly reconnect to bypass it.
- Discovery requires advertising; printing additionally requires a usable GATT service and characteristic. Classic SPP is not the transport used here, even for “h” models. Manual address/model setup cannot add a missing GATT implementation.

## Symptoms and actions

| Symptom | Failing stage | Checks | Action |
|---|---|---|---|
| No discovery / unreachable | Discovery / connect | Printer awake, battery, proxy online state, distance and advertised name | Wake/charge the printer and restore the receiver. Use manual setup only if a supported profile actually matches the advertised model. |
| Found but cannot connect | Connect | `bluetooth_proxy.active` for GATT, free slots, other app connections, proxy power/network | Disconnect other apps and free a slot before retrying. `esp32_ble_tracker.scan_parameters.active` requests scan responses; it is separate. Passive scanning alone does not prove connections impossible. |
| Connected but no reply | Session / subscribe / query | Selected model/firmware, print service, printer busy/asleep | Wake the printer and verify the profile. `NotificationTimeout` means a reply did not arrive after connection/subscription, not necessarily a pairing failure. |
| Missing bands / early stop | Transfer / raster | Paper, cover, radio path and pacing | Automatic proxy pacing is at least 20 ms, packets at most 100 bytes; local automatic pacing comes from the model. Increase packet interval in Configure if needed; this does not change proxy firmware settings. |
| Link loss / write timeout | Transfer / link / write | Actual path, battery, proxy restart/power/network and simultaneous traffic | Restore power/network and retry after checking paper. A write that never returned differs from waiting for a printer reply. The integration drops a hung kept link so the next operation reconnects. |
| Job completion timeout | Completion | Whether paper actually printed | Look at the paper before retrying: the image may already have printed. Repeating the action can produce duplicate labels and consume paper. |
| Intermittent success | Last reported failure stage | Last failure versus latest print, connection retention and slot usage | Success does not erase `last_failure`. The default is connect–query–disconnect; Keep connection is off. |

Automatic connection recovery and printer-specific diagnosis do not promise every failed print will be retried. This integration does not expose BLE ESL's Retry Count, Debounce or guarded-write actions.

## Diagnostics and logs

Under **Settings → Devices & services → Cat Printer → your device**, open the diagnostic entities or inspect their attributes under **Developer tools → States**. Actual entity IDs depend on your registry names; search for the entity suffix below.

- `sensor.*_print_duration`: seconds for the current/last print. After completion its attributes include the last print's session report. While printing, a previous report is omitted so it cannot be confused with the current duration.
- `sensor.*_last_failure`: last counted failure timestamp and its report attributes; retained until another failure. A successful job does not clear it.
- `sensor.*_error_count`: counted BLE session failures since entry load, reset by reload. A status poll that fails before connecting is excluded; this is not a lifetime failure total.
- `sensor.*_status`, `sensor.*_conditions` and paper/cover/heat binary sensors: distinguish a device fault from a transport failure. `binary_sensor.*_connection` is live connection state; off between jobs can be normal.

Use report attributes actually present for this operation: `failed_stage`, `failed_detail`, `error`, `likely_cause`, and radio facts such as `via`, `via_type`, `rssi`, `paths`, `via_unconfirmed`. Optional keys are not guaranteed on every failure. An unconfirmed/best advertisement path is not proof of the radio used for the connection; RSSI alone does not establish the cause.

The device maps `subscribe`, `precheck`, `query_info` and `query_state` into the shared `session` stage; `raster` and `feed` map into `transfer`. Connection/link errors use the shared blesession stages/details. Inspect the accompanying error and cause to distinguish a paper fault from link or protocol failure. No integration `diagnostics.py` download is provided; use these real entity attributes and action traces instead.

Include HA/integration versions, installed blesession/imagespec versions when known, printer model/firmware, local adapter or proxy model/revision/ESPHome version, failure time, sanitized attributes, action YAML and whether paper actually printed. Separate last success from last failure and identify unverified paths.

For a short reproduction, enable only the actual integration logger and turn it off afterwards:

```yaml
logger:
  logs:
    custom_components.catprinter: debug
```

## If the problem persists

Include the evidence described above and follow the existing issue instructions. Before posting in [Issues](https://github.com/eigger/hass-catprinter/issues), remove Bluetooth/MAC/device addresses, internal IPs/hostnames, tokens, keys and private print payloads/images from logs, attributes and traces. Use [Discussions](https://github.com/eigger/hass-catprinter/discussions) for setup questions.

Existing repository hardware confirmation is X6h firmware 3.0.5D with a local adapter and ESPHome proxy. This standards migration runs automated HA/transport tests; it does not add physical-model, proxy-board, radio-performance or frontend validation. See [adoption evidence](../ADOPTION_CHECKLIST.md).
