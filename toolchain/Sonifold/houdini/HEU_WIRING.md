# Sonifold -> Melodia HeartGate: wiring guide

Status 2026-10-24. Everything below was verified live on this machine
(Houdini 22.0.368 hython, BS_GodFile repo, Sonifold at `toolchain/Sonifold`).

## What is proven

| Claim | Evidence |
|---|---|
| Sonifold runs on this box (CPU mode) | 10 eigenpairs on sphere match theory (2,2,2,5.97=) |
| WaveHarp cymatic staff eigenmodes | `data/eigen/SM_Cymatic_A_clean.npz` (50 pairs) |
| HeartGate eigenmodes | `data/eigen/HeartGate_clean.npz` (50 pairs, 1.7 s) |
| Live Python SOP cooks per-frame audio in Houdini | `houdini/test_sonifold_sop.py` -> TEST PASS, frames respond to beats |
| Copernicus context scriptable from hython | node inventory + `sopimport` cooks clean |

## The three-layer architecture (do not collapse these)

1. **Offline eigenbank** (per shape, CPU minutes): `melodia_eigen.py` ->
   `data/eigen/<shape>.npz`. Watertight remesh first (voxel 0.12 m pitch +
   marching cubes + largest component); raw HDA cooks are unwelded shards.

2. **Author-time live drive** (Houdini/Houdini-Engine cook): Python SOP
   (`houdini/sonifold_live_sop.py` + `sonifold_live.py`) maps audio FFT ->
   LB coefficients (freqmatch: sqrt(lambda_k) affine-mapped to 50 Hz..Nyquist
   in log freq) -> per-vertex `sonifold_amp` + `Cd`. Position-matching lets one
   eigenbank drive any decorated variant of the shape.

3. **Runtime (UE)**: bake, do not cook live. HEU frame-range cook ->
   vertex animation texture / `sonifold_amp` -> existing cymatic master
   material path (MI_Nikki_Chaldni canon). No second material authority.

## HDA / Houdini Engine wiring

- Put the Python SOP **inside the HDA subnet** after the gate's output0 merge.
- Promote spare parms: `eigen_npz`, `audio_file`, `strategy`,
  `nmodes`, `modeoffset`, `gain`, `n_fft` (see `_DEFAULTS` in
  sonifold_live_sop.py). HDA = self-contained; HEU passes parms from UE.
- HEU: instantiate HDA -> set parms -> cook frame range -> read
  `sonifold_amp` point attrib -> bake to VAT. HEU is not a per-frame live
  driver; "live" during authoring = CHOP path (`chop_path` parm,
  Audio Device In -> numpyArray tail).
- Re-cook rule: eigenbank only changes when the SHAPE changes; audio/mode
  parms re-cook cheaply (npz + wav are mtime-cached).

## Copernicus (hero textures / pearlescence) - inventory verified on 22.0.368

Copernicus category (`Cop`, 383 node types) is present and scriptable.
Relevant verified nodes: `sopimport` (SOP->Cop via `soppath`, cooks clean),
`bakegeometrytextures` (tracer baker), `bakepreprocess` (UV/normal prep),
`geotolayer` / `layertogeo`, `layerfromattrib` (stamp sonifold_amp into a
layer!), `geoattribfromlayer`, `attribfromlayer`, `ramp` (spatial
horizontal/vertical/radial/concentric), `hsv` (hue shift), `crystalnoise`,
`bubblenoise`, `chladni`, `heighttonormal`, `heighttoambientocclusion`,
`heighttocaustics`, `sdftomono`, `sdftorgb`, `dilateerode`, `edgdetect`,
full `grunge_*` preset family.

OPEN: exact layer data-type chain (geometry layer -> image layer) needs one
GUI pass in the Copernicus editor; headless hython cook of image filters
after `sopimport` fails (type mismatch). Build the 5-node pearl graph in GUI,
save .hip, then automate from there.

## HeartGate hero-texture recipe (target)

- Base gild: `bakegeometrytextures` curvature/AO -> gold wear mask for
  MI_Copernicus_GildedLoom.
- Pearlescent veil (MI_Mother_Veil): crystalnoise/bubblenoise layer modulated
  by the Sonifold eigenbank (layerfromattrib on sonifold_amp) -> thin-film
  banding via hsv hueshift ramps -> export PNG -> UE MI emissive/iridescent
  params. Follow AUDIO_REACTIVE_CANON: textures are INPUTS to existing MIs,
  no new material writers.
- UVs: gate HDA needs a UV step (bakepreprocess method) before UDIM bakes.

## Repro commands

```
# eigenbank (venv)
USE_GPU=0 ./.venv/Scripts/python.exe melodia_eigen.py HeartGate_clean 50

# live SOP test
hython houdini/test_sonifold_sop.py

# audio-driven strip figure
./.venv/Scripts/python.exe <render frames_gate_live.npz via data/meshes/HeartGate_clean.obj>
```
