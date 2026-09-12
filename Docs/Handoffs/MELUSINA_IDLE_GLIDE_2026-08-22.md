# Melusina Idle + Glide — Session Record 2026-08-22

**Scope:** owner notes "BP Melusina still t-poses on idle; glide mechanic still missing".
**Method:** Monolith MCP against a single editor instance; every claim below is a live
query, an audit JSON in `Docs/Evidence/2026-08-22_melusina_idle_glide/`, or a capture PNG.

---

## Shipped (all on disk, compile 0 errors / 0 warnings)

| Change | Final state |
|---|---|
| Idle binding | `Locomotion/A_Melusina_Idle_Mocap_RootX` — proven upright (original T-pose was the old unsuffixed clip) |
| Glide state | plays `Mocap/A_Mocap_LittleDance_001` placeholder loop |
| Glide entries | `Idle→Glide`, `Locomotion→Glide`, `Airborne→Glide` — all `bool bIsGliding` |
| Glide exits | pre-existing `Glide→Airborne` (`bRuntimeIsInAir`), `Glide→Land` (`bRuntimeIsGrounded`) |
| Dead edges removed | ruleless `Glide→Idle/Locomotion` (compiled as "never taken") |
| Gameplay half | already ships: `UMelodiaTraversalComponent.StartGlide` + stamina + jump-then-second-press input; capability catalog `DA_MelodiaCosmeticCatalog` exists |

Ground truth at session end: `melusina_idle_glide_final_2026-08-22.json` → **PASS**.

## The Blender hand-keyed lesson (why the idle is mocap tonight)

Owner's hand-keyed idles were imported directly onto `SK_Melusina_Skeleton`
(name-matched tracks). Both render as exploded/lying-down piles despite skeleton +
cm checks passing:

- `Authored/A_Melusina_Idle_v22` — unguarded import
- `Cascadeur/A_BL_Melusina_Idle_Loop` — guarded import, cm probe PASSED

Root cause: per-bone rest-pose rotations differ between the ARP stage rig and the
UE-built skeleton; unit probes don't catch it. **Retargeting through an IK chain is
mandatory** for stage-blend clips. Full path + evidence:
[`Docs/Production/BLENDER_HANDKEYED_ANIM_IMPORT_PIPELINE_2026-08-22.md`](../Production/BLENDER_HANDKEYED_ANIM_IMPORT_PIPELINE_2026-08-22.md).

## New: reusable skill

`.agents/skills/melusina-blender-handkeyed-import/` (also installed to
`%USERPROFILE%\.agents\skills\`):
- `SKILL.md` — 7 hard rules + A→G workflow checklist
- `scripts/bind_and_verify.py` — Stage F wrapper: bind → compile → ReadOnly-clear →
  save → mtime assert → live re-read. Passed first real run
  (`Saved/Audit/bind_and_verify_idle_*.json`).

## Incidents hit (documented, not new)

1. **ReadOnly save crash** — LFS lockable attribute on the ABP crashed the editor inside
   `save_packages` (same as MF_Madoka 2026-08-15). Cleared `attrib -R` on that one file.
2. **Parallel-lane churn** — editors replaced twice mid-session; both `wire_melusina_*`
   tool fixes were reverted by another lane. ABP changes were re-applied via direct MCP
   calls; tool-file fixes need coordination with their owning lane.
3. **Capture budget** — two captures consumed this day (one per editor session rule);
   frames committed under `Docs/Evidence/`.

## Open items

1. Next editor session: one fresh capture of Idle (ABP context) + real-input PIE:
   jump → second press after apex → glide engages, Glide state plays; read
   `BlockReason` logs if rejected.
2. Owner call: delete or keep quarantined `A_Melusina_Idle_v22` / `A_BL_Melusina_Idle_Loop`.
3. Land a hand-keyed clip through pipeline Stage E (retarget route) to replace the
   mocap idle placeholder.
4. Swap glide placeholder clip when authored art lands.
5. Re-land `wire_melusina_idle.py` / `wire_melusina_glide.py` fixes with the owning lane.
