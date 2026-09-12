# Session Handoff — 2026-08-11 (corrected)

> **CORRECTION (owner, end of session):** the rig prep ran against `FinalUERig43.blend`
> which is the **OLD rig file**. The **current rig lives inside
> `Melodia_Portfolio_Stage_v22_ZenRebuild_WIP.blend`** (`G:\EnvironmentPortfolio\BS_GodFile\`),
> where the character is `Melusina.001` (120 shape keys, 52 drivers) bound to
> `character_rig` (1124 bones) with `character_rig.002` (759 bones = the v43 armature)
> also present. All next steps must target **v22**, not FinalUERig43.

## 1. Shipped deliverables (on disk)

| Deliverable | Path | State |
|---|---|---|
| **Gothic Cathedral Kit — 41 pieces** (vault bay, buttress, pier, rose window, portal, chandelier, staff balustrade, harmonic altar, observatory, Escher trio, statuary, stained glass, pavilion/stall/garland, bed, perch, resonant door…) | `KitbashExport/CathedralKit/SM_Cathedral_*.fbx` + `.meta.json` | ✅ 41/41, round-trip verified, zero zero-face |
| 126 m nave review scene (live GN stacks, artist-editable) | `KitbashExport/CadenceCathedral_Review_2026-08-11.blend` | ✅ |
| Review Queue populated into the stage | v22 → 29 `RQ_Cathedral_*` items + existing `Asset_*` items | ⚠️ last sync was aborted mid-write — **verify on next open** |
| Build + audit tooling (idempotent, re-runnable) | `Tools/build_cathedral_kit.py` · `Tools/cathedral_gn_audit.py` · `Tools/populate_cathedral_review_queue.py` · `Tools/blender_mcp_client.py` | ✅ |
| RPG-tagged world manifest (UE-ready) | `Saved/Audit/cathedral_world_manifest.json` | ✅ 6 rooms + slice props |
| Evidence | `Saved/Audit/cathedral_kit_build.json`, `cathedral_builder_capabilities.json`, `cathedral_review_queue_sync.json` | ✅ |

**Addon fixes (in `deploy/surreal_arch`, synced to live 5.2):** `primitives.py` 5.2 API drift (`local_space` → "Local Space" input socket; 3 array builders were broken) · in-tree `Realize Instances` needed for export (5.2 no longer realizes instances at export).

**BlenderMCP installed:** `addon.py` (BlenderMCP) → 5.2 addons, `blender` MCP client in `.mcp.json` (`uvx blender-mcp`, port 9876), direct client at `Tools/blender_mcp_client.py`.

## 2. Rig findings (current = stage v22)

1. **Blender 5.2 API moved vertex groups:** `Mesh.vertex_groups` no longer exists — they live on **`Object.vertex_groups`**. Use the object-level path for all weight work (and verify ARP/Simply Cloth compatibility).
2. **Eye shape-key drivers are broken in BOTH rig generations** (same Face-It authoring): all 53 (v43) / 52 (v22) drivers invalid — variable targets have `id: null`, pointing at `c_*` bones (`c_eyelid_upper.L`, `c_LookAt2D_slider2d`, `c_lookat_mch.L/R`, `c_cheek_upper.L`, …) that belong to a `FaceitControlRig` armature missing from the file. In v22 additionally `Melusina.001`'s two ARMATURE modifiers have **`obj: None`** (unbound).
3. **Fix procedure (proven live in v43, replay into v22):** append `FaceitControlRig` (78 bones + 66 ARKit amp custom props) from `G:\MelodiaMelusina\MelusinaFinalRig\MelusinarigWithFaceUntextured.blend` → set `t.id = faceit` on every null driver target (do NOT touch `id_type`, read-only) → verify `driver.is_valid` count → pose test: `c_eyelid_upper.L` **Y-location** drives `eyeBlinkLeft` via `(max(0, var/3.0)) * amp`. Result in v43: 0 → 53/53 valid. **The v43 fix was in-memory only (session closed) — nothing on disk changed; re-run into v22.**
4. **Water hair** = Flip Fluids (`FF_MelusinaHair_Domain/Drip/Sheet`) — no hair-card weighting; baked surface rides `hair_root`/`head_x` rigidly, domain/flow parented to the head, jiggle for runtime motion.
5. **Garments** (`Melusina_Skirt/Sleeve/Shawl` + panels) use native Cloth + Surface Deform; Simply Cloth Studio 1.5.2 expects pins in a `SimplyPin` vertex group (hips/shoulders).

## 3. Next steps (all target **v22**)

1. **Rig prep in v22** (via BlenderMCP or `blender -b`): append FaceitControlRig → repoint the 52 shape-key driver targets on `Melusina.001` → **rebind its two null ARMATURE modifiers** to `character_rig` → weight audit + normalize via `Object.vertex_groups` → save. (Backup v22 before editing; it is the owner's live stage file.)
2. **Water-hair prep**: rigid `hair_root`/`head_x` weights on the baked fluid surface; parent domain/flow to the head chain; note sim obstacle state.
3. **SimplyPin groups** on Skirt/Sleeve/Shawl at hip-waist/shoulder seams (weight 1.0, coarse — owner tunes).
4. **Verify Review_Queue sync** in v22 (aborted run) and finish the cathedral queue sync.
5. **Owner exports** per AAA doc: ARP 3.77.25 → Universal, Only Deform Bones, cm/scale 1.0, no leaf bones, Export Shape Keys ON, one Armature modifier at export (Subsurf below or clean export copy).
6. **W2/W3 leftovers:** Game Readiness Report as addon N-panel command; world-manifest fully UE-prepped (manifest drafted).

## 4. Files touched

`Tools/` (5 new) · `deploy/surreal_arch/melodia_gn/primitives.py` (fix) · `.mcp.json` (+blender) · live 5.2 addons (`addon.py`, synced `surreal_arch`) · `KitbashExport/` (kit + review blends) · `Saved/Audit/` (evidence) · v22 (RQ items — verify) · **Old-rig probes only** against `FinalUERig43` (nothing saved there).
