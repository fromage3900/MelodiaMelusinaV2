# SHOREWAKE — BOUNDED GOAL (updated 2026-10-07)

Replaces the framing of the v29 decision packet for the current push. Scope: the school
animatic delivery + the reel loop + the beauty stills. Blender 5.2 only. All claims
below are measured; receipts in `Saved/Audit/` (paths at the bottom).

## Mission (bounded)

Ship three artifacts from the one scene lineage by **Fri Oct 9, 5 PM**:

1. **ANMN301 animatic MP4** — 65.0 s, 1920x1080, 24 fps, silent, text layer complete
   (title, end, numbered panels). Status: **exists as v05 and passes the measured spec**
   (title/end text + panel numbers verified from extracted frames).
2. **The seamless SHOREWAKE loop** — 120 frames (5.0 s) of the starskiff at mooring;
   f1 == f120; 1080p24; the hero loop for the reel.
3. **Beauty stills set** — 6 x 1920x1080 frames from the loop scene (recipes in the
   shot plan).

Everything else (UE, new frameworks, new architecture) is out of scope.

## Definition of done (measurable)

- **Animatic:** file in `ANMN301_Animatic/`, 1560 f, 24 fps, 0 audio streams, title +
  end text present, panels numbered. [_v05 currently meets this; optional pacing trim
  of shots 12/15 and any panel refresh are owner calls._]
- **Loop:** all keyed-holder transforms f1==f120 (audited: PASS, 0.000 mm/deg); lantern
  flicker cycles 4.0 -> 5.12 -> 3.28 -> 4.0 (PASS); ocean time 0.2 -> 3.0 -> 0.2 (PASS);
  force fields close (PASS); every animation key inside 1-120 (PASS after the 2026-10-07
  wake-trail trim); pixel seam gate f1 vs f120 on the master at render time.
- **Stills:** 6 renders from named cameras per the shot plan, at least one carrying the
  full lookdev stack (fog-glow compositor pass, RT, star world).

## Current state (proven, with receipts)

- **Structure audit (2026-10-07):** 214 objects; 0 dead GN modifiers; 0 silent losses;
  0 stray/isolated objects; all textures resolve. Topology: 0 degenerate faces, 0
  non-manifold edges. Fixed: LaundryLine mesh weld (184->164 v; render-diff 0 px),
  Pennant -2 loose verts.
- **GN trees:** 47 trees, all wired and in use; every nested group reference resolves
  (an earlier "dead nested" alarm was an audit access-path error, corrected); pearl
  tree carries its repair (DIVIDE 20.3718, c2p EVALUATED). Litter: 5 provably-inert
  nodes found, wiring archived (`gn_litter_context_20261007.json`) - cleanup optional.
- **Animation audit (2026-10-07):** all 12 actions bound to 1-120 window; closures
  table all 0.000; the six "still" holders animate non-transform channels (force-field
  strength 0.012->0.035->0.012 / 0.025->0.07->0.025, ocean-modifier time, lyre
  rotation, hidden proxies). **One anomaly found and fixed:** the legacy wake-trail
  action carried 68 keys spanning f10-170; the 20 keys beyond f120 were removed and
  the action now sits cleanly inside the loop window.
- **FLIP Fluids:** audited in full. Domain = 43.2 m, res 400, obstacle = ProxyWater,
  cache dir `//SHOREWAKE_proxy_v03_skiff_flip_fluid_cache` - **cache does not exist;
  the sim was never baked.** The addon itself loads cleanly under 5.2 now, but a
  free-surface sim cannot close a seamless 120 f loop and a res-400 bake is out of
  budget anyway. **Resolution: parked** (FLIP Domain + fluid_surface hidden in render
  and viewport, disk + live). Deletion remains open owner call D4.
- **Lookdev (variant files, pending merge):** water extended (8.05 m -> 64.3 m, wave
  heights unchanged); EEVEE ray tracing ON; star world; compositor fog-glow tuned
  (6.6% pixel footprint); komikaze "tuned+" hybrids (50 materials / 172 assignments,
  GN-material sweep landed, lantern flicker intact).
- **Live session (as of tonight):** pearl restore + mesh fixes + animfix + FLIP park
  are STAGED in-memory (unsaved). Two stray objects exist only in the live session:
  `audvis_global_settings` (AudVis addon helper) and `x undo` (test leftover).

## The one structural step: assemble the master

`SHOREWAKE_LOOP_v5_master.blend` := structurefix+animfix lineage (geometry, fur, mesh
fixes, clean animation) + **lookdevstack** (water extent, RT, stars, fog-glow) +
**komikaze tuned+** (hybrid material set). One scripted pass on a copy with a
feature checklist: pearls 5246 v / 61 beads + aft instancing; water span 64 m; RT on;
comp chain R_LAYERS -> GLARE (Fog Glow, thr 1.2, size 6, str 0.7) -> GROUP_OUTPUT;
~50 hybrids; flicker cycles; seam gates re-run. Est. ~30 min, fully verifiable.
**Owner: say GO and it runs.**

## Work queue (ordered, bounded, after the master exists)

1. **Night value A/B** — one wide with water emission 3.0 -> ~1.0 for the night read
   (2 stills, preview only). Owner eyeballs, picks.
2. **Loop final render + seam gate + MP4** — 120 f, EEVEE 64 spp, headless; f1-vs-f120
   pixel gate; assemble MP4 (ffmpeg available at the hermes tools path). Unattended.
3. **Beauty stills** — 6 frames per shot plan.
4. **Animatic final** — verify v05 against the submission spec; optional: pacing trim
   (measured 2026-10-08: every shot <= 5 s; only action shots 13 = 3 s / 14 = 4 s run
   over the 1-2 s action guide — trim optional) and panel refresh
   (11 panels are still Sep-18 renders; 6 were refreshed Oct 6). Re-render only if
   the owner wants it.
5. **Optional polish windows** — nails audited 2026-10-08: all seated (0.000 m to hull) — no action needed; remove the 5 inert GN nodes;
   datablock-name hygiene; hide `LG_LightObj_0` (confirmed inert light at z=-18).

## Open owner calls (each answer is one line of work)

- D1 sail kiss: A (drop sail) or B (lift stays) — still open from v29.
- D2 carillon vs pagoda — still open.
- D3 keep the MoonWell deck basin as built — still open.
- D4 legacy deletions — now cleanly available: FLIP Domain + fluid_surface (parked,
  deletable), WakeTrail_legacy_flat (keys now window-clean). Guides/profiles stay.
- Komikaze final weights (tuned+ vs bolder) — pending your eye at full resolution.
- Night value pass direction (how dark should the sea go).
- Litter cleanup (5 nodes) + live junk objects (audvis_global_settings, "x undo").

## Fences / never

- Never save the live session for the owner; staged != saved.
- No git/p4 operations unprompted; no destructive git commands, ever.
- No FLIP bake before Friday (cannot loop; out of budget). FLIP stays parked.
- No re-topology beyond the audited fixes; no new scatter/compiler frameworks.
- One editor, one writer; all heavy work headless on copies; receipts in Saved/Audit.

## Receipts index

- `Saved/Audit/skiff_structure_audit_20261007.json` + `structurefix_receipt_20261007.json`
- `Saved/Audit/scene_full_audit_20261007.json` (render / lights / cameras / seam)
- `Saved/Audit/animfix_receipt_20261007.json` + `animfix2_receipt_20261007.json`
- `Saved/Audit/gn_litter_context_20261007.json`, `deadend_sweep_20261007.json`
- `Saved/Audit/night_pass1..7_receipt.json` (lookdev + komikaze passes)
- `Saved/Audit/pearl_restore_receipt_20261007.json`
- Scripts: `audit_structure.py`, `audit_full2.py`, `anim_deep.py`, `fix_anim_flip.py`,
  `trim2_fix.py`, `fix_structure.py`, `stage_animfix.py`, `stage_structurefix.py`
