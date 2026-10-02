"""
Shorewake animatic — rebuild the VSE and export the submission MP4.

Reads the numbered panels + real title/end cards from panels_final/ and
rebuilds the sequence from scratch, so the cut cannot inherit a strip from the
broken v3 file. Timing comes straight from SHOREWAKE_BEAT_BOARD.md:

    00 title   72f    01 120f   02 96f   03 48f   04 48f   05 72f
    06        120f    07 48f   08 48f   09 48f   10 48f   11 96f
    12        120f   13 72f   14 96f   15 120f  16 120f  17 96f
    18 end     72f                        = 1560f = 65.0s @ 24fps

The 3 permitted dissolves go on the beat board's own fade marks — shots
06, 13, 17 — as short cross dissolves at the strip boundaries.

Run:  blender -b --factory-startup --python build_vse.py
"""

import bpy
import os
import sys

ROOT = r"P:\MelodiaMelusinaV2-Laptop\Humber_FinalYear_Prep\ANMN301_Animatic"
PANELS = os.path.join(ROOT, "panels_final")
OUT_BLEND = os.path.join(ROOT, "SHOREWAKE_VSE_animatic_v04.blend")
OUT_MP4 = os.path.join(ROOT, "ShepherdBrennan_AnimaticCreation_2026-10-09_v04.mp4")

W, H, FPS = 1920, 1080, 24

# (name, filename, frames) — durations locked from the beat board, total 1560.
ORDER = [
    ("00_Title", "title.png", 72),
    ("PANEL_01", "panel_01.png", 120),
    ("PANEL_02", "panel_02.png", 96),
    ("PANEL_03", "panel_03.png", 48),
    ("PANEL_04", "panel_04.png", 48),
    ("PANEL_05", "panel_05.png", 72),
    ("PANEL_06", "panel_06.png", 120),
    ("PANEL_07", "panel_07.png", 48),
    ("PANEL_08", "panel_08.png", 48),
    ("PANEL_09", "panel_09.png", 48),
    ("PANEL_10", "panel_10.png", 48),
    ("PANEL_11", "panel_11.png", 96),
    ("PANEL_12", "panel_12.png", 120),
    ("PANEL_13", "panel_13.png", 72),
    ("PANEL_14", "panel_14.png", 96),
    ("PANEL_15", "panel_15.png", 120),
    ("PANEL_16", "panel_16.png", 120),
    ("PANEL_17", "panel_17.png", 96),
    ("18_End", "end.png", 72),
]

# Beat board: "(*) = the 3 allowed fades, marked for the VSE pass
# (Gamma Cross at 06/13/17 boundaries)."
#
# Blender 5.2 has NO StripModifier transition — the transition enum on a strip
# was removed, and StripModifiers only takes ADJUSTMENT-family types. The real
# mechanism is a GAMMA_CROSS *blend_type* on a strip that OVERLAPS the previous
# one on a lower channel. So a fade = the incoming panel starts `len` frames
# early on channel 2, with the outgoing panel still live on channel 1.
FADE_BEFORE = {"PANEL_06": 12, "PANEL_13": 12, "PANEL_17": 12}


def log(m):
    print("VSEBUILD %s" % m)
    sys.stdout.flush()


