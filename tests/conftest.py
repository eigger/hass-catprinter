"""Test setup for the standalone protocol layer.

The ``catprinter_ble`` package under ``custom_components/catprinter`` has no Home
Assistant imports, so it can be tested on its own. Its parent directory goes on
``sys.path`` (importing ``custom_components.catprinter`` instead would pull in
the HA integration).
"""

from __future__ import annotations

import sys
from pathlib import Path

COMPONENT_DIR = Path(__file__).resolve().parents[1] / "custom_components" / "catprinter"
sys.path.insert(0, str(COMPONENT_DIR))
