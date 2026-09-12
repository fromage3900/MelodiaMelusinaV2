# P0 Allowlist Delta — Rider Handoff 2026-08-28

Junie — this is your editor queue. I stayed off the editor so you keep it.

## What I did (no editor, no .uasset writes)

- **Hygiene verified:** the 4 zero-byte root files (`Checking`/`Installing`/`Set`/`uv`) are already gone; `BS_GodFile.uproject` is clean — only 4 lines adding `HoudiniEngine` `Enabled:true`, no BOM/reindent churn left. No action needed.
- **QSC defects fixed in working tree** (already in `git diff`, not yet committed):
  - `MelodiaQuillWardrobeEquip.qsc`: `flags.melusina...` → `flag.melusina...` + removed standalone `$ Notify melodia:reward:reward.wardrobe.first_outfit`
  - `MelodiaQuillChoralSheepRecruit.qsc`: removed standalone `reward.companion.choral_sheep`
  - `MelodiaQuillSeaAboveCutscene.qsc`: removed standalone `reward.cutscene.sea_above_memory`
  - Result: `test_flag_prefix_is_singular` ✅ and `test_no_reward_grant_shadows_a_questcomplete_reward` ✅
- **Contract test proven:**
  - `test_p0_quests_and_content_contract.py` — 8/8 ✅
  - `test_qsc_allowlist_contract.py` — 3/4 ✅, 1 expected FAIL (`test_every_gated_id_is_allowlisted`) listing 27 missing IDs — that's your work queue.
- **Ledger sync already done:** `Saved/gate_ledger.json` + `Saved/gate_ledger_report.md` regenerated 2026-08-28 04:27 UTC; `battle_integration_map` and `hud_single_writer` both PASS. No action needed.

## What you need to do in Rider (one editor, your lock)

1. **Read live allowlist truth** (do NOT use `melodia_config_get_allowlist` — it returns stale fixture per `P0_TASK_LEDGER.json`):
   ```
   blueprint_query get_cdo_properties -- asset_path=/Game/MelodiaIntegration/Config/DA_MelodiaIntegrationConfig
   ```
   Confirm the 2026-08-28 snapshot still matches §B2 of `Docs/P0_CLOSEOUT_PLAN_2026-08-28.md` (6 sets, ~15 IDs).

2. **Extend `DA_MelodiaIntegrationConfig`** with the JSON delta in `Docs/Handoffs/P0_ALLOWLIST_DELTA_FOR_RIDER_2026-08-28.json`:
   - `QuestIds` +5 (4 P0 + harmony_awakening)
   - `NarrativeFlagIds` +13 (12 P0 + harmony flag)
   - `DialogueRewardIds` +5 (4 P0 + harmony)
   - `SocialStatIds` +2 (`melodia_elegance`, `melodia_resonance`)
   - `TravelLevelIds` +1 (`LV_SeaAbove_Prototype`)
   - Save the asset, confirm mtime moved.

3. **Verify offline (no PIE needed):**
   ```bash
   python -m unittest Content.Python.Tests.test_qsc_allowlist_contract -v
   ```
   Expected: 4/4 PASS. If still red, re-read the CDO — you missed an ID.

4. **Then compile the .qsc → .uasset** (your Phase 1 step 7): the 4 P0 scripts + `MelodiaQuillHarmonyAwakening` (5 total). Confirm each loads via `unreal.load_asset` or editor content browser. This is why the allowlist must come first — compiled scripts with rejected IDs still fail at `IsAllowed`.

5. **Leave the 27-file hygiene alone** — I'll stay in verifier lane. When you're done with the allowlist + compiles, ping me and I'll re-run the full offline chain and draft the ledger row for Phase 1.

## Files for reference

- Delta (machine-readable): `Docs/Handoffs/P0_ALLOWLIST_DELTA_FOR_RIDER_2026-08-28.json`
- This handoff: `Docs/Handoffs/P0_ALLOWLIST_DELTA_FOR_RIDER_2026-08-28.md`
- Failing contract: `Content/Python/Tests/test_qsc_allowlist_contract.py`
- Source of truth for P0 IDs: `specs/progression/melodia_p0_slice_quests.v1.json` `required_allowlist`

Good winds, Junie — the rest is just your keystrokes.
