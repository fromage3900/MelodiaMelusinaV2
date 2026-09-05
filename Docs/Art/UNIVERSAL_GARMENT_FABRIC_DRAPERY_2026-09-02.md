# Universal Garment System — Fabric Drapery Pipeline (2026-09-02)

**Status:** Active — offline Houdini Vellum drapery + Vertex Animation Texture (VAT)
bake plan for the universal garment system's 10 Shorewake layers. Maps each garment
layer to a Nikki cloth-tier drape recipe. No editor, no `.uasset`, no landscape.

**Authority:**
- `Docs/Research/INFINITY_NIKKI_UE5_TRANSLATION_FOR_MELODIA_2026-08-30.md` §3–5,10 (cloth
  tiers A–D; cost ladder; "the piece carrying gameplay meaning gets the expensive solution")
- `Docs/Art/CYMATIC_GARMENT_NIKKI_PIPELINE_2026-09-02.md` (10-layer grid, Chladni modes,
  `M_Master_Nikki` / `M_Universal_Enhanced_Fabric` / `M_Master_Toon_Universal_Alpha` family)
- `Docs/Art/FARAWAY_MOTHER_CLOTH_TIERS_2026-09-02.md` (per-piece tier precedent)
- `AGENTS.md` evidence culture (manifests with recorded seed + sha256; claims verifiable on disk)

**Input garment grid (verified):**
`Saved/Audit/melusina_lookdev/night_pkg_2026-08-31/garment_layers_manifest.json`
(48 Shorewake panels → 10 garment layers / material groups; seed `20260902`).

---

## 0. Node presence — verified against Houdini 22.0.368

Headless `hython` cannot register the SOP node-type graph (`hdefereval` and `hou.nodeType`
return "graphical Houdini only" / `None`). Presence was therefore verified by filesystem
evidence shipped inside the install: per-node-type **Dialog config definitions** and
**help-example node directories**. Full JSON: `Saved/Audit/universal_garment/vellum_node_presence.json`.

**Vellum SOP nodes present (safe to use):**
`vellumsolver` · `vellumdrape` · `vellumconstraints` · `vellumattachconstraints` ·
`vellumconstraintproperty` · `vellumrestblend` · `vellumpostprocess` · `vellumpack` ·
`vellumunpack` · `vellumio` · `vellumrefframe` · `vellumxformpieces` · `vellumbrush` ·
`vellumconfiguremuscles` · `vellumconfiguretissue` · `vellumconstraints_grain`.

**Vellum DOP present:** `vellumsolver` · `vellumobject` · `vellumsource` ·
`vellumconstraintproperty` · `vellumconstraints` · `vellumrestblend`.

**`veler` NOT present** → the Vellum Erosion ("relax") node is **excluded** from all recipes.
Relaxation is instead achieved with the verified `vellumrestblend` (hold drape between runs)
+ `vellumpostprocess` (laplacian smoothing filter), which fill that role.

Every recipe below uses only verified nodes.

---

## 1. Cloth-tier doctrine (Nikki §3 + cost ladder §10)

| Tier | Meaning | Runtime cost | When |
|---|---|---|---|
| **A** | Rigid authored motion (bones / Control Rig, deterministic) | Cheap | Structured bodice, studs/ornament, support panels — sim adds noise |
| **B** | Soft pin (light Vellum soft-pin + settle, low-budget collisions) | Moderate | Structured lace/collar — subtle breath, no fold fidelity demanded |
| **C** | WPO / shader response (no sim) | Cheap | Distant fill, hidden underlayers, micro-swell |
| **D** | Offline Houdini Vellum sim + VAT bake | Expensive (precomputed) | **The hero drape** — the garment piece carrying gameplay meaning |

Cost ladder respected: Material/WPO → Niagara/instanced → authored transform/spline →
Chaos → **Houdini VAT/cache** → custom runtime.

**Project rule:** *the garment piece carrying gameplay meaning gets the expensive solution.*
The hero drape is **`M_Skirt_Full`** — the "big plate" that sings (Chladni `(7,9)`, the dress's
full-voice panel). Every other layer supports it cheaply.

---

## 2. Per-layer drapery table (garment → tier → sim approach → output)

