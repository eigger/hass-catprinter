"""Manifest / translation consistency."""

from __future__ import annotations

import json
from pathlib import Path

from catprinter_ble import all_name_prefixes

COMPONENT = Path(__file__).resolve().parents[1] / "custom_components" / "catprinter"


def test_every_prefix_has_a_matcher():
    manifest = json.loads((COMPONENT / "manifest.json").read_text(encoding="utf-8"))
    names = {m["local_name"].rstrip("*") for m in manifest["bluetooth"] if "local_name" in m}
    assert set(all_name_prefixes()) <= names
    assert all(len(n) >= 3 for n in names)


def test_translations_cover_strings():
    strings = json.loads((COMPONENT / "strings.json").read_text(encoding="utf-8"))
    for lang in ("en", "ko"):
        data = json.loads((COMPONENT / "translations" / f"{lang}.json").read_text(encoding="utf-8"))
        assert _keys(data) == _keys(strings), lang


def _keys(node, prefix=""):
    if isinstance(node, dict):
        out = set()
        for k, v in node.items():
            out |= _keys(v, f"{prefix}.{k}")
        return out
    return {prefix}