def main():
    missing = [f for _, f, _ in ORDER
               if not os.path.exists(os.path.join(PANELS, f))]
    if missing:
        log("ABORT missing from panels_final: %s" % missing)
        return

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    scn.render.resolution_x = W
    scn.render.resolution_y = H
    scn.render.resolution_percentage = 100
    scn.render.fps = FPS
    scn.frame_start = 1
    total = sum(d for _, _, d in ORDER)
    scn.frame_step = 1
    scn.render.use_sequencer = True
    scn.render.use_compositing = False

    # COLOUR MANAGEMENT — pass the panels through untouched.
    #
    # Each panel was already rendered to PNG through the 3D scene's view
    # transform. Blender 5.x defaults that to AgX, so the panels are already
    # tonemapped. The VSE then applies the transform AGAIN on the way to h264,
    # double-tonemapping the cut: measured 16-19 levels darker than the source
    # panels, with max channel delta 70. Standard = identity, so what was
    # rendered is what ships.
    scn.view_settings.view_transform = 'Standard'
    scn.view_settings.look = 'None'
    scn.view_settings.exposure = 0.0
    scn.view_settings.gamma = 1.0
    scn.display_settings.display_device = 'sRGB'
    scn.sequencer_colorspace_settings.name = 'sRGB'
    log("colour view_transform=Standard (panels pass through; AgX already baked)")
    # frame_end is set from measured coverage after the strips exist — the
    # dissolve extensions make it larger than the declared 1560, and leaving
    # it at 1560 would silently truncate the last dissolve.

    scn.sequence_editor_create()
    se = scn.sequence_editor
    strips = getattr(se, "strips", None)
    if strips is None:
        raise SystemExit("SequenceEditor.strips missing - 5.2 API drift")

    # A cross dissolve OVERLAPS two strips, so the overlap frames are shared,
    # not stolen. The schedule therefore has to be laid out as:
    #
    #   strip i  occupies  [cursor, cursor + dur)
    #   a fade-in on strip i+1  starts `length` frames BEFORE cursor+dur
    #
    # and the outgoing strip is EXTENDED by `length` so it stays on screen
    # through the whole dissolve. Shortening the incoming strip instead
    # (the obvious first guess) silently deletes `length` frames of runtime
    # per fade — 3 x 12 = 36 frames, a 63.5s cut that the coverage gate
    # correctly refused to export.
    #
    # So: every strip is laid at full `dur`, and a faded strip is additionally
    # given `length` extra frames of duration on the channel below.
    frame = 1
    for i, (name, fname, dur) in enumerate(ORDER):
        prev = ORDER[i - 1] if i else None
        length = FADE_BEFORE.get(name, 0) if prev else 0
        length = min(length, dur - 1) if length else 0

        # Faded strips go on channel 2 so they blend OVER the outgoing strip.
        channel = 2 if length else 1
        strip = strips.new_image(
            name=name,
            filepath=os.path.join(PANELS, fname),
            channel=channel,
            frame_start=frame,
            fit_method="ORIGINAL",
        )
        strip.frame_final_duration = dur
        if length:
            strip.blend_type = "GAMMA_CROSS"
            strip.blend_alpha = 1.0
            strip.use_default_fade = True
            # Extend the OUTGOING strip so the dissolve has something to
            # dissolve FROM. Without this the tail of the previous panel is
            # simply absent and the blend has no visible effect.
            outgoing = strips.get(prev[0])
            if outgoing is not None:
                outgoing.frame_final_duration += length
                log("fade %s->%s gamma_cross len=%d (extends %s to %df)"
                    % (prev[0], name, length, prev[0],
                       outgoing.frame_final_duration))
        log("%-10s %-16s f%4d-%4d (%df) ch%d%s"
            % (name, fname, frame, frame + dur - 1, dur, channel,
               "  +fade%d" % length if length else ""))
        frame += dur

    # The brief's "no gaps" is a coverage assertion: the cut must be exactly
    # the declared 1560f / 65.00s. A dissolve does NOT extend the runtime —
    # the outgoing strip is extended INTO frames the incoming strip already
    # owned, so the two share them. Coverage therefore stays at `total` and
    # the dissolves show up as measured OVERLAP, which is asserted separately.
    #
    # (An earlier version asserted covered - total == fade_total. That is
    # wrong: it would require each dissolve to add 12f of runtime, giving a
    # 66.5s cut against a beat board locked to 65s.)
    fade_total = sum(min(FADE_BEFORE.get(n, 0), d - 1)
                     for n, _, d in ORDER if FADE_BEFORE.get(n, 0))
    chk = sorted(strips, key=lambda s: s.frame_final_start)
    cursor = 1
    holes = []
    overlap_total = 0
    for s in chk:
        start = s.frame_final_start
        if start > cursor:
            holes.append((cursor, start - 1, s.name))
        elif start < cursor:
            overlap_total += cursor - start
        cursor = max(cursor, start + s.frame_final_duration)
    covered = cursor - 1
    for a, b, who in holes:
        log("GAP frames %d-%d before %s" % (a, b, who))
    log("strips=%d declared=%d covered=%d overlap=%d (want %d) duration=%.2fs"
        % (len(strips), total, covered, overlap_total, fade_total,
           covered / float(FPS)))
    if holes:
        log("FATAL %d gap(s) in the cut" % len(holes))
        return
    if covered != total:
        log("FATAL coverage %d != declared %d (%.2fs vs %.2fs)"
            % (covered, total, covered / float(FPS), total / float(FPS)))
        return
    if overlap_total != fade_total:
        log("FATAL overlap %d != declared fade total %d"
            % (overlap_total, fade_total))
        return
    scn.frame_end = covered

    # Blender 5.x gates video containers behind image_settings.media_type,
    # which defaults to IMAGE — with that set, FFMPEG is not merely rejected,
    # it is ABSENT from the file_format enum, so probing alone reports a build
    # without ffmpeg. Set media_type=VIDEO first, then choose the container.
    ims = scn.render.image_settings
    if hasattr(ims, "media_type"):
        ims.media_type = "VIDEO"
        log("media_type -> %s" % ims.media_type)
    fmts = [i.identifier for i in
            type(ims).bl_rna.properties["file_format"].enum_items]
    if "FFMPEG" not in fmts:
        log("FATAL no FFMPEG output in this build (%s)" % fmts)
        return
    ims.file_format = "FFMPEG"
    ff = scn.render.ffmpeg
    ff.format = "MPEG4"
    ff.codec = "H264"
    ff.constant_rate_factor = "HIGH"
    ff.ffmpeg_preset = "GOOD"
    ff.gopsize = 12
    # The brief is explicit: the animatic brief does NOT request audio, so the
    # export is silent. Do not add an audio strip to "improve" it.
    try:
        ff.audio_codec = "NONE"
    except Exception as e:
        log("audio set skipped: %s" % e)
    log("ffmpeg format=%s codec=%s audio=%s"
        % (ff.format, ff.codec, getattr(ff, "audio_codec", "?")))

    scn.render.filepath = OUT_MP4
    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
    log("saved blend -> %s" % OUT_BLEND)

    bpy.ops.render.render(animation=True)
    log("rendered mp4 -> %s" % OUT_MP4)
    log("DONE")


main()
