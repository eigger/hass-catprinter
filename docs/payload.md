# Cat Printer payloads

[README](../README.md) | **English** | [한국어](payload.ko.md)

## Common payload guide

See the [imagespec payload guide](https://github.com/eigger/imagespec/blob/main/docs/payload.md) for shared syntax, elements, properties, colors, rotation and dithering. The integration-specific action wrapper and printer settings are described below.

## Using payloads in this integration

Call `catprinter.print` from **Developer tools → Actions**, a script or an automation. Select a configured printer with `target.device_id` or an entity belonging to that printer with `target.entity_id`; area targets are also resolved to loaded printers. With only one loaded printer, the action can select it without a target. With several printers, select the intended target explicitly.

`data.payload` contains the imagespec element list. Home Assistant evaluates action-data templates before the integration renders it; the integration passes that prepared payload to imagespec without a second Jinja evaluation. Keep the existing [user guide examples](user-guide.md#services) for text, QR codes, downloaded images and print tuning.

## Minimal working example

[Complete action YAML](../examples/payload/minimal.yaml) uses an X6h profile, a text element and the bundled default font to render a **384 × 80 pixel** black-and-white image. Replace `image.cat_printer_last_print` with an entity from your configured printer, or select its device in the action editor. Entity IDs depend on your registry names.

The example sets `preview: true`: it updates the last-print image and returns the PNG data URL without sending a print command. After checking the preview, set `preview: false` to print. Rendering a preview still requires a loaded printer entry so its head width is known. This is a complete HA action, including its target and data, rather than the common guide's bare element list.

## Device output settings

The configured model determines width; X6h has a **384-pixel, 200-dpi** head. Width is not an action option. `height` defaults to 240 pixels; the action editor offers 8–4000. Choose enough height for all elements and margins. Other profiles have their own head widths; see [supported models](user-guide.md#supported-models).

`rotate` uses 0, 90, 180 or 270 degrees. The integration fixes imagespec's internal `rotate_mode` to `canvas`: at 90/270 degrees, author on a height × head-width canvas and the final image remains head-width × height. The example uses 0 degrees. Output is black and white (`#000000`, `#ffffff`), with a white default `background`. Global renderer dithering is disabled internally (`dither=False`); element-level image processing such as the existing `dlimg` example follows imagespec's element options. `rotate_mode` and global `dither` are not exposed action options.

The default font is bundled `ppb.ttf`; `rbm.ttf` is also bundled. A requested font basename is looked up first in the integration's `fonts` directory and then in Home Assistant's `www/fonts`. Install custom fonts there before using their names. Local images are enabled in the render context; downloaded images need an accessible source. Neither the examples nor this documentation require a network image or custom font.

`mode`, `density`, `energy`, `speed`, `feed` and `copies` control the device job after rendering; they do not change the canvas width. The [user guide](user-guide.md#services) describes these controls. Thermal paper produces monochrome output; this is not a color printer.

## Supported features and limitations

The manifest requires `imagespec[datamatrix]>=1.1.0`. Element availability and properties follow the installed imagespec version; use its common guide rather than assuming a feature from a newer release. Text, QR codes and downloaded-image examples are preserved in the user guide. The datamatrix extra is declared; other optional extras are not promised by this integration.

The integration provides imagespec with its real font resolver and a Home Assistant recorder history provider (`get_significant_states`). History elements require recorder data for the requested entities/time range; an empty history is not proof of a Bluetooth failure. HA action templates can read entity state through HA's normal template context. There is no additional integration-owned template engine, font download action or history configuration action.

Only X6h firmware 3.0.5D has existing local-adapter/proxy hardware confirmation. Other supported profiles are untested. D1-secret authentication, unsupported credit-window flow control, Classic SPP, A4 and Wi-Fi printing remain unsupported. A successful rendered preview does not verify GATT transport, paper handling or physical output.

## Troubleshooting

For render errors, verify the element properties against the installed imagespec version, font names, image accessibility and canvas bounds. The action reports rendering failures as `Failed to create image`; BLE printing failures use `Failed to print`. Check the last-print image before changing transport settings.

For power, paper, connection and session reports, use [device-specific troubleshooting](troubleshooting.md). Report reproducible problems through the existing [Issues](https://github.com/eigger/hass-catprinter/issues), following its reporting instructions and removing private payloads/images and addresses from public evidence.
