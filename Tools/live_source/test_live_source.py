"""Live-source harness tests: MP4 parser, preflight contracts, ledger gates.

Run: python -m unittest test_live_source -v   (from Tools/live_source)
"""

import json
import os
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ledger
import preflight
from ledger import EVIDENCE_LADDER, Ledger, Take
from mp4probe import probe_mp4


def build_mp4(path: str, width=1920, height=1080, fps_num=60, seconds=2):
    """Minimal synthetic MP4: ftyp + moov(mvhd, trak(mdhd, hdlr, minf(stbl
    (stsd(avc1), stts)))) + mdat-free. Just enough for probe_mp4."""
    def box(t, payload):
        return struct.pack(">I4s", 8 + len(payload), t.encode()) + payload

    n_samples = fps_num * seconds
    media_ts = fps_num * 1000
    mdhd = struct.pack(">B3sIIIII", 0, b"\0\0\0", 0, 0, media_ts,
                       n_samples * 1000, 0)
    hdlr = struct.pack(">B3s4sIII", 0, b"\0\0\0", b"vide", 0, 0, 0)
    # stsd: version/flags + count + avc1 sample entry (w/h at offset 32)
    avc1 = struct.pack(">4s", b"avc1") + b"\0" * 28 + struct.pack(">HH", width, height) + b"\0" * 20
    stsd = struct.pack(">B3sI", 0, b"\0\0\0", 1) + avc1
    stts = struct.pack(">B3sIII", 0, b"\0\0\0", 1, n_samples, 1000)
    stbl = box("stbl", box("stsd", stsd) + box("stts", stts))
    minf = box("minf", stbl)
    mdia = box("mdia", box("mdhd", mdhd) + box("hdlr", hdlr) + minf)
    tkhd = struct.pack(">B3sIIIII", 0, b"\0\0\0", 0, 0, 1, 0, n_samples)
    trak = box("trak", box("tkhd", tkhd) + mdia)
    mvhd = struct.pack(">B3sIIIII", 0, b"\0\0\0", 0, 0, 1000, seconds * 1000, 0)
    moov = box("moov", box("mvhd", mvhd) + trak)
    ftyp = box("ftyp", b"isom\0\0\0\1isom")
    with open(path, "wb") as f:
        f.write(ftyp + moov)


class TestMp4Probe(unittest.TestCase):
    def test_probe_1080p60(self):
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "take.mp4")
            build_mp4(p)
            info = probe_mp4(p)
            self.assertEqual((info["width"], info["height"]), (1920, 1080))
            self.assertAlmostEqual(info["fps"], 60.0, places=1)
            self.assertAlmostEqual(info["seconds"], 2.0, places=1)

    def test_probe_4k30(self):
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "take.mp4")
            build_mp4(p, width=3840, height=2160, fps_num=30)
            info = probe_mp4(p)
            self.assertEqual((info["width"], info["height"]), (3840, 2160))
            self.assertAlmostEqual(info["fps"], 30.0, places=1)

    def test_rejects_non_mp4(self):
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "x.mp4")
            with open(p, "wb") as f:
                f.write(b"not an mp4 at all")
            with self.assertRaises(Exception):
                probe_mp4(p)


class TestClassify(unittest.TestCase):
    def test_sources(self):
        self.assertEqual(preflight.classify("Imports/Mocap/Rokoko/Inbox/IdleTest.fbx"), "ROKOKO")
        self.assertEqual(preflight.classify("Imports/Animations/Cascadeur/Inbox/CAS_Melusina_Idle_Serene.fbx"), "CASCADEUR")
        self.assertEqual(preflight.classify("C:/temp/OBS_Walk_01.mp4"), "OBSBOT")

    def test_protected_surface_rejected(self):
        self.assertFalse(preflight._protected_check("Content/Melodia/Characters/Melusina/x.fbx"))
        self.assertTrue(preflight._protected_check("Imports/Mocap/Rokoko/Inbox/IdleTest.fbx"))


class TestPreflight(unittest.TestCase):
    def test_rokoko_inbox(self):
        name = "IdleTestTmp.fbx"
        p = os.path.abspath(os.path.join(preflight.ROKOKO_INBOX, name))
        try:
            with open(p, "wb") as f:
                f.write(b"dummy")
            r = preflight.check_rokoko(p)
            self.assertTrue(r["in_rokoko_inbox"])
            self.assertTrue(r["verb_naming"])
            self.assertEqual(r["skeleton_verified"], "UNVERIFIED")
        finally:
            os.remove(p)

    def test_actual_rokoko_and_cascadeur_prefixes(self):
        self.assertTrue(preflight.VERB_NAME.match("A_Rokoko_GlideForward.fbx"))
        self.assertTrue(preflight.CAS_NAME.match("A_CAS_Melusina_Idle_Serene.fbx"))

    def test_cascadeur_naming(self):
        self.assertTrue(preflight.CAS_NAME.match("CAS_Melusina_Idle_Serene.fbx"))
        self.assertFalse(preflight.CAS_NAME.match("idle.fbx"))

    def test_obsbot_preset_flag(self):
        with tempfile.TemporaryDirectory() as td:
            good = os.path.join(td, "good.mp4")
            build_mp4(good)
            self.assertTrue(preflight.check_obsbot(good)["preset_1080p60"])
            bad = os.path.join(td, "bad.mp4")
            build_mp4(bad, width=1280, height=720, fps_num=30)
            checks = preflight.check_obsbot(bad)
            self.assertFalse(checks["preset_1080p60"])


class TestLedgerGates(unittest.TestCase):
    def test_advance_requires_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            led = Ledger(os.path.join(td, "l.json"))
            t = Take("ROKOKO_Idle_20260920_01", "ROKOKO", "Idle", "/x.fbx")
            led.upsert(t)
            t2 = Take("ROKOKO_Idle_20260920_01", "ROKOKO", "Idle", "/x.fbx",
                      evidence="CAPTURE_PROVEN")
            with self.assertRaises(ValueError):
                led.upsert(t2)
            t2.receipts.append("Saved/SemesterEvidence/receipt.md")
            led.upsert(t2)  # now legal
            self.assertEqual(led.takes[t2.take_id].evidence, "CAPTURE_PROVEN")

    def test_demotion_requires_blocker(self):
        with tempfile.TemporaryDirectory() as td:
            led = Ledger(os.path.join(td, "l.json"))
            t = Take("CASCADEUR_Walk_20260920_01", "CASCADEUR", "Walk", "/x.fbx",
                     evidence="RETARGET_PROVEN", receipts=["r.md"])
            led.upsert(t)
            t2 = Take(t.take_id, t.source, t.verb, t.path, evidence="CAPTURE_PROVEN",
                      receipts=["r.md"])
            with self.assertRaises(ValueError):
                led.upsert(t2)
            t2.blockers.append("neck_warp")
            led.upsert(t2)

    def test_persistence_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "l.json")
            led = Ledger(p)
            led.upsert(Take("OBSBOT_HarpBow_20260920_01", "OBSBOT", "HarpBow", "/x.mp4"))
            led.save()
            led2 = Ledger(p)
            self.assertIn("OBSBOT_HarpBow_20260920_01", led2.takes)

    def test_ladder_labels_exact(self):
        self.assertEqual(EVIDENCE_LADDER[0], "SOURCE_PREPARED")
        self.assertEqual(EVIDENCE_LADDER[-1], "PACKAGED_PROVEN")


if __name__ == "__main__":
    unittest.main()
