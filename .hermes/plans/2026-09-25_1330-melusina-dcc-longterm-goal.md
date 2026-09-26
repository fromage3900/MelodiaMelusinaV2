# GOAL — Melusina long-term DCC pass → reimport → face + locomotion (2026-09-25, owner: "audit, re-verify, proceed, updated goal")

**Parent:** `2026-09-25_0500-melusina-signature-and-hotpass-goal.md` (G1–G4 done, G5 now passes).
**Rules:** one Blender writer on `..._R09_HotPass.blend` at a time; canonical R08 untouched; no UE reimport over live assets without owner OK; no new master material (MI rule) — master edits are owner decisions.

## Audit — claims re-verified against disk (2026-09-25)

| Earlier claim | Verified | Evidence |
|---|---|---|
| Eyes fix only in blend, not in UE | **Wrong** — neither the 09-02 `SK_Melusina_V2_Body.arp.fbx` nor the staged FBX skins `eyes`; UE body already carries it | FBX re-import audit |
| Fingers need re-weight (postmortem open decision) | **Wrong cause** — export config. Mannequin/HUMANOID mode + metacarpals off orphaned `index/middle/ring/pinky_01` and made `neck_02` a root | staged FBX parent chains |
| 432 vs 387 bones | Resolved — UNIVERSAL + ARP names + metacarpals → **463** vs UE skeleton 465; 10/10 key parent links match `SK_Melusina_Skeleton` | `Tools/melusina_export_dryrun.py` |
| Export 100× small | **Wrong** — checker artifact; owner confirmed normal height in UE (scratch import) | `/Game/_Staging/MelusinaExportCheck` (unsaved) |
| "75 ARKit-like" keys | Imprecise — **52/52 exact ARKit** names present | FBX audit |
| Locomotion BlendSpace unfixed | **Confirmed** — 7 samples/4 clips, root-locked, axis max 650 | live `get_blend_space_info` |
| Sprint speed 714 | Unverified (postmortem only) — measure in D5 | — |
| Face SDF needs master work | **Wrong** — master already has `FaceSDF_Texture/Strength/Tiling`, `bFaceSDF_UV1` | master expression list |
| Vertex-colour MPC zones | Master reads **only VertexColor.G** (→ Multiply_51); R/B/A zones need a master edit | `get_expression_connections` |

## Order

- **G5 — DONE.** Staged body+skirt pass `Tools/validate_melusina_staged_fbx.py` (463 bones, both blinks, 52 ARKit, height UE-confirmed).
- **G7 — ATTEMPTED 2026-09-25, FAILED, REVERTED (unsaved).** Owner OK'd. Reimport landed (blinks present, 70 non-empty morphs; iris/outline slots + skirt NikkiGemstone/outline slots restored by hand) but PIE showed Melusina in **T-pose with a distorted head**. Not saved; disk assets byte-identical to `Saved/Audit/p0_closeout_2026-09-24/g7_reimport_backup/` and re-locked read-only; in-memory copies still dirty → **restart the editor without saving them**. Prime suspect: export used `arp_mannequin_axes=False` while the saved scene (and likely the 09-02 export) had `True` — bone axes change, anims no longer map. Next try: keep UNIVERSAL + metacarpals but restore `mannequin_axes=True`, re-validate, then retry in a scratch folder with a PIE pose check BEFORE touching the live asset.
- **G7 retry 2026-09-25 17:45 — FAILED, REVERTED (unsaved).** mannequin_axes=True produced a byte-identical FBX (setting inert in UNIVERSAL mode — not the cause). Real cause found: the reimported body **cannot host an anim instance** — `CharacterMesh0.GetAnimInstance()` is None in fresh PIE, and forcing `SetAnimInstanceClass(ABP_Melusina_Current_C)` still returns None → T-pose. The earlier "scratch swap looks posed" result was a false pass (runtime mesh swap kept the pre-existing instance). Interchange also warned "invalid bind poses — rebound using time zero pose". Next: diff the imported ref skeleton against `SK_Melusina_Skeleton` (root bone name/parenting, bind pose) in the scratch asset; gate the retry on a FRESH-spawn anim-instance check, not a runtime swap.
- **G7 (original gate).** Body + skirt over `SK_Melusina_V2_Body` / skirt asset on `SK_Melusina_Skeleton`, morphs on. Gate: both blinks close in PIE, skirt Kawaii ring constraints still bound, `test_melusina_skin_topology_contract` no new violations. Then delete `/Game/_Staging/MelusinaExportCheck`.
- **D3 attempt 1 (Sonnet subagent, 2026-09-25): NOT USABLE.** `Tools/melusina_bake_face_sdf.py` → `Saved/Staging/MelusinaFaceSDF/`; contact sheet is sparse vertex dots (per-vertex nearest-texel splat), not a gradient — agent report overstated it. Real blocker: face UVs are several disjoint islands (UV0; UV1 in the FBX is 98.6% at (0,0)). Needs a dedicated single-chart face UV (SDF-only channel) or a surface-rasterized Houdini bake.
- **D3 — Face SDF shadow map.** Bake threshold-SDF (Houdini 22 or Blender) into `T_Melusina_FaceSDF` on UV1; set existing `FaceSDF_*` params on the face MI. Gate: light sweep capture shows a clean nose/cheek shadow edge.
- **D4 — Face rig in UE.** After G7: map the 52 ARKit morph curves (Live Link Face pose asset / curve remap in ABP). Gate: blink + jawOpen + visemes in PIE.
- **D5 — Locomotion.** Retarget Rokoko takes with root motion kept, `get_root_motion_speed` per clip, rebuild BlendSpace from measured speeds (dedupe; axis ≥ fastest clip). Gate: no foot slide at walk/run/sprint in PIE.
- **D2 — Vertex-colour zones (owner decision).** G channel usable now; R/B/A need a master edit to read them. Decide before painting.
- **Not doing:** Tripo / UV re-unwrap on skinned garments.

## Owner eye-checks owed
S1 hair sway · S2 skirt figure · skirt/hair motion clipping · KaleidoNave arrival point · Shorewake silhouette strength.
