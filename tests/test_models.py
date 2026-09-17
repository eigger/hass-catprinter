"""Profile lookup tests."""

from __future__ import annotations

from catprinter_ble import models as m


def test_case_sensitive_prefix_first():
    assert m.find_profile_by_name("X6h-D0D5").model_id == "X6h"
    assert m.find_profile_by_name("X6H-D0D5").model_id == "X6H"
    assert m.find_profile_by_name("x6-abcd").model_id == "X6"
    assert m.find_profile_by_name("GB03SH-1234").model_id == "GB03SH"
    assert m.find_profile_by_name("GB03-1234").model_id == "GB03"
    assert m.find_profile_by_name("P15-1234") is None
    assert m.find_profile_by_name(None) is None


def test_x6h_profile_values():
    prof = m.find_profile_by_name("X6h-0000")
    assert prof.printhead_px == 384 and prof.mtu == 180 and prof.interval_ms == 4
    assert prof.packet_size == 177 and prof.default_feed_dots == 96
    assert prof.energy_for("image", 4) == 5000
    assert prof.energy_for("text", 4) == 8000
    assert prof.energy_for("image", 7) == 7250
    assert prof.energy_for("image", 1) == 2750
    assert prof.speed_for("image") == 10
    assert prof.battery_model == 1


def test_feed_step_follows_dpi():
    assert m.find_profile_by_name("X6h-0000").feed_step == 48
    p5 = m.find_profile_by_name("P5-0000")
    assert p5.dpi == 300 and p5.feed_step == 72 and p5.default_feed_dots == p5.paper_num * 72


def test_zero_energy_means_no_command():
    assert m.find_profile_by_name("GB01-0000").energy_for("text", 4) is None


def test_unsupported_reasons():
    assert not m.find_profile_by_name("FL01-0000").supported
    assert not m.find_profile_by_name("YMS-BT01-0000").supported
    assert all(p.supported or p.unsupported_reason for p in m.registered_profiles())


def test_advertisement_guard():
    assert not m.advertisement_contradicts([])
    assert not m.advertisement_contradicts(["0000af30-0000-1000-8000-00805f9b34fb"])
    assert m.advertisement_contradicts(["0000ff00-0000-1000-8000-00805f9b34fc"])
