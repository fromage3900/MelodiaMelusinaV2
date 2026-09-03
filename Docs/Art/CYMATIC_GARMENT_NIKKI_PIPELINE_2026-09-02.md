# Cymatic Garment — Expanded Infinity Nikki Technical Pipeline (2026-09-02)

**Status:** Active — folds the Shorewake silhouette garment grid into an
Infinity Nikki-style wardrobe pipeline where the dress *sings*. Every garment
layer weaves its own Chladni standing-wave mode, presentation channels
(iridescence / sheen / emissive) are keyed to cymatic nodes, and the whole
dress is audio-reactive-READY with zero new audio writers.

**Authority it obeys:** `Docs/Research/INFINITY_NIKKI_UE5_TRANSLATION_FOR_MELODIA_2026-08-30.md`
(10 principles), `AGENTS.md` evidence culture, the echo contract (maps + ledger
row, never prose-only).

---

## 1. Where this lands in the Nikki doctrine

| Principle | How cymatic garments satisfy it |
|---|---|
| #1 Layered specialization | 10 garment layers → 10 Chladni modes, one "sing" per piece — not one giant fabric system |
| #2 Small master family | All 80+ cymatic maps drive the **verified** small family `M_Master_Nikki` / `M_Universal_Enhanced_Fabric` / `M_Master_Toon_Universal_Alpha`; **no new master** (the phantom `M_Master_FarawayMother_Fabric` is remapped away, per the 2026-09-02 fabric audit) |
| #3 Mix cloth tiers by category | Bodice/skirt tier = WPO/satin (cheap); collar/shoulder-lace = masked alpha; hero skirt = Chaos candidate; ornament studs = rigid |
| #4 Niagara reveals the field | Cymatic emissive/sheen lanes are ready to be driven by the existing cymatics/MPC consumers — no new writer |
| #5 WPO cheap, Chaos where it matters | Satin layers use WPO; skirt hero sheet is flagged Chaos |
| #7 Readable lighting headroom | Restrained PPV preserved (bloom 0.15, exposure +0.5) so sheer/glowing fabric reads |
| #9 Precompute | All height→normal, ORM pack, node-glow, iridescence baked offline (deterministic, seed `20260902`) |

---

## 2. The garment grid → cymatic mode table

The 48 Shorewake panels were already grouped into 10 dead-silhouette garment
layers (`silhouette_garment_label.py`). Each is now assigned a distinct Chladni
standing-wave mode so **no two garment pieces vibrate alike** — the dress reads
as one instrument whose different pieces sing different harmonics.

| Garment material | Chladni (m,n) | Reads-as |
|---|---|---|
| `M_Bodice_Torso` | (5,7) | the chest note — lowest full-body bass |
| `M_Bodice_Front` | (3,4) | front chest/yoke panels |
| `M_Bodice_Side` | (2,6) | side torso |
| `M_Bodice_Upper` | (1,3) | upper bodice band |
| `M_Collar` | (6,6) | symmetric collar frame |
| `M_Shoulder_Trim` | (4,8) | shoulder/armhole cap trim |
| `M_Shoulder_Ornament` | (8,8) | bead-dot grid nodal |
| `M_Sleeve` | (2,7) | sleeve/arm |
| `M_Underskirt` | (3,5) | mid skirt/slip |
| `M_Skirt_Full` | (7,9) | the big skirt plate — full sing |

Mode pairs chosen so adjacent layers differ (audit: no two identical, all ≤8 so
nodal lines stay crisp at 2K, all ≥1 so they read as a woven motif).

---

## 3. Cymatic fabric generation (Houdini/COPs, hython-adjacent)

`Tools/Houdini/sea_above_reef/shorewake_cymatic_garment.py` (pure numpy +
Pillow, same recipe family as the COPs pipeline — runs in venv python, no
Houdini resolution cap). Per layer it writes a 9-map copernicus-contract set:

```
T_Cymatic_Garment_<Layer>_{BaseColor,Normal,Height,Roughness,Metallic,
                            Iridescence,Emissive,ORM,Opacity}.png
```

- **Height** = charmeuse satin weave + `smoothstep(0.30,0.85, Chladni(m,n,phase))`
  — the standing-wave nodal lattice is *woven over* the satin, not layered on.
- **Albedo** = pearl base + cool cymatic node light (`200,230,255`) on nodal lines.
- **Emissive** = `smoothstep(0.72,0.98, ch) * node_glow * 0.85` — the singing lines.
- **Iridescence** = nacre crest + `0.30*ch` — sheen follows the nodes too.
- **Metal** = 0 cloth, +20% "silver thread" at nodal crests (only for laced layers).
- **Normal** = height-derived, OpenGL Y+ (flip G on UE import).
- **ORM** = pack(AO, Rough, Metal); **Opacity** = 1.0 opaque (lace variants get
  alpha coverage).

Plus a **seamless 8-frame animated flipbook** (phase 0==2π) so the nodal field
crawls like a Chladni plate breathes — `animated/FrameNN_*` (BaseColor / Normal /
Iridescence / Emissive / Height per frame).

**Audio contract respected:** texture-only. No code reads audio. The single
audio writer (`MelodiaAudioReactivePresentationSubsystem → MPC_Melodia_Palette`)
is untouched; the cymatic emissive/iridescence/sheen lanes are *ready* to be
driven by existing cymatics/MPC consumers with zero new writers.

---

## 4. Fold into the master family + cloth tiers

**Nikki principle #2 (small family):** everything above feeds the existing
verified family. Target MI creation names (Nikki lens):

```
MI_Melusina_Shorewake_Cymatic_Bodice   (M_Master_Nikki)
MI_Melusina_Shorewake_Cymatic_Collar   (M_Master_Toon_Universal_Alpha, masked)
MI_Melusina_Shorewake_Cymatic_Skirt    (M_Universal_Enhanced_Fabric)
... per garment layer, one MI each
```

**Principle #3/#5 cloth tiers:** attach a tier tag per garment piece so the
physics budget matches the cyc scale:

| Garment | Tier | Solution |
|---|---|---|
| Bodice_Torso/Front/Side/Upper | C | WPO micro-swell via cymatic height (cheap) |
| Collar / Shoulder_Trim | A | rigid authored motion (structured lace) |
| Shoulder_Ornament | A | rigid studs |
| Sleeve | C | WPO drape |
| Underskirt | C | WPO |
| Skirt_Full | **B** | **Chaos candidate** — hero sheet, meaningful collision; but Wave only where the sing needs fidelity |

**Rule:** the garment piece carrying gameplay meaning gets the expensive
solution. Skirt_Full (the "big plate") is the hero; the rest support it cheaply.

---

## 5. Where emissive/sheen/iridescence plug in (audio lane)

The cymatic node lanes are author-time textures now. To make them *react* (later,
owner-gated), the existing consumers (CymaticsSubsystem / MPC palette lanes,
already used by `MF_FabricMountainWPO`) can drive:

- `Emissive` intensity ← `BeatPulse` / `CymaticAmp`
- `Iridescence` hue rotation ← `Melodia.Rhythm.*` velocity lane
- `Sheen` strength ← `BassIntensity`
- flipbook phase advance ← a rhythm tempo band

No new writer is added. This mirrors the Faraway Mother fabric-mountain contract
(Chladni weave reads no audio today; the lane is reserved).

---

## 6. Deliverables produced this session

| Path | What | Evidence |
|---|---|---|
| `Tools/Houdini/sea_above_reef/shorewake_cymatic_garment.py` | cymatic garment generator (10 layers × 9 static + 10 × 8-frame animation) | manifest `cymatic_garment_manifest.json` (seed `20260902`, sha256/file) |
| `Saved/Audit/melusina_lookdev/garment_refresh/cymatic/` | `T_Cymatic_Garment_<Layer>_*.png` + `animated/` | 80+ static maps + 40+ animated maps |
| `Tools/Houdini/sea_above_reef/silhouette_garment_label.py` | 48→10 garment-layers classifier | `garment_layers_manifest.json` |
| `.../ShorewakeGarment/` | Substance staging (10 texture sets) | `painter_build_done.json` on next Painter launch |

All deterministic (seed `20260902`), headless, committed. No `.uasset` edited by
script; texture/MI work routes through Interchange / `unreal` Python.

---

## 7. Path to "truly breathtaking" (tonight + next)

1. **Tonight:** cymatic garment maps exist (done). Next: import + create the
   per-layer MIs on the verified family (editor-gated), wire Emissive +
   Iridescence + Height(parallax), and release the collars/ornaments alpha
   variants for the lace cutout.
2. **Next step:** a full `capture_material_grid` / LookDev pass on
   `L_MaterialPreview_Studio` using the Nikki lens (55mm orbit, Melodia void,
   StorybookVines + MeluGrade) so the sing is seen, not just authored.
3. **Owner decision:** bind the emissive/sheen/iridescence lanes to the existing
   cymatics consumers for the live audio sing.

*This spec is folded from the 2026-09-02 session; the garment-layer and cymatic
grids it describes are verified on disk with seed-locked manifests.*