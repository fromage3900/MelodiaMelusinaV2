# Melusina HDA Native Pipeline — Technical Breakdown (2026-10-29)

**Status:** runtime set promoted; source/native geometry is proven identical in
hython. The first pass was Object-level; the SOP-level rebake is now the
container. Both SOP salon variants still cook over-height in UE
(`engine_y_up=1`: 14.97 m; `engine_y_up=0`: 17.29 m) while Houdini is 7.90 m; the
source Python control did not cook headlessly, so the UE Houdini Engine
import/cook path is the remaining open cause. P0 placement is pending.
`CURRENT_STATE.md` remains the sole status authority.

## 1. What this is

A production pipeline for turning the Melusina/Poitou room-shell HDAs into **native,
self-contained runtime HDAs with no embedded PythonModule**, while keeping the
parametric authoring sources intact. Eight runtime finals are promoted; four
authoring/experimental bakes are archived separately.

The native set is recorded in
`specs/housing/hda_native_registry.v1.json` with source type, native type, point/prim
counts, receipt, and UE asset path.

## 2. The failure that forced it

The room-suite variants were staged only in `Saved/Staging/PoitouInteriors_20261025`.
That tree is gitignored scratch, and a cleanup pass deleted it. The surviving
authoring assets were:

- `hda/MelodiaRoomShell_ContactFloor_1.0.hda`
- `hda/MelodiaRoomShell_Rounded_1.0.hda`
- `Tools/Houdini/room_shell/stage_interiors.py` (the seven-variant generator)
- `Saved/Audit/PoitouInteriors_20261025/interior_manifest.json`

The suite was regenerated successfully (all seven variants `all_pass`), and the
native bake was built from those sources. The lesson is explicit in the promotion
rule below: **never let `Saved/Staging` be the only copy of an HDA.**

## 3. Native bake

For each source HDA:

1. Install the source definition and cook it in Hython.
2. Create the source node and a native `stash` SOP **in the same `geo` network**.
3. Press the stash SOP's actual storage button, `stashinput` (`stash` is the Data
   parm, not the button).
4. Add a native `null` output after the stash; remove the source node.
5. Create a new digital asset from that network.
6. Verify the new HDA's geometry counts and sections; write a JSON receipt.

The resulting HDA contains only native SOPs (`stash` + `null`) and **no
`PythonModule`**. The source's primitive attributes and groups are preserved by the
stash: `material_role`, `unreal_material`, `surface`, `room`, `collision_geo`, etc.
The source HDA's parameter interface is **not** retained — the native bake is fixed
geometry, not a parametric replacement.

Three bugs found and fixed:

- The stash was in a different `geo` from the source; `setInput` across networks is
  invalid.
- The wrong stash parm was pressed (`stash` Data) instead of `stashinput` (Button).
- **Container-category bug (2026-10-29):** `createDigitalAsset()` was called on the
  Object-level `geo`, so the native was an **Object** HDA while every source is a
  **SOP** HDA. The stash geometry was correct, but the UE Houdini Engine
  Object-HDA import doubled the cooked height (`16.32 × 12.54 × 15.61 m` instead of
  `16.32 × 12.54 × 7.90 m`).

The correct bake copies the `stash`/`null OUT` pair into a **SOP subnet** and calls
`createDigitalAsset()` on that subnet, producing a SOP-level HDA:

```text
Tools/Houdini/hda_native/bake_native_hda_sop.py <source.hda> <out.hda> <type>
```

The first SOP rebake (`salon_measured`) verifies:

- `new_category: Sop`
- source/native points 72,416 / prims 18,240 (identical)
- source/native bbox `16.32 × 7.90 × 12.54 m`
- `has_python_module: false`; display `OUT`; 523,743-byte HDA

The SOP salon still cooks `16.32 × 12.54 × 14.97 m` in UE. A controlled
`--engine-y-up 0` rebake produced `16.32 × 7.90 × 17.29 m` — worse, not better.
The source Python HDA imported in the headless editor never finished its cook
(placeholder default box), so the UE-side axis/scale path is the remaining
suspect. The failed `engine_y_up=0` test is archived under
`Saved/Audit/HDA_Native_20261029/experimental/`, not the runtime set.

The generator/authoring HDAs remain the source of truth for new variants.

## 4. Runtime set (8)

| Asset | Source type | Native type | Points | Prims | Native bytes |
|---|---|---|---:|---:|---:|
| bedroom | `melodia::room_shell_poitou_bedroom::1.0` | `..._native` | 73,444 | 19,913 | 516,679 |
| bedroom_small | `..._bedroom_small::1.0` | `..._native` | 21,444 | 5,393 | 192,034 |
| landing | `..._landing::1.0` | `..._native` | 4,072 | 1,018 | 47,928 |
| landing_wide | `..._landing_wide::1.0` | `..._native` | 17,212 | 4,319 | 165,042 |
| salon_bay | `..._salon_bay::1.0` | `..._native` | 85,256 | 21,450 | 599,739 |
| salon_bay_stepped | `..._salon_bay_stepped::1.0` | `..._native` | 85,256 | 21,450 | 601,728 |
| salon_measured | `..._salon_measured::1.0` | `..._native` | 72,416 | 18,240 | 523,743 (SOP) |
| stained glass | `melodia::stained_glass_window` | `..._native` | 232 | 348 | 10,347 |

All eight receipts report `"ok": true` and `"has_python_module": false`; source and
native point/prim counts match exactly.

Locations:

- `hda/Native/` — native runtime archive
- `Content/HDA/Native/` — UE import copies
- `Saved/Audit/HDA_Native_20261029/` — receipts
- `Saved/Audit/HDA_Native_20261029/experimental/` — the four non-runtime bakes
  (`ContactFloor`, `Rounded`, stale `MelodiaRoomShell_1.0`, `MelodiaHouse`)

## 5. Level convergence: `salon_measured`

The live `HDA_House_Salon` actor is at `(50, 0, 0)` with bounds center
`(818, -576, 360)` and extent `(792, 603, 380)` — **15.84 × 12.06 × 7.60 m**. That
is an exact match for the `salon_measured` variant, which makes it the level-first
convergence candidate; `salon_bay` (16.8 × 12.0 × 7.2) is a deliberate bay-aligned
redesign, not the measured fit.

The salon source resolves six contract slots; the native UE cook resolves the four
slots actually used by this variant:

- `MI_RoomShell_wall_plaster`
- `MI_RoomShell_floor_stone`
- `MI_RoomShell_trim_gold`
- `MI_Nikki_Show_PearlSheen` (the provisional `pearl_shell` borrow)

`stone` and `crystal_glass` are in the contract but unused by the salon variant, so
the native component omits the empty slots. The cooked component has no default
material and collision query+physics.

The native Houdini bbox is **16.32 × 7.90 × 12.54 m**; the UE cook does not match
it. The Object-level first pass was **16.32 × 12.54 × 15.61 m**; the SOP
`engine_y_up=1` pass is **16.32 × 12.54 × 14.97 m**; the SOP `engine_y_up=0` pass
is **16.32 × 7.90 × 17.29 m**. The Houdini point/prim counts (72,416 / 18,240) and
the four material slots match exactly, so this is a UE Houdini Engine
import/axis/scale problem, not lost geometry. The live salon is
**15.84 × 12.06 × 7.60 m** at `(50,0,0)` in the latest scene context (the
2026-10-28 audit recorded `(360,-330,0)`); the transform drift must be resolved
before placement. The editor opened `L_MelodiaMainMenu`, so no P0 placement has
been saved.

## 6. Organization and promotion rule

- `hda/` — parametric/authoring sources (Git-tracked).
- `hda/Native/` — native runtime archive.
- `Content/HDA/Native/` — UE import copies (P4 workspace).
- `Saved/Audit/HDA_Native_20261029/` — receipts/provenance.
- `Saved/Staging/` — transient only. The staging protection rule is
  `Saved/Staging/HDA_PROTECTED.md`; `hda/README.md` carries the pipeline summary.
- `specs/housing/hda_native_registry.v1.json` — source → native → UE mapping.

**Promotion rule:** never leave a finished HDA only in `Saved/Staging`; promote to
`hda/Native` + `Content/HDA/Native` + a receipt before deleting a staging copy.

## 7. What to convert — and what not to

**Convert (runtime finals):** the seven room-shell variants and the stained glass.
These are UE-facing, the embedded Python was the actual cargo, and the native bake
preserves the geometry/attributes.

**Do not convert wholesale:**

- `ContactFloor` / `Rounded` — parametric generator bases; the native bake freezes
  them and loses the room/portal parameters.
- `MelodiaHouse` — already has no `PythonModule`; its 112 s cook is geometry/PCG, not
  Python. The source keeps the artist parameters.
- `hda/HDA_Faraway_*`, `ArpeggioStair`, `CrystalCathedralV3`,
  `HDA_Melodia_CrystalCathedral`, `HDA_Poitou_AbbeyBuilder` — tracked
  authoring/offline HDAs; native baking loses controls, bloats Git/P4, and has no
  proven runtime benefit.

**Known gaps:** `HouseExteriorKit` fails on an invalid/unrecognized source type;
`HouseTerrain` exits 0 but writes no expected output; `HousingUltimate` /
`SalonConvergence` sources were not in the recovery set. Fix those sources/types
before any conversion.

## 8. Evidence levels

- **Houdini-proven:** all eight native bakes; geometry counts preserved; no
  PythonModule; receipts.
- **UE cook/material pass:** native salon imported; `HoudiniStaticMeshComponent`;
  four used material slots; no default material; collision query+physics.
- **UE bounds open:** SOP `engine_y_up=1` 16.32 × 12.54 × 14.97 m; SOP
  `engine_y_up=0` 16.32 × 7.90 × 17.29 m; Houdini 16.32 × 7.90 × 12.54 m; live
  15.84 × 12.06 × 7.60 m. The source Python control did not cook headlessly.
- **P0 placement pending:** editor opened the main menu; old salon not compared;
  the transform drift `(50,0,0)` vs `(360,-330,0)` is open.
- **Not proven:** packaged runtime, traversal, or a finished room replacement.

## 9. Portfolio takeaway

The durable value is not “fewer Python files.” It is a production split that
survived a deletion:

- parametric source of truth (`hda/`, generator, registry),
- native runtime delivery (`hda/Native`, `Content/HDA/Native`, receipts),
- a staging rule that prevents the only copy from living in scratch,
- a level-first convergence method (`salon_measured` matched to the live bounds,
  not guessed),
- evidence at every step, with the unproven layers named.

That is the reusable pipeline for the rest of the house and the next portfolio
piece.
