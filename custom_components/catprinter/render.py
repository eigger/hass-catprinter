"""Image rendering via imagespec."""

from __future__ import annotations

import os

from homeassistant.components.recorder.history import get_significant_states
from homeassistant.exceptions import HomeAssistantError
from imagespec import RenderContext, RenderError, render


def _make_context(hass, *, default_font, palette):
    def font_resolver(name):
        base_name = os.path.basename(name)

        # 1. Fonts shipped with this integration
        local_path = os.path.join(os.path.dirname(__file__), "fonts", base_name)
        if os.path.exists(local_path):
            return local_path

        # 2. Home Assistant www/fonts
        www_path = os.path.join(hass.config.path("www/fonts"), base_name)
        if os.path.exists(www_path):
            return www_path

        return None

    def history_provider(entity_ids, start, end):
        return get_significant_states(
            hass,
            start_time=start,
            entity_ids=list(entity_ids),
            significant_changes_only=False,
            minimal_response=True,
            no_attributes=False,
        )

    return RenderContext(
        font_resolver=font_resolver,
        history_provider=history_provider,
        default_font=default_font,
        palette=palette,
        allow_local_images=True,
    )


def render_image(entity_id, service, hass, width: int = 384):
    """Render the service payload into a PIL image.

    ``width`` is the print head width of the resolved device profile and is
    not a service option: the wire protocol has no width field, every row is
    exactly ``printhead_px / 8`` bytes.
    """
    try:
        return render(
            payload=service.data.get("payload", ""),
            width=width,
            height=service.data.get("height", 240),
            rotate=service.data.get("rotate", 0),
            # The output width is fixed like an e-ink panel: with 90/270 the
            # payload is authored on a height x width canvas (along the paper)
            # and the result is still exactly width x height.
            rotate_mode="canvas",
            background=service.data.get("background", "white"),
            dither=False,
            context=_make_context(hass, default_font="ppb.ttf", palette=["black", "white"]),
        )
    except RenderError as err:
        raise HomeAssistantError(str(err)) from err
