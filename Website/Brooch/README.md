# Flower Brooch — website asset set (2026-09-17)

Everything here is generated from the live build of `Saved/MelusinasHouse/FlowerBrooch.blend`
via the lane tools (`Tools/brooch_pres_rig.py`, `Tools/brooch_web_anim.py`,
`Tools/brooch_sky.py`). Re-render anything with the commands at the bottom.

## stills/

48 JPGs: the hero in 8 sky variants x 3 views (front / three-quarter / macro).

    <variant>_<view>.jpg       full size (from the 1600x2000 masters)
    <variant>_<view>_800.jpg   800 px wide (web-optimized)

Variants: `editorial_dark` (the default site look), `forte`, `radiant` (the bright one),
`arcane`, `tide`, `stone`, `gale`, `umbral`.

## loops/

Seamless, muted-friendly, camera-driven loops (the piece never moves; the camera does).
Every loop is 4 s at 24 fps, 1080x1350, H.264 MP4 (faststart) + VP9 WebM.

    <loop>_<sky>.mp4 / .webm
    <loop>_<sky>_poster.jpg    frame 0, for the poster attribute

Loop types: `sweep` (front ping-pong arc, the hero loop), `detail` (macro arc across the
bead row and dangles), `bloom` (petal bloom ping-pong: the flower opens from a closed bud to
the full crown and back — drives the hero's "Bloom" GN socket; the piece itself animates in
this one, by design), `turntable` (full 360 orbit, on request).

Embed shape:

    <video autoplay muted loop playsinline poster="sweep_editorial_dark_poster.jpg">
      <source src="sweep_editorial_dark.webm" type="video/webm">
      <source src="sweep_editorial_dark.mp4" type="video/mp4">
    </video>

## Re-render / extend

    cd P:/MelodiaMelusinaV2-Laptop
    blender -b Saved/MelusinasHouse/FlowerBrooch.blend \
      --python Tools/brooch_pres_rig.py --python Tools/brooch_web_anim.py -- \
      --loop sweep --sky tide --frames 96 --res 1080x1350 --samples 32 \
      --out P:/MelodiaMelusinaV2-Laptop/Saved/Website/Brooch

Then encode (ffmpeg 9.x is on PATH):

    ffmpeg -framerate 24 -i frames/<tag>_%04d.png -c:v libx264 -pix_fmt yuv420p \
           -crf 18 -preset slow -movflags +faststart <tag>.mp4

Loop types: `sweep` | `detail` | `bloom` | `turntable`. Skies: any variant name, or `auto`
(genome-derived). Seamlessness: loop paths close and the dangle sway is set to 2 full cycles
per loop; the bloom loop adds a raised-cosine bloom curve (0 -> 1 -> 0, zero velocity at the
seam). Verify with `Saved/Audit/web_seam_check.py` (seam diff must be within ~2x of the
adjacent-frame diff).

Stills: the 1600x2000 masters live in `Saved/Audit/sky_<variant>_{front,tq,macro}.png`
(re-render with `Tools/brooch_pres_shot.py -- --sky <variant>`).
