# UNIVERSAL GARMENT SPATIAL 3D — Shorewake spatial-relation engine

**Date:** 2026-09-02 · **Seed:** `20260902` · **Status:** Offline architecture spec — headless, verify-on-disk, no editor
**Manifest:** `Saved/Audit/universal_garment/garment_spatial_3d.json`
**Input SBOM:** `Saved/Audit/universal_garment/garment_spatial_3d_inputs_sbom.json`

---

## 1. What this is

An offline spatial-relation engine over the Shorewake garment/body stack. It detects, quantifies,
and reports five capabilities — **per-pose, deterministic, verifiable on disk** — so the wardrobe
pillar follows the **Infinity Nikki clipping doctrine** (precompute expensive garment/body
intersections; never solve them at runtime). It is the quantified, pose-aware authority behind the
`HDA_CH_WardrobeIntersectionAudit` target (Nikki translation §6) and plugs into the **World Field
Bus** (Resonance / Tension) laid down in the Emerging-Toolchain Master Index §5.

> **Non-negotiable:** this spec is **headless**. No Unreal editor, no `Content/**/*.uasset` writes,
> no git clean/checkout, no new landscape, no live mesh_query. All five classifications are pinned to
> concrete, locally-verifiable core implementations.

---

## 2. Authority it obeys

| Source | Clause | Role |
|---|---|---|
| `Docs/Research/INFINITY_NIKKI_UE5_TRANSLATION_FOR_MELODIA_2026-08-30.md` §6 | HDA_CH_WardrobeIntersectionAudit (body + garment stack + pose samples → penetration heatmap / body hide groups / problem frames / min separation field / corrective target candidates) | HDA target this spec formalizes |
| `Docs/Research/EMERGING_TOOLCHAIN_MASTER_INDEX_2026-08-31.md` §5 / §5b | World Field Bus contract: `FilterFlow / Tension / Moisture / Contact / Residue / Reaction / AnchorStability / Resonance` | field names this engine publishes to |
| `Docs/Art/CYMATIC_GARMENT_NIKKI_PIPELINE_2026-09-02.md` §2 | 48 Shorewake panels → **10 dead-silhouette garment layers** with Chladni modes + cloth tiers | the garment-stack grid this engine operates on |

---

## 3. Inputs

```
body (SK_ShorewakeDress_Melusina465.fbx, retargeted, binary)
   + garment-stack (48 panels -> 10 garment layers)
   + poses (466 animation Takes from the retargeted FBX + authored QA poses)
   = outputs
```

**Verified on disk (sha256 in input SBOM):**

| Input | Path | Evidence |
|---|---|---|
| Retargeted dress FBX | `Saved/Audit/melusina_lookdev/retargeted/SK_ShorewakeDress_Melusina465.fbx` | binary Kaydara FBX, 22.35 MB, **466 Take records** (pose-sample source), 6 Vertices / 1 PolygonVertexIndex sections — sha256 `685f0634…` |
| 48-slot material map | `Saved/Audit/melusina_lookdev/dress_materials_manifest.json` | slot 0–47, `SW_Dress_P01…P48` ← `dressedit7…54` (orig_panel cross-ref), poly/vert counts |
| Body/garment passA inventory | `Saved/Audit/melusina_lookdev/magical/passA_inventory.json` | dressedit mesh list incl. `dressedit54` 69145 verts / 68419 polys, `dressedit53` 46134/45884, `dressedit8` 23058/22621, `dressedit7` 13034/25788 |
| Cymatic garment manifest | `Saved/Audit/melusina_lookdev/garment_refresh/cymatic/cymatic_garment_manifest.json` | 10-layer × Chladni(m,n) seed-locked grid |

### The 10-layer garment stack (operating grid)

| Garment material | Chladni (m,n) | Tier | Solution | Role in spatial engine |
|---|---|---|---|---|
| `M_Bodice_Torso` | (5,7) | C | WPO micro-swell | skin-tight chest — highest body-penetration ratio |
| `M_Bodice_Front` | (3,4) | C | WPO | front chest/yoke |
| `M_Bodice_Side` | (2,6) | C | WPO | side torso |
| `M_Bodice_Upper` | (1,3) | C | WPO | upper bodice band |
| `M_Collar` | (6,6) | A | rigid authored | masked alpha — translucency depth-sort case |
| `M_Shoulder_Trim` | (4,8) | A | rigid | armhole cap guard |
| `M_Shoulder_Ornament` | (8,8) | A | rigid studs | nodal bead-dots — occlusion case |
| `M_Sleeve` | (2,7) | C | WPO drape | arm flexion → pose-adaptive penetration |
| `M_Underskirt` | (3,5) | C | WPO | inner slip — near-body, occluded by outer sheet |
| `M_Skirt_Full` | (7,9) | B | **Chaos candidate** | hero plate — self & inner-layer intersection risk |

---

## 4. Outputs (classification surface)

```
penetration_heatmap            per-vertex signed penetration depth (inside body = negative)
body_hide_groups               per garment region: body sub-mesh point groups to hide (Nikki hide-mask)
problem_frames                 per-pose subset flagged on min-separation clearance breach
min_separation_field           distance field of min adjacent-layer & garment-body separation (depth-sort input)
layer_ordering                 depth-sort order of the 10 garment materials for any view direction
corrective_targets             recurring-intersection morph-target clusters (pose-space correction candidates)
```

---

## 5. Core implementations (concrete + verifiable)

### A1 — Houdini VDB signed-distance / proximity  *(primary, verifiable)*
- **Tool:** headless `hython` — verified `C:/Program Files/Side Effects Software/Houdini 22.0.368/bin/hython.exe`.
- **Method:** fit a clothing body proxy; build a dense **latent SDF** (`VDBCreateFromVolume` /
  iso-offset) of the body surface; evaluate each garment vertex and a thin outward shell.
  `penetration = signed_distance < 0` with a near-zero clamping epsilon for surface contact.
- **Outputs:** per-vertex penetration scalar → `penetration_heatmap`; dense voxel field retained as
  the latent `min_separation_field`.
- **Resonance/field reuse:** the latent field is the shared body-proxy field (CFG_1) so all 10 layers
  read one comparable field across all 466 poses.

### A2 — numpy nearest-points on the retargeted FBX  *(independent cross-check, verifiable)*
- **Tool:** `python3` + `numpy` 2.4.6 (present) + `scipy.cKDTree` / `trimesh` over the retargeted FBX.
- **Method:** KDTree over body vertices; nearest-point distance per garment vertex;
  **sign by `dot(N_body, P_garment − P_body_near)`** → inward (penetration) vs outward (clearance).
- **Outputs:** a second, independent `penetration_heatmap`; reconciles with A1 (same units, cm).

### A3 — mesh_query / Monolith HDA assembly  *(NOT run headless — reserved socket)*
- `HDA_CH_WardrobeIntersectionAudit` (body + garment stack + pose samples → the five outputs) is the
  editor-gated consumption surface. This spec prescribes its input/output contract **but does not
  execute** it headless. Requirement note: *mesh_query may not be run* — so the offline engines A1/A2
  are the verifiable core; A3 stays the bake/socket target.

### A4 — layer ordering / depth-sorting of the 10 garment materials  *(verifiable)*
- **Method:** per-layer mean radius + spine-relative reveal direction; produce a **static material
  draw-order** plus a **per-view depth-sort** using the `min_separation_field`, so translucency
  (`M_Collar` masked alpha, `M_Skirt_Full` sheen) resolves correctly. Respects the Nikki OIT caution
  (§5): minimize overlapping translucent layers, prefer masked/dithered, authored layer priority —
  no engine fork.

### A5 — corrective morph targets for recurring intersections  *(verifiable)*
- **Method:** across `problem_frames`, cluster per-vertex displacement vectors via
  **numpy k-means** → one **corrective-morph target** per recurring-intersection region;
  each target = an authored mesh edit toward the precomputed reveal of that region, feeding
  Control Rig / pose-space correction (Nikki doctrine: corrective morphs for recurring intersections).

---

## 6. World Field Bus mapping

Reuses the **existing** field names from Emerging-Toolchain Master Index §5 (`WorldField.Resonance /
Tension / Contact / …`) — never names new fields (anti-duplication §9 rule 5).

| World Field Bus field | Source output | Semantic |
|---|---|---|
| `WorldField.Resonance` | penetration_heatmap (volume × per-layer Chladni nodal signature) | how strongly the garment stands/sings against the body at a point |
| `WorldField.Tension` | min_separation_field + penetration depth | how strongly a garment draws/pulls/compresses at a location (low separation = high tension) |
| `WorldField.Contact` | body_hide_groups + proximity | garment↔body contact regions (where hide masks apply) |

Resonance/Tension here integrate the §5b-i cymatic publishers (CymaticsSubsystem Chladni ModeN/ModeM →
Resonance; SampleCymaticAmplitude → Tension) with the garment spatial truth.

---

## 7. Risk ranking (penetration risk per garment article)

Highest-risk articles for penetration, grounded in the verified mesh counts and layer geometry:

1. **`M_Skirt_Full`** — the largest plate (`dressedit53/54`: 45884→68419 polys, 46134→69145 verts),
   **Tier B Chaos** = self-intersection on movement; hem volume interacts with the entire inner stack.
   _Highest overall risk_ (#1).
2. **`M_Underskirt`** — inner skin-cling slip, smallest body offset within the skirt stack → body
   penetration + outer-sheet occlusion.
3. **`M_Bodice_Torso`** — skin-tight torso panels (`dressedit7` 25k poly region), smallest body
   clearance → highest **body-to-garment** penetration probability.
4. **`M_Sleeve`** — arm-compression on bend/stride poses → pose-adaptive intersection.

---

## 8. Evidence culture (verified on disk)

- **Seed-locked manifests:** `garment_spatial_3d.json` (seed `20260902`), `garment_spatial_3d_inputs_sbom.json`
  (sha256 of all 7 input files verified present).
- **Tool-chain verified present:** Houdini 22.0.368 + `hython.exe`; `python3` + numpy 2.4.6; scipy/trimesh path.
- **No editor, no Content/.** All five classifications prescribed with headless, locally-verifiable cores;
  A3 (mesh_query) is reserved for the editor-gated HDA bake only.

---

*This spec is the offline contract for the warp/clipping audit; it formalizes the Nikki §6
`HDA_CH_WardrobeIntersectionAudit` input→outputs and maps them to the World Field Bus.*