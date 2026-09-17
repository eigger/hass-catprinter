"""Frame, CRC, RLE and job-assembly tests."""

from __future__ import annotations

from catprinter_ble import protocol as p


def test_frame_bytes():
    assert p.cmd_get_state().hex(" ") == "51 78 a3 00 01 00 00 00 ff"
    assert p.cmd_get_info().hex(" ") == "51 78 a8 00 01 00 00 00 ff"
    assert p.cmd_feed(48).hex(" ") == "51 78 a1 00 02 00 30 00 f9 ff"
    assert p.cmd_feed(96).hex(" ") == "51 78 a1 00 02 00 60 00 f5 ff"
    assert p.cmd_quality(3).hex(" ") == "51 78 a4 00 01 00 33 99 ff"
    assert p.cmd_quality(5).hex(" ") == "51 78 a4 00 01 00 35 8b ff"
    assert p.cmd_mode("image").hex(" ") == "51 78 be 00 01 00 00 00 ff"
    assert p.cmd_mode("text").hex(" ") == "51 78 be 00 01 00 01 07 ff"
    assert p.cmd_stop().hex(" ") == "51 78 a6 00 01 00 05 1b ff"


def test_crc_matches_printer_replies():
    # Real X6h replies: CRC over payload only.
    assert p.crc8(bytes.fromhex("79 00 03 33 2e 30 2e 35 44 00")) == 0x07
    assert p.crc8(bytes.fromhex("00 0d 27")) == 0x1C


def test_rle_row():
    assert p.rle_row(bytes(384)) == bytes([0x7F, 0x7F, 0x7F, 0x03])
    assert p.rle_row(bytes([1] * 10 + [0] * 5)) == bytes([0x8A, 0x05])
    assert p.rle_row(bytes([1] * 130)) == bytes([0xFF, 0x83])
    assert p.rle_row(b"") == b""


def test_encode_row_picks_rle_or_raw():
    white = p.encode_row(bytes(48), 384)
    assert white[2] == p.CMD_RLE_LINE and white[4] == 4
    # Alternating pixels never compress: raw, LSB-first (0xAA -> 0x55).
    noisy = p.encode_row(bytes([0xAA] * 48), 384)
    assert noisy[2] == p.CMD_RAW_LINE and noisy[4] == 48 and noisy[6] == 0x55


def test_frame_parser_reassembles_split_and_joined_frames():
    parser = p.FrameParser()
    joined = bytes.fromhex(
        "51 78 a8 01 0a 00 79 00 03 33 2e 30 2e 35 44 00 07 ff"
        "51 78 a3 01 03 00 00 0d 27 1c"
    )
    frames = parser.feed(joined)
    assert [f.cmd for f in frames] == [0xA8]
    frames = parser.feed(b"\xff")
    assert [f.cmd for f in frames] == [0xA3]
    assert frames[0].direction == 1


def test_decoders():
    info = p.decode_info(bytes.fromhex("79 00 03 33 2e 30 2e 35 44 00"))
    assert info.device_type == "XW00121" and info.firmware == "3.0.5D" and info.wifi_state == 3

    state = p.decode_state(bytes.fromhex("00 0d 27"))
    assert state.conditions == () and state.fault is None and state.battery_raw == 0x27
    state = p.decode_state(bytes.fromhex("85 00 00"))
    assert state.conditions == ("out_of_paper", "overheating", "printing")
    assert state.fault == "out_of_paper" and state.is_printing

    assert p.battery_percent(0x27, 1) == 83
    assert p.battery_percent(0x28, 1) == 100
    assert p.battery_percent(0x22, 1) == 0
    assert p.battery_percent(0x27, 0) is None
    assert p.battery_percent(59, 2) == 60

    assert p.decode_flow(bytes.fromhex("10 70")) == "full"
    assert p.decode_flow(bytes.fromhex("00 00")) == "empty"


def test_build_print_job_layout():
    rows = [bytes(48)] * 250
    job = p.build_print_job(rows, 384, p.JobParams(energy=5000, speed=10, feed_dots=96))
    assert job.startswith(p.cmd_quality(3) + p.cmd_energy(5000) + p.cmd_mode("image") + p.cmd_speed(10))
    assert job.endswith(p.cmd_speed(25) + p.cmd_feed(48) * 2 + p.cmd_get_state())
    # Speed refreshed once, after row 200.
    assert job.count(p.cmd_speed(10)) == 2
    # No energy frame when the profile has none.
    job = p.build_print_job(rows[:1], 384, p.JobParams(energy=None, speed=10, feed_dots=0))
    assert p.CMD_ENERGY not in {job[i + 2] for i in range(0, len(job)) if job[i : i + 2] == p.MAGIC}
