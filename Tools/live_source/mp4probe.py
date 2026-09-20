"""MP4 preflight without ffmpeg — box-header parser (stdlib only).

Reads moov/mvhd for duration, the video trak's stsd for resolution, and
stts for an average frame-rate estimate. If the fast path fails (fragmented
MP4, unusual layout), the check reports UNVERIFIED instead of guessing —
per the project rule that unverifiable capture prep is labeled, not assumed.
"""

from __future__ import annotations

import struct


class Mp4ProbeError(Exception):
    pass


def _read_boxes(data: bytes, start: int, end: int):
    pos = start
    while pos + 8 <= end:
        size, box_type = struct.unpack_from(">I4s", data, pos)
        header = 8
        if size == 1:
            size = struct.unpack_from(">Q", data, pos + 8)[0]
            header = 16
        elif size == 0:
            size = end - pos
        box_type = box_type.decode("ascii", "replace")
        if size < header or pos + size > end:
            raise Mp4ProbeError(f"truncated box {box_type} at {pos}")
        yield box_type, pos + header, pos + size
        pos += size


def _find(data: bytes, box_type: str, start: int, end: int):
    for t, s, e in _read_boxes(data, start, end):
        if t == box_type:
            return s, e
    raise Mp4ProbeError(f"box {box_type} not found")


def probe_mp4(path: str) -> dict:
    with open(path, "rb") as f:
        data = f.read()
    if len(data) < 12 or data[4:8] != b"ftyp":
        raise Mp4ProbeError("not an MP4 (no ftyp)")

    moov_s, moov_e = _find(data, "moov", 0, len(data))

    # mvhd: version 0 -> 32-bit, version 1 -> 64-bit timescale/duration
    mvhd_s, _ = _find(data, "mvhd", moov_s, moov_e)
    version = data[mvhd_s]
    if version == 1:
        timescale, duration = struct.unpack_from(">IQ", data, mvhd_s + 20)
    else:
        timescale, duration = struct.unpack_from(">II", data, mvhd_s + 12)
    seconds = duration / timescale if timescale else 0.0

    # first video track: trak -> mdia -> minf -> stbl
    result = {"seconds": round(seconds, 2), "width": None, "height": None,
              "fps": None, "timescale": timescale}
    for t, trak_s, trak_e in _read_boxes(data, moov_s, moov_e):
        if t != "trak":
            continue
        try:
            mdia_s, mdia_e = _find(data, "mdia", trak_s, trak_e)
            minf_s, minf_e = _find(data, "minf", mdia_s, mdia_e)
            stbl_s, stbl_e = _find(data, "stbl", minf_s, minf_e)
            stsd_s, _ = _find(data, "stsd", stbl_s, stbl_e)
            # stsd: version/flags(4) + entry_count(4), then sample entry
            entry_off = stsd_s + 8
            w, h = struct.unpack_from(">HH", data, entry_off + 32)
            stts_s, _ = _find(data, "stts", stbl_s, stbl_e)
            entry_count = struct.unpack_from(">I", data, stts_s + 4)[0]
            total_samples = 0
            total_delta = 0
            off = stts_s + 8
            for _ in range(entry_count):
                count, delta = struct.unpack_from(">II", data, off)
                total_samples += count
                total_delta += count * delta
                off += 8
            mdhd_s, _ = _find(data, "mdhd", mdia_s, mdia_e)
            v = data[mdhd_s]
            media_timescale = struct.unpack_from(">I", data, mdhd_s + (20 if v == 1 else 12))[0]
            if total_delta and media_timescale:
                result["fps"] = round(total_samples / (total_delta / media_timescale), 2)
            result["width"], result["height"] = w, h
            return result
        except Mp4ProbeError:
            continue  # non-video trak or odd layout — try next trak
    raise Mp4ProbeError("no parseable video track")