| # | Garment layer (material) | Tier | Sim approach | Output (VAT/WPO/bone) | Rationale |
|---|---|---|---|---|---|
| 1 | `M_Bodice_Torso` | **A** rigid | None — bone skinning; optional cymatic **micro-swell WPO** on `M_Universal_Enhanced_Fabric` | Bone (+ optional WPO) | Structured torso band, the chest note. Deterministic skinning; sim = noise. |
| 2 | `M_Bodice_Front` | **A** rigid | None — bone skinning (yoke/corset panels) | Bone | Structured front/yoke. Rigid. |
| 3 | `M_Bodice_Side` | **A** rigid | None — bone skinning | Bone | Side torso panels. Rigid. |
| 4 | `M_Bodice_Upper` | **A** rigid | None — bone skinning | Bone | Upper band = **waist anchor** row that pins the hero skirt VAT seam. Rigid. |
| 5 | `M_Collar` | **B** soft pin | Houdini **Vellum soft pin** — pin collar edge to neck; low-resolve settle | Bone + light VAT (or bone) | Structured lace; scapula soft-pin for subtle breath; masked alpha; **≤2 overlapping translucent layers** (Nikki OIT lesson). |
| 6 | `M_Shoulder_Trim` | **B** soft pin | Houdini **Vellum soft pin** — tiny, 1-2 frame settle, no collision | WPO or bone | Small armhole cap trim. Cheap secondary. |
| 7 | `M_Shoulder_Ornament` | **A** rigid | None — bone (bead/stud clusters) | Bone | Decorative studs/beads — rigid studs, deterministic. |
| 8 | `M_Sleeve` | **C** WPO | **WPO drape** (cymatic height + gravity squash on `M_Universal_Enhanced_Fabric`); optional soft-pin later | WPO | Sleeve/arm. Cheap distant fill; no collision fidelity demanded. |
| 9 | `M_Underskirt` | **C** WPO / light Vellum | **WPO** (fallback) or very light Vellum drape **inside** the hero plate | WPO | Mid skirt / slip — hidden under the hero skirt. Cheap. |
| 10 | `M_Skirt_Full` | **D** hero VAT | **FULL Vellum drape + VAT bake** (see §3) | **VAT (hero)** | **The hero drape.** The big sing plate — gameplay-meaning garment. Expensive solution. |

**Hero drape target:** `M_Skirt_Full`.

---

## 3. Vellum drape + VAT bake plan (Tier D — `M_Skirt_Full`)

An offline, deterministic bake (`seed 20260902`). No runtime Vellum in-game.

### Stage 0 — Prep
- Input: `SM_ShorewakeDress_48MAT_v2` (48-panel merged dress) → split to the 10 garment
  groups per `garment_layers_manifest.json`.
- Per drapery layer build a **low-poly proxy** from the base mesh (standard remesh; the
  hero skirt proxy keeps the silhouette, ~flat-unfolded drape domain plus weld seams).
- Mark the **waistband/seam** group (`M_Bodice_Upper` edge) as the pin anchor.

### Stage 1 — Drape (settle)
- `vellumdrape` (Vellum Drape SOP, verified) auto-drapes the proxy onto body colliders
  (hip/leg/waist primitives) for the rest pose.
- `vellumconstraints` + `vellumattachconstraints` pin the waistband group to the
  `M_Bodice_Upper` anchor; collision separator configured on the `vellumsolver`.

### Stage 2 — Animate (sim)
- Drive `vellumsolver` over a **sampled run/pirouette cycle** exported from the Melusina
  ABP (typically 90–150 frames, 30 fps, x1 loop). Colliders = legs/hips static prims.
- `vellumrestblend` holds the settled drape between spawn (no drift on loop);
  `vellumpostprocess` applies a smoothing filter to the resolved cloth.

### Stage 3 — Bake VAT
- Capture **per-frame P** (and a packed normal when translucency needs it) for every sim
  vertex.
- `vellumpack` / `vellumio` pack the per-frame position-stream into a **RGBA16F VAT atlas**
  (row = frame; column = vertex-id → UV), exported once per drapery layer.
- Contracted to one 4K (target 8K) atlas + pose-range metadata (`frame_start`, `frame_end`,
  `fps`, `loop`).

### Stage 4 — UE import (editor-gated, offline spec only)
- Import VAT into `M_Master_Nikki` / `M_Universal_Enhanced_Fabric` **without a new master**:
  read VAT P in a WPO lane and blend by screen-importance LOD (close = full VAT blend;
  vista = VAT 0 + Toksvig 1.8, per Nikki P10).
- Target MI per the cymatic spec:
  `MI_Melusina_Shorewake_Cymatic_Skirt (M_Universal_Enhanced_Fabric)`.
- The gameplay "sing" (Chladni `(7,9)` emissive/iridescence lanes) rides *on top of* the VAT
  drape — same mesh, one hero motion source.

### Cost
- Bakes are offline; runtime cost is a sampled VAT texture + WPO read on the hero plate
  only. Zero Chaos/Vellum at runtime for the dress. Collar (B) is a light pin if wired.

---

## 4. Deliverables

| Path | What |
|---|---|
| `Docs/Art/UNIVERSAL_GARMENT_FABRIC_DRAPERY_2026-09-02.md` | This spec + drapery table |
| `Saved/Audit/universal_garment/fabric_drapery_pipeline.json` | Manifest (seed, chain, node-presence results, per-layer table) |
| `Saved/Audit/universal_garment/vellum_node_presence.json` | Vellum SOP/DOP presence evidence (Houdini 22.0.368) |
| `Saved/Audit/universal_garment/_vellum_check*.py`, `_vellum_probe2/3.py` | Verifier scripts (evidence trail) |

All offline, deterministic (`seed 20260902`), committed. No `.uasset` touched. The heroic
drapery budget lands entirely on `M_Skirt_Full`.