# Morning Brook & PCG Scatter — Implementation Plan

> **For Hermes:** research done; execute task-by-task with owner viewport gates. Single editor holder throughout.

**Goal:** L_MelusinaMorning gains PCG-scattered banks and a cute brook/lake where Melusina meets Mr Choral Sheep, using only Sea Above-proven Python features.

**Architecture:** Port the Sea Above heatmap-dress + live-PCG wiring recipe to Morning scale (meters, not kilometers); water via toon-native pond first, vendor lake only on owner nod.

**Tech Stack:** UE 5.8, Monolith editor Python, PCG live graphs, Oceanology lake kit (gated), toon water MIs, audit JSON.

---

## Context (verified 2026-09-15)

- Sea Above proven recipe (`melodia-sea-above-integration` skill): raycast-sampled heatmap → manifest (`Tools/PCG/build_sea_above_heatmap_dress.py`, golden-decay falloff) → height-aware apply (`Tools/PCG/apply_sea_above_heatmap_dress.py`) → persistence proof by close-and-reload, never by save-return. Only 3 PCG graphs verified live (spawner present): `PCG_Hero_ResonanceCathedral`, `PCG_Hero_XylophoneTrail`, `PCG_Hero_BellTreeGarden`; the rest of the 754-graph gallery is hollow until node-censused. Volume wiring: spawn `PCGVolume`, `set_graph`, scale, `comp.generate(True)` (force arg required), count ISM instances after the run.
- Morning census (offline actor scan): 38 StaticMeshActors, 7 Niagara, 6 PointLights + Spot, 1 PPV (`PPV_NikkiDream`, frozen four), 1 PCGVolume (graph unknown — audit first), 1 CameraActor (portfolio cam), bed, skiff, `BP_ChoralSheep_C`, state anchor, PlayerStart. Editor currently on `L_MelodiaMainMenu` — live sheep/camera coordinates resolve at execution, never hardcoded here.
- Water on hand: vendor `BP_OceanologyLake` + `M_Lake_Inst` + shoreline-wetness + underwater-glass + lake cues under `Plugins/Oceanology_Plugin/Content/Design/Lake/`; toon-side `MI_WaterClean`, `MI_Flat_water`, Copernicus silk-waterfall. Skill arbitration: Oceanology vendor track is `HOLD_VENDOR_INPUTS_MISSING` in the P0 ledger — owner call required before vendor FX lands in a shipping map.

## Approach

Two lanes, owner picks at Task 0. Recommended: water B first (shippable this week), A as the gated upgrade.

- Water A (vendor): `BP_OceanologyLake` scaled to a brook, `M_Lake_Inst`, shoreline wetness decal. Needs owner nod per ledger hold.
- Water B (toon-native, recommended): shallow pond disc + narrow brook ribbon meshes, `MI_WaterClean` (or Flat water tinted), banks dressed by PCG scatter (pebbles, grass tufts, petals), shoreline wetness via vertex-color/MI blend. Zero vendor dependency, zero ledger friction.

## Tasks

### Task 0: Owner picks water lane + brook route

**Objective:** One decision unlocks everything downstream.

**Files:** none.

**Step 1:** Present: (A) vendor lake, prettiest, ledger-gated; (B) toon pond, shippable now (recommended).
**Step 2:** Owner marks the brook route on the portfolio camera frame: bed → door → sheep-meet point. Screenshot or "from bed to sheep, hugging the window light" is enough.
**Step 3:** Record choice + route in `Saved/Audit/morning_brook_choice_2026-09-15.json`.
**Gate:** no placement before this file exists.

### Task 1: Load Morning, audit, never save yet

**Objective:** Live ground truth with zero footprint.

**Files:** read-only.

**Step 1:** `mesh get_level_actors` (or editor Python census) on `/Game/Melodia/Levels/Opening/L_MelusinaMorning`: sheep label + transform, camera transform, existing PCGVolume label + graph + scale, bed/skiff/door positions, floor bounds + Z.
**Step 2:** Node-census the existing PCGVolume's graph (`nodes` property, spawner-class check per skill recipe). If hollow, it gets replaced in Task 3, not repaired.
**Step 3:** Write `Saved/Audit/morning_brook_census_2026-09-15.json` (actors, transforms, floor Z, existing volume verdict).
**Step 4:** Verify dirty packages reflect load churn only; SAVE NOTHING this task (Sea Above rule: load dirties ~all WP payloads; saving now writes 64 unintended files).

### Task 2: Morning heatmap (hand scale, not kilometers)

**Objective:** A density field from the REAL floor, Sea Above method shrunk to the room.

**Files:** create `Tools/PCG/build_morning_brook_heatmap.py` (new, modeled on `build_sea_above_heatmap_dress.py`); output `Saved/Audit/morning_brook_heatmap.json`.

**Step 1:** Raycast grid over the room bounds from the census (seed-locked, e.g. seed 2026; document it).
**Step 2:** Zones: `banks` (brook ribbon offset band, full density), `petal_drift` (window-light to bed, mid), `vista` (corners, sparse). Falloff: golden decay `rho = (D/(d+D))^1.618`, D ≈ room-scale band (e.g. 300uu), no hard floors.
**Step 3:** Scatter inventory from REAL meshes only (verify each `load_asset` non-null before manifesting; phantom refs killed the 2026-09-02 veil kit): pebbles, grass tufts, petals (`NS_Melodia_PetalLoop` family is the legitimate melodic use).
**Step 4:** Manifest schema `melodia.morning_brook_heatmap.v1` with per-point mesh + density + clearance; counts committed in the JSON (ledger == manifest rule).

### Task 3: Place PCG volumes (live graphs only)

**Objective:** Two volumes max, both generating on first run.

**Files:** modify level only (no new graphs).

**Step 1:** Bank volume: spawn `PCGVolume` over the brook ribbon, 3–5m box scale (Morning is meters — NOT the 8000uu cathedral size), `set_graph` to a census-verified LIVE graph (`PCG_Hero_BellTreeGarden` generates standalone; `XylophoneTrail` needs spline coverage — use only with a brook spline actor in range).
**Step 2:** Petal-drift volume: second `PCGVolume` on the window→bed lane, same live-graph rule.
**Step 3:** `comp.generate(True)` each; count ISM instances (exist only after success); expected counts recorded from the run into the apply report. Zero instances = stop, diagnose, never proceed to water.
**Step 4:** If the pre-existing Morning PCGVolume is hollow (Task 1), repoint or remove it — one volume owner, no duplicates.

### Task 4: Lay the water (chosen lane)

**Objective:** A brook a sheep would drink from.

**Lane B steps:** place pond disc + ribbon meshes at sheep-meet point (raycast-snapped Z, clearance per manifest); assign `MI_WaterClean`; bank ring from Task 3 scatter; shoreline wetness blend at the waterline; 1 PointLight warm kiss if the census shows budget (7 exist — restrained).
**Lane A steps:** spawn `BP_OceanologyLake`, scale to brook, `M_Lake_Inst`, wetness + underwater glass, cue hookup muted by default.
**Step N (both):** height-aware verify — every scatter/water point raycast-snapped, no fixed-Z floats (the drowned-canyon lesson, room scale).

### Task 5: Persistence proof + viewpoint gate

**Objective:** On disk AND beautiful, in that order.

**Step 1:** `save_dirty_packages(True, True)`; confirm NEW payload files under `Content/__ExternalActors__/Melodia/Levels/Opening/L_MelusinaMorning/` + dirty flag clears. No new files = owner sees nothing = stop and diagnose.
**Step 2:** Close-and-reload `L_MelusinaMorning`; re-enumerate PCG ISM counts; identical = on disk.
**Step 3:** Owner at the portfolio camera: cute verdict. Sheep sightline to water readable, ink calm (FXAA lock holds), dawn light untouched (lookdev skill §5 recipe stands — no PPV changes in this plan).

## Validation

- `morning_brook_choice_*.json`, `morning_brook_census_*.json`, `morning_brook_heatmap.json`, apply report with ISM counts — all in `Saved/Audit/`, counts agreeing everywhere.
- Reload proof (counts identical before/after), never save-return or mtime.
- Beauty gate: owner eyes only; agent captures never count.

## Risks

- WP load churn: loading Morning dirties ~64 payloads; save only after real mutations, and say so in the report.
- Hollow graphs: names lie; spawner check or it didn't happen. Never build a 755th graph — wire the 3 live ones.
- Vendor hold: lane A without the owner nod repeats the ledger fight. Default to B.
- Single editor holder; `generate(True)` force arg required; `set_actor_location` takes 3 args (loc, sweep, teleport).
- Scope: no new landscapes (owner hard rule), no PPV surgery, no parallel audio writer (MPC single-writer stands — materials may READ BeatPulse, never write).
- Behind this plan, untouched: Greybox 11-mat conversion, Morning canonical commit (map + actors), MI reset revert offer.
