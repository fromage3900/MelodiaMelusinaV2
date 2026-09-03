# Overnight Houdini Learn Loop — 2026-08-28 → 2026-08-29

## Mission
Run an **autonomous overnight loop** that:
1. **Melusina Weight Lab** — auto-capture + QA on `choralsheep.fbx` (106 bones) → scale to Melusina 465
2. **Wool Evolution** — iteratively mutate 4 albedo modes + glow, render lit spheres, score, learn
3. **Recursive Learning** — each generation writes evidence, model proposes next mutation, loop
4. **Documentation** — every test auto-documented with renders, metrics, decisions

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    OVERNIGHT ORCHESTRATOR                        │
│  Tools/Houdini/overnight_orchestrator.py                        │
│  - Task queue (JSONL)                                           │
│  - Generation counter                                            │
│  - Evidence ledger (Echo-compatible)                            │
└──────────────────────┬──────────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  MELUSINA    │ │  WOOL EVOLVE │ │  DOCUMENT    │
│  WEIGHT LAB  │ │  + RENDER    │ │  EVERYTHING  │
│              │ │              │ │              │
│ - HIP builder│ │ - Mutate     │ │ - Markdown   │
│ - Capture QA │ │ - Lit render │ │ - Screenshots│
│ - Scale plan │ │ - Score      │ │ - CSV metrics│
│ - Delta Mush │ │ - Promote    │ │ - Auto-summary│
└──────────────┘ └──────────────┘ └──────────────┘
        │              │              │
        └──────────────┼──────────────┘
                       ▼
           ┌────────────────────────┐
           │   SHARED EVIDENCE DIR  │
           │ Saved/Audit/overnight/ │
           │  - generation_001/     │
           │  - generation_002/     │
           │  - ...                 │
           └────────────────────────┘
```

## Queue Schema (JSONL, one line per task)

```json
{"id": "W001", "type": "melusina_weight", "stage": "build_hip", "gen": 0, "deps": [], "status": "pending", "created": "2026-08-28T...", "params": {"source_fbx": "choralsheep.fbx", "test_mode": true}}
{"id": "W002", "type": "wool_evolve", "stage": "mutate", "gen": 1, "deps": [], "status": "pending", "params": {"mode": "B_worley12", "mutation": "worley_strength +0.02"}}
{"id": "W003", "type": "wool_evolve", "stage": "render", "gen": 1, "deps": ["W002"], "status": "pending", "params": {"mode": "B_worley12"}}
{"id": "W004", "type": "wool_evolve", "stage": "score", "gen": 1, "deps": ["W003"], "status": "pending", "params": {"metrics": ["wool_reading", "glow_subtlety", "nissi_softness"]}}
```

## Melusina Weight Lab — Phase 1 (Tonight's Test)

### Input
- `Content/Melodia/Companions/ChoralSheep/choralsheep.fbx` (47KB, 106 bones, proper UVs)
- `choralsheephi.fbx` (50MB hi-poly) for detail transfer

### HIP Pipeline (Tools/Houdini/melusina_weight_lab.hipnc)
```
/obj/melusina_weight_lab
  ├── geo_import_sheep      (File SOP → choralsheep.fbx)
  ├── geo_import_sheep_hi   (File SOP → choralsheephi.fbx)
  ├── bonecapture           (Bone Capture Biharmonic)
  │    └── settings: max_distance=auto, smoothing=3, mirror=xy
  ├── capture_clean         (Attribute Wrangle: clamp 4 influences, smooth groups)
  ├── capture_qa            (Attribute VOP: heatmaps)
  │    ├── zero_weight_heatmap
  │    ├── influence_count_heatmap (red >4)
  │    └── stretch_heatmap
  └── delta_mush            (Delta Mush for skin sliding)
  └── export_fbx            (ROP FBX → test_skinned.fbx)
  └── export_json           (Python SOP → boneCapture JSON)
```

### QA Outputs (Saved/Audit/melusina_weight_lab/gen_001/)
- `zero_weight_vertices.json` — list of vert IDs with 0 influence
- `influence_violations.json` — verts with >4 bone weights
- `capture_stats.json` — min/mean/max influence per bone
- `heatmap_zero_weight.png` — red = unskinned
- `test_skinned.fbx` — import to UE/Blender for visual QA

### Scale-to-Melusina Plan (Phase 2)
Same HIP, swap `choralsheep.fbx` → `SK_Melusina` (465 bones), adjust:
- `max_distance` per bone radius
- `mirror` plane = X
- `smoothing` 4-5 iterations
- Add `Bone Capture Regions` for hair/face/cloth separate
- Output same JSON + heatmaps for Blender import via `prep_melusina_weight_paint_base.py`

## Wool Evolution Loop — Phase 2 (Concurrent)

### State
- Gen 0 = 4 modes already baked (A_flat, B_worley12, C_worley25, D_pop) + glow
- Target: find the "perfect" wool albedo + glow for each PC that reads as *Infinity Nikki wool* under light

### Mutation Space
| Parameter | Range | Step |
|-----------|-------|------|
| Worley strength | 0.00 - 0.30 | 0.02 |
| Saturation | 0.35 - 0.55 | 0.03 |
| Glow strength | 0.04 - 0.18 | 0.02 |
| Fiber grain | 0.0 - 1.0 | 0.15 |
| Hue shift (per PC) | -5° .. +5° | 1° |

### Scoring (0-10 each)
1. **wool_reading** — does it look like wool not paint? (visual, Blender render)
2. **glow_subtlety** — visible only in gaps/dim, not rave (0=none, 10=perfect peek)
3. **nissi_softness** — matches Nikki palette dustiness (0=neon, 10=dreams)
4. **uv_stability** — no stretching on low-poly UV islands
5. **emission_balance** — glow color harmonizes with albedo

### Render & Learn
- Each gen: mutate 1-2 params per mode → render 12 PCs lit sphere (512) → auto-score via PIL heuristics + your eye on sheet
- Winner promotes to next gen + mutates further
- Loser archived with reason
- After 5 gens → promote best to "shipping" `Saved/Audit/choral_sheep/houdini_variants/`

## Documentation Pipeline

Every task writes to `Saved/Audit/overnight/generation_NNN/`:
```
generation_001/
  task_W001.json
  task_W002.json
  renders/
    B_worley12_PC00_C.png
    B_worley12_PC01_Cs.png
    ...
    _SHEET_B_worley12_gen001.png
  metrics/
    W001_capture_stats.json
    W002_scores.json
  summary.md
```

Auto-summary per generation → appended to `OVERNIGHT_LOG.md`
```
## Gen 001 (2026-08-28 23:12)
- W001: Melusina weight lab built, 106 bones, 0 zero-weight verts, 3 >4-influence
- W002: Wool mutate B_worley12 worley +0.02 → 0.14
- W003: Render 12 PCs lit sphere
- W004: Scores: wool=7.2, glow=8.1, nissi=7.8, uv=9.0, emission=7.5
- PROMOTE B_worley12 -> gen 002
```

## Recursive Learning Controller

`Tools/Houdini/recursive_learn.py` runs after each full gen cycle:
1. Reads all task results + scores
2. Fits simple linear model: `param → score` per mode
3. Proposes next mutations: `argmax(grad(score))` + noise
4. Writes next gen queue entries
5. If score > 8.5 on all 5 metrics for 2 gens → mark "shipping"

## Deploy Commands

```powershell
# 1. Build weight lab HIP
python Tools/Houdini/build_melusina_weight_lab.py --out Tools/Houdini/melusina_weight_lab.hipnc --test-sheep

# 2. Start overnight loop
python Tools/Houdini/overnight_orchestrator.py --max-gens 10 --modes A,B,C,D --start

# 3. Monitor (anytime)
python Tools/Houdini/overnight_orchestrator.py --status
# or tail Saved/Audit/overnight/OVERNIGHT_LOG.md

# 4. Morning review
cat Saved/Audit/overnight/OVERNIGHT_LOG.md
ls Saved/Audit/overnight/generation_*/
```

## Files to Create

| File | Purpose |
|------|---------|
| `Tools/Houdini/build_melusina_weight_lab.py` | HIP builder (sheep test + Melusina scale params) |
| `Tools/Houdini/overnight_orchestrator.py` | Queue runner, status, evidence ledger |
| `Tools/Houdini/recursive_learn.py` | Score → mutation proposal |
| `Tools/Houdini/mutate_wool.py` | Param mutation + render + score (stateless) |
| `Tools/Houdini/render_lit_sheet.py` | Fast Blender/PIL lit render for scoring |
| `Saved/Audit/overnight/queue.jsonl` | Task queue |
| `Saved/Audit/overnight/OVERNIGHT_LOG.md` | Human-readable log |

## Success Criteria (Morning Check)

- [ ] Melusina weight lab HIP works on sheep (0 zero-weight, <5 >4-influence)
- [ ] At least 3 wool generations complete with scores improving
- [ ] One mode hits ≥8.5 on all 5 metrics → promoted to shipping
- [ ] `OVERNIGHT_LOG.md` complete, every task has renders + metrics
- [ ] Scale-to-Melusina plan written with exact parameter changes

---

**Start command:** `python Tools/Houdini/overnight_orchestrator.py --max-gens 8 --modes A,B,C,D --start`

Let it run. Morning = data.