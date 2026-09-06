# 𝄞 Melusina House GN — Foundation → Shell Builder Roadmap

**Date:** 2026-09-04  
**Status:** current implementation roadmap  
**Canonical entrypoint:** `MELUSINA_HOUSE_GN_START_HERE.md`  
**Melodia Studio category:** **Melusina House**  
**Search tokens:** `Melusina House GN` · `MEL_mh_` · `MH Foundation` · `roof ribbon` · `opening family` · `porch stair`

> **This document answers one question:** what should an agent build next after the Melusina House foundation layer?

Do not use old `GN_MH_*` planning aliases as registry authority. Registered Melodia Studio builders use `MEL_mh_*`.

---

## ♬ Current truth

The house now has a real foundation layer in Melodia Studio:

```text
MEL_mh_foundation_pod
MEL_mh_foundation_cluster
MEL_mh_foundation_porch
MEL_mh_foundation_master
```

These are wired through the normal Melodia Studio chain:

```text
builder source
→ register_builder(...)
→ GROUP_BUILDERS / GROUP_METADATA
→ melodia_gn/__init__.py import
→ TREE_CATEGORIES
→ Melusina House GN Stack section
→ presets
```

Source/catalog integration is complete. **Live Blender 5.2 construction + visual evidence is still required.**

Do not call the new foundation builders visually proven until that smoke exists.

## ♪ Evidence state

| Layer | Source | Registered | Category / presets | Blender 5.2 smoke | Artist approved |
|---|:---:|:---:|:---:|:---:|:---:|
| Foundation Pod | ✓ | ✓ | ✓ | pending | pending |
| Foundation Cluster | ✓ | ✓ | ✓ | pending | pending |
| Foundation Porch | ✓ | ✓ | ✓ | pending | pending |
| Foundation Master | ✓ | ✓ | ✓ | pending | pending |
| `MEL_mh6_room_shell` | ✓ | ✓ | ✓ | re-smoke with new foundation | pending composition |
| `MEL_melusina_house_round_interior` | ✓ | ✓ | ✓ | re-smoke with new foundation | pending composition |
| AAA trim family | ✓ | ✓ | ✓ | existing family | defer until silhouette |
| House dressing family | ✓ | ✓ | ✓ | existing family | defer until silhouette |

Proof ladder:

```text
source exists
≠ registered
≠ visible in GN Stack
≠ constructs in Blender
≠ responds correctly to parameters
≠ visually matches Melusina House
≠ approved export asset
```

State the exact level you have.

---

# ♫ First task after pulling main — smoke the foundation

From repo root:

```powershell
git pull
python Tools/verify_melusina_house_gn_catalog.py
```

Then in Blender 5.2:

```text
Melodia Studio
→ GN Stack
→ Melusina House
→ MH Foundation Master
→ preset: ROUND_BAROQUE_DEFAULT
```

Change `Side Spread`, `Porch Offset`, and `Tower X`.

Required evidence:

```text
Saved/Audit/melusina_house/
├── foundation_top.png
├── foundation_front.png
└── foundation_three_quarter.png
```

Do not save the live v22 portfolio stage from agent automation.

### Foundation approval gate

The footprint should already read as rounded overlapping room pods, a broad central social heart, a clear front arrival platform, and a right-side Listening Tower counterweight. If it reads like a conventional cottage floor plan, fix the foundation before making a roof.

---

# 𝄞 Canonical next builder batch

Build **only these three first**:

```text
MEL_mh_roof_ribbon
MEL_mh_opening_family
MEL_mh_porch_stair
```

These are the shortest path from **foundation blobs** to **recognizably Melusina's House**.

Do not start furniture, shader genomes, foliage systems, Blue Room dressing, or Unreal Nanite assembly before this batch is visually proven.

## 1. `MEL_mh_roof_ribbon` — P1

**Purpose:** create the silhouette-defining roof grammar: broad main roof + offset wing roof + lower porch roof, reading as overlapping shell/ribbon/whale-back forms rather than ordinary gables.

Reuse existing Melodia Studio curve/profile/transform utilities first. Do not create a second generic curve-to-mesh framework.

Proposed interface:

```text
Roof Width
Roof Rise
Eave Curl
End Lift
Thickness
Asymmetry
Preview Density
```

Minimum graph contract:

```text
guide / ridge curve
→ controlled profile
→ Curve to Mesh
→ thickness
→ Mesh Bevel
→ output
```

Definition of done: one builder can produce main/wing/porch variants through parameters; roof reads clearly with ornament disabled; eave curl changes shape rather than merely scaling; it registers in **Melusina House**; at least two presets exist; Blender 5.2 screenshot proof exists.

**Do not put shingles inside this builder.**

## 2. `MEL_mh_opening_family` — P1

**Purpose:** one reusable house-specific window/door language instead of twenty bespoke boolean holes.

It should provide a visible frame branch plus a deliberately simple cutter volume.

First variants:

```text
Tall Arch
Round Rose
Turret Small
Entry Door
```

Proposed interface:

```text
Opening Type
Width
Height
Frame Depth
Moulding Width
Arch Rise
Inset
Cutter Depth
Ornament Amount
```

Reuse existing `MEL_arch`, gothic/opening tools, ornament frames, curve/profile helpers, and musical ornament builders. Wrap/compose them where possible instead of duplicating generic builders.

Definition of done: at least one tall arch and one round opening; cutter simpler than visible frame; repeated instancing is possible before boolean realization; registered in **Melusina House**; Blender proof on a simple wall shell.

## 3. `MEL_mh_porch_stair` — P1

**Purpose:** connect the new foundation porch to existing stair, railing, shell, pearl, and musical vocabulary.

Shape target:

```text
soft oval / crescent landing
→ curved or gently fanned steps
→ rising cheek curves
→ optional rail sockets
→ hero finial sockets
```

Proposed interface:

```text
Width
Rise
Run
Step Count
Fan
Cheek Curl
Rail Offset
Landing Depth
Hero Post Scale
```

Reuse existing stair/rail/baluster/curve-array builders first. This should be a **house composition wrapper**, not a new generic stair engine.

Definition of done: attaches cleanly to `MEL_mh_foundation_porch`; readable arrival path in clay; supports later rail/shell/pearl dressing without owning it; registered in **Melusina House**; Blender front and three-quarter proof.

---

# ♬ Second builder batch — only after the first three pass

Then build:

```text
MEL_mh_listening_tower
MEL_mh_shingle_distributor
MEL_mh_melusina_loop
```

### `MEL_mh_listening_tower`

Use the Foundation Master tower pad as its anchor. It is a slender vertical counterweight with lookout/listening niche, bell/chime sockets, and a small shell/dome cap. **Do not turn it into a castle keep.**

### `MEL_mh_shingle_distributor`

This is not a new scallop tile primitive. Reuse `MEL_mh_aaa_scallop_uv`; this builder owns controlled roof-wide distribution:

```text
roof surface / UV
→ stable row points
→ alternating offset
→ sample position / normal
→ orient
→ instance scallop variants
```

Keep instances unrealized in authoring preview.

### `MEL_mh_melusina_loop`

Create the stable house-specific curve DNA used later for rocaille, furniture silhouettes, rail details, crest paths, and pearl/fabric paths. This is a reusable ornamental gesture, not an all-purpose procedural ornament generator.

---

# ♪ Deferred architecture

Only after roof, openings, porch, tower, and shingles are stable:

```text
MEL_mh_blue_room_grotto
furniture composition wrappers
material genome pass
foliage / planter dressing
Unreal export / Nanite assembly
```

The Blue Room is important, but it should inherit stable house geometry rather than force the whole architecture system to mutate around one interior.

---

# ♫ Melodia Studio integration checklist

A house builder is not complete until all of these are true:

- [ ] implementation lives in `deploy/surreal_arch/melodia_gn/`;
- [ ] house-specific ID begins with `MEL_mh_`;
- [ ] `register_builder(..., category="melusina_house")`;
- [ ] module is imported through the addon registration path;
- [ ] derived registry data sees it;
- [ ] GN Stack displays it under **Melusina House**;
- [ ] description says what the builder owns and deliberately does not own;
- [ ] presets use exact interface socket names;
- [ ] no duplicate generic primitive was created unnecessarily;
- [ ] source verifier / manifest is updated if expected catalog changes;
- [ ] Blender 5.2 construction smoke passes;
- [ ] at least one parameter visibly changes geometry;
- [ ] evidence screenshot lands under `Saved/Audit/melusina_house/`;
- [ ] artist approval is recorded separately from technical smoke.

---

# 𝄞 Agent execution rule

When an agent is told **"continue Melusina House"**, the default action is:

```text
read MELUSINA_HOUSE_GN_START_HERE.md
→ read this roadmap
→ run Tools/verify_melusina_house_gn_catalog.py
→ smoke MEL_mh_foundation_master
→ inspect only the module relevant to the next builder
→ implement ONE builder
→ register it
→ preset it
→ Blender smoke it
→ capture evidence
→ update docs/status
```

Not:

```text
search every Docs/Plans file
→ infer architecture from old aliases
→ build five systems in parallel
→ declare success because Python source exists
```

## ♬ Agent-sized work packets

**Packet A — Foundation proof:** no new builder code; prove Foundation Master in Blender 5.2.

**Packet B — Roof:** only `MEL_mh_roof_ribbon`.

**Packet C — Openings:** only `MEL_mh_opening_family`.

**Packet D — Arrival:** only `MEL_mh_porch_stair`.

**Packet E — Silhouette integration:** foundation + room shell + roof ribbon + opening family + porch stair; capture clay front / three-quarter / side. No materials required.

---

# ♪ House silhouette gate

Before decorative production, the clay model must answer **yes** to:

1. Does the house read as round / layered before ornament?
2. Does the roof create the primary fantasy silhouette?
3. Is the Listening Tower location an intentional asymmetrical counterweight?
4. Is the entry sequence readable from game camera distance?
5. Do openings feel part of one architectural language?
6. Can major proportions change without rebuilding the graph?
7. Is it recognizably Melodia without musical-note decals?

If **no**, stay in structure.

---

# ♫ Current priority order

```text
NOW
├─ Blender smoke: MEL_mh_foundation_master
├─ MEL_mh_roof_ribbon
├─ MEL_mh_opening_family
└─ MEL_mh_porch_stair

NEXT
├─ integrated clay silhouette proof
├─ MEL_mh_listening_tower
├─ MEL_mh_shingle_distributor
└─ MEL_mh_melusina_loop

LATER
├─ Blue Room grotto
├─ AAA ornament composition
├─ furniture
├─ materials
├─ foliage
└─ Unreal export / Nanite proof
```

> **Foundation first. Then silhouette. Then language. Then ornament.** ♪