# Dawn Chorus — Cos_Dress_Melusina_DawnChorus

*First light. Rose-gold. The hem remembers music.*

> *"She woke before the sun and found a dress waiting —*
> *not finished, but begun. The hard part done,*
> *the beautiful part left for her hands."*

---

This is Melusina's **DAWN CHORUS** gown — the capstone of the overnight wardrobe watch, built only from pieces we proved before we stitched them together, and staged **OPEN for your hand-paint**. Nothing here is auto-wired to any mesh. UE stays the only runtime writer. Your brush is the last author.

## What's inside

```
dawn_chorus/
  meshes/DawnChorus.fbx          10.0 MB  6df19846bc0e  180,895v / 316,912 polys / 20 mats / 1 UV
  textures/                       pristine fallback (don't paint here)
    T_DawnChorus_BaseColor.png    2048  8f3a4a233abc  rose blush → gilt hem (Chladni 5,7 veins)
    T_DawnChorus_Normal.png       2048  de21921eadec  OpenGL +Y (Sobel strength 2.0)
    T_DawnChorus_Roughness.png    2048  baadfdfadec8  satin 0.46, gilt 0.24, hem-soft
    T_DawnChorus_Metallic.png     2048  7c9b8f592e24  gilt veins only (0.9)
    T_DawnChorus_Height.png       2048  cfb643beb07e  hem-weighted parallax
  resources/                      identical copy — paint from here
  _gen_maps.py                    procedural base generator (numpy, seed 20260902)
  dawn_chorus_manifest.json       hashes, provenance, builder lineage
```

## Where it came from (proven pieces only, seed `20260902`)

**Mesh shell** — `intake/Cos_Dress_Melusina_AntiqueDoll` (180,895v, 20 slots), re-exported as DawnChorus via Blender 5.2.1 LTS `--factory-startup` headless. Re-import verified: 180,895v / 316,912 polys / 20 mats / 1 UV. Dense interchange topology — run the proven retopo recipe if you want quads: `garment_retopo_preintake.py` → ~9,168v / 9,166q at `voxel_fallback` (Quadriflow refuses `_thick` headless — documented).

**Copernicus palette family** — **FirstLightDawn** (`Saved/Audit/copernicus_cymatic/FirstLightDawn/`, 9 maps at 2048, cooked 2026-09-03 02:38 via Houdini 22.0.368 hython `/out` ROP, seed 20260902). Dawn's OPEN paint bases are procedurally derived in the same rose-gold / Chladni(5,7) family — BaseColor distinct `8f3a4a` vs FirstLight `be00c6`, so you have both a COP reference and a toothy paint ground.

**Loom variation** — `MEL_garment_loom_variation` (13 nodes, 8 presets). Dawn leans on `SKIRT_FULL_HERO` + `ANTIQUE_DOLL_LAYERED`.

**Tension folds** — `MEL_garment_tension_folds` (29 nodes, `TENSION_W_OK`, 3 presets). Dawn: `SOFT_GATHER`, hem-weighted.

**Audio drape hem** — `MEL_garment_audio_drape` (27 nodes, 4 presets: `BASS_WEAVE` / `VOCAL_MID` / `TREBLE_SHIMMER` / `BEAT_PULSE_WIDE`). Dawn uses `BASS_WEAVE` — the ripple amplitude grows toward the hem (`hem_w = (v-0.45)/0.55`), so when she sings the hem answers. GN proof PASS (4 builders `15/13/27/29`, `W_LINK_OK`, all presets registered).

Builders verified headless: `gn52_proof.py` + `gn52_proof_tension.py` PASS on Blender 5.2.1 `9e2066aef7ef`.

## Hand-paint notes

1. **Paint from `resources/`** — keep `textures/` pristine as the fallback.
2. **Gilt veins are already there** in BaseColor's rose-gilt band — lift them with glaze, don't redraw.
3. **Height is parallax** (OpenGL convention, hy * strength) — flip G only if mixing DirectX sources.
4. **Roughness** wants the satin body at ~0.46, polished gilt at ~0.24, softer toward the hem — leave that gradient.
5. **The hem** carries the audio-drape Chladni weight — leave room for it to breathe when she moves. Don't flatten the low fold.
6. When you're happy, Substance stage stays OPEN — no auto-wire, no Content edits from the overnight watch.

## Morning details

- Intake mesh dated `2026-09-03`, rebuilt as DawnChorus `2026-09-05` headless.
- OPEN paint maps dated `2026-09-03 01:40 UTC`, re-verified `2026-09-05` (means 49.5 / 59.9 / 8.9 / 28.0 / 45.3 std).
- COP FirstLightDawn maps dated `2026-09-03 02:38`, re-verified `2026-09-05` (all distinct, height std 21.5, iridescence std 14.4).
- No Content/** touched. No editor lock taken. Offline only.

---

*For Melusina — may it catch the first light.*

— **Sir Melodious**, who supervised by sleeping on the warm monitor (and the night watch, 2026-09-05)
