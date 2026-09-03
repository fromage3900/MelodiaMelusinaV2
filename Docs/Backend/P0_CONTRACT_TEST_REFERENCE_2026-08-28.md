# P0 Contract Test Reference Snapshots — 2026-08-28

Offline reference copies of the two P0 contract suites, captured for a future agent that needs
them without re-deriving from the repo. These are snapshots, not the source of truth — the live
tests under `Content/Python/Tests/` are authoritative. Update the snapshots if the live tests change.

## test_p0_quests_and_content_contract.py (8 tests, all PASS)

Path: `Content/Python/Tests/test_p0_quests_and_content_contract.py`

Assertions:
1. `test_fixtures_present` — `.qsc` files + spec files exist
2. `test_p0_playthrough_qsc` — grammar + `melodia:battle:melodia_smoke_encounter` + questcomplete + flag
3. `test_wardrobe_equip_qsc` — item grant + outfit flag + sorrow seam flag + questcomplete
4. `test_companion_recruit_qsc` — stat + recruit flag + questcomplete
5. `test_sea_above_cutscene_qsc` — travel + resonance stat + two flags + questcomplete
6. `test_progression_package_spec` — 4 quests in spec, scripts resolve
7. `test_wardrobe_manifest` — slots + Glide capability
8. `test_companion_manifest` — pitch class C + quest binding
9. `test_cutscene_manifest` — 3 camera tracks + pulse 16.0s

Result (2026-08-28): 8/8 PASS ✅

## test_qsc_allowlist_contract.py (4 tests, 1 expected FAIL)

Path: `Content/Python/Tests/test_qsc_allowlist_contract.py`

Assertions:
1. `test_fixtures_present` — `.qsc` files + allowlist asset exist
2. `test_every_gated_id_is_allowlisted` — every `$ Notify melodia:` gated id exists in
   `DA_MelodiaIntegrationConfig` (FAIL until allowlist extended — 27 IDs missing)
3. `test_flag_prefix_is_singular` — no `flags.` typo (PASS after QSC fixes)
4. `test_no_reward_grant_shadows_a_questcomplete_reward` — no standalone reward grant before a
   questcomplete reward leg (PASS after QSC fixes)

Result (2026-08-28): 3/4 PASS, 1 expected FAIL (27 missing IDs — the whole reason Phase 1 exists)

## Missing IDs (2026-08-28 snapshot, for the allowlist delta)

From `Docs/Handoffs/P0_ALLOWLIST_DELTA_FOR_RIDER_2026-08-28.json`:

QuestIds (5): quest.first_dream, quest.wardrobe.equip_outfit, quest.companion.choral_sheep,
quest.cutscene.sea_above, quest.harmony_awakening

NarrativeFlagIds (13): flag.first_dream.quest.completed, flag.p0.playthrough.completed,
flag.p0.playthrough.attempted, flag.p0.playthrough.fled, flag.wardrobe.outfit_equipped,
flag.wardrobe.equip_completed, flag.melusina.sorrow_seam_restored, flag.companion.choral_sheep_recruited,
flag.companion.choral_sheep_completed, flag.cutscene.sea_above_witnessed,
flag.sea_above.membrane_pulse_active, flag.cutscene.sea_above_completed, quest.harmony_awakening.completed

DialogueRewardIds (5): reward.first_resonance_echo, reward.wardrobe.first_outfit,
reward.companion.choral_sheep, reward.cutscene.sea_above_memory, reward.harmony_awakening

SocialStatIds (2): melodia_elegance, melodia_resonance

TravelLevelIds (1): /Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype
