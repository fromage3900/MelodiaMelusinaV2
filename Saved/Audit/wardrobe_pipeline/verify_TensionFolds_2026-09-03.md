# Verify — Tension-fold loom v2 `MEL_garment_tension_folds` (2026-09-03)

**Gate:** **PASS** — builder restored + headless GN52 proof PASS, re-read from disk.

**Builder:** `MEL_garment_tension_folds` — *Garment Tension Folds* — Tension-driven folds: rest/deviation mask → normal displacement — Category `Garment`, seed **20260902**.

**Files restored** (from `aa4dc6d9` → `merge/unify-histories`, branch had dropped the garment lane):

| file | bytes | sha12 | note |
|---|---|---|---|
| `deploy/surreal_arch/melodia_gn/garment_tension_folds.py` | 6585 | `5ef6e16bebef` | target builder, 143 lines, 29-node tree |
| `deploy/surreal_arch/melodia_gn/garment_loom.py` | 14928 | `315dafc7ee18` | co-restored (GN52 proof needs all four) |
| `deploy/surreal_arch/melodia_gn/garment_audio_drape.py` | 7492 | `b8c86d8916d5` | co-restored |
| `deploy/surreal_arch/melodia_gn/garment_xpbd_drape.py` | 5329 | `8c045aa8a9c5` | co-restored (research lane) |
| `deploy/surreal_arch/melodia_gn/__init__.py` | 7590 | `b7399bc36790` | re-adds 4 garment imports + `_rebuild_derived_data()` |
| `deploy/surreal_arch/melodia_gn/presets.py` | 162424 | `9965a97efb61` | re-adds 3 loom+audio+**tension** + XPBD preset families |

**Tree (Blender 5.2.1 LTS `9e2066aef7ef`, `--factory-startup --background`):**

- `TREE_OK MEL_garment_tension_folds 29 nodes, 10 sockets` — matches v1 proof (29 nodes, FLOAT_VECTOR fix).
- **Chain verified:** `Position → StoreNamedAttribute(rest_position, FLOAT_VECTOR, POINT)` → `TexNoise(Vector=Position, W=Seed)` → `SUBTRACT 0.5 → MULTIPLY 2.0` signed deviation `s∈[-1,1]` → compression branch `negate × Compress Gain → Clamp[0,1]` + stretch branch `× Stretch Gain → Clamp[0,1]` → `ADD` fold mask → `SeparateXYZ(Y) → Y*6 → +Seed → SINE → (sin+1)*0.5` striation → `mask × striation × Strength` → `Normal → VectorMath SCALE → SetPosition(Offset)` → `StoreNamedAttribute(tension_fold, FLOAT, POINT)` → `Group Output`.
- **Gates:**
  - `SCALE_OK` — `ShaderNodeVectorMath` operation `SCALE` exists, `Scale` socket linked, `SetPosition.Offset` fed by `VectorMath` (not scalar).
  - `W_LINK_OK` + `TENSION_W_OK` — `Seed → TexNoise.W` linked via `sock()` (iteration-safe, no `inputs["W"]`).
  - `Clamp + SetPosition` present.
  - `PRESETS_OK ['PRESSED_PLEATS','STRETCH_CREASES','SOFT_GATHER']` → `PRESET_AUDIT_OK` — every preset key is a real input socket (filtered Music* passthrough):
    - `PRESSED_PLEATS {Strength:0.6, Compress Gain:2.5, Stretch Gain:0.2, Seed:20260902}` — sharp compression folds for pleated skirts.
    - `STRETCH_CREASES {Strength:0.5, Compress Gain:0.3, Stretch Gain:2.0, Seed:20260902}` — pull creases at seams/elbows.
    - `SOFT_GATHER {Strength:0.35, Compress Gain:1.0, Stretch Gain:0.8, Seed:20260902}` — balanced everyday drape.
  - Full input socket set re-read: `['Compress Gain','Music Influence','Musical Amplitude','Musical Freq A','Musical Freq B','Seed','Strength','Stretch Gain']` — the 4 Music* sockets are the universal musical post-pass added by `core.add_musical_sockets` (gate: `Music Influence==0` skips warp).
  - `label_tree` sections: `Rest Capture | Tension Field | Fold Mask | Detail + Displace`.

**Broader proof `Tools/wardrobe_pipeline/gn52_proof.py` — PASS:**

```
BUILDER_OK MEL_garment_uv_unwrap Garment UV Unwrap
BUILDER_OK MEL_garment_loom_variation Garment Loom Variation
BUILDER_OK MEL_garment_audio_drape Garment Audio Drape
BUILDER_OK MEL_garment_tension_folds Garment Tension Folds
TREE_OK MEL_garment_uv_unwrap 15 nodes, 6 sockets
TREE_OK MEL_garment_loom_variation 13 nodes, 9 sockets
TREE_OK MEL_garment_audio_drape 27 nodes, 15 sockets
TREE_OK MEL_garment_tension_folds 29 nodes, 10 sockets
W_LINK_OK / TENSION_W_OK / GN52_PROOF PASS
```

**What was re-read (not trusted):** `gn52_proof_tension.py` + `gn52_proof.py` both executed headless with `--factory-startup` (Blender 5.2.1 LTS `9e2066aef7ef`). No `success:true` taken on faith — trees, links, and preset audits are read back from `bpy.data.node_groups`.

**Rules upheld:** Seed 20260902, offline only, Blender headless only with `--factory-startup`, verified by re-reading, `core.sock()` for ALL lookups, VectorMath SCALE path, UE stays runtime writer, hand-paint staging stays OPEN.

Companion JSON: `verify_TensionFolds_2026-09-03.json`
