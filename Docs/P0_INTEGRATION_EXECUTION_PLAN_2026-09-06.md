# P0 integrated execution plan — 2026-09-06

## Current truth

The project is source/editor-ready but not shipping-certified. The active P0 ledger has eight
green gates; the remaining certification boundary is a current closed-editor package followed by
one uninterrupted owner-played golden run. The Sea Above route has authored placement/runtime
evidence, but its Starskiff segment is a Glide transition and still needs focused real-input proof.

Authority remains unchanged:

- QuillScript owns narrative and notifications.
- The TurnBased JRPG template owns battle, damage, results, inventory, saves, and turns.
- MelodiaNarrativeSubsystem is the narrow bridge.
- MelodiaAudioReactivePresentationSubsystem is the sole MPC writer.
- MelodiaCymaticsSubsystem is a read-only consumer.
- Existing PCG graphs and PCG_ExclusionFalloff own scatter/falloff.
- MelodiaStarskiffPawn owns boarding, movement, and boat traversal.
- Dungeon coordinator/persistence lanes remain quarantined; they do not become a second save or
  encounter authority during P0.

## Execution order

### 1. Offline contract gate

Run and archive:

~~~text
python Tools/verify_p0_offline.py
python Tools/test_echo_contract.py
python -m unittest Content.Python.Tests.test_sea_above_level_loop_contract Content.Python.Tests.test_sea_above_t3d_contract Content.Python.Tests.test_qsc_allowlist_contract Content.Python.Tests.test_shorewake_quest_contract
~~~

Expected current result: 12/12, 77/77, and 17/17 respectively. A full discovery run is
diagnostic only until Windows temp-directory permissions and the missing authored BaseColor fixture
are corrected; its failures must not be converted into gate passes.

### 2. Editor-backed static and placement validation

With exactly one editor and one Monolith listener:

1. Run echo_run status, project_state --view integration, and static_gates.
2. Confirm CanonicalLandscape is the only Landscape actor and all loaded streaming proxies use
   MI_SeaAbove_CanonicalLandscape_Substrate.
3. Confirm the Sea Above actor folders, PCG_Spline corridor tags, PCG_Exclude/WP_NoScatter anchors,
   and the Starskiff dock/boarding anchor.
4. Rebuild navigation and verify entry → Quill and Quill → music-key nav paths.
5. Keep music-key → dock as Glide, never as a fabricated nav connection.

### 3. Dungeon integration probe

Do not reactivate quarantined coordinator/persistence authorities. The authorized live sequence is:

~~~text
FirstDungeonGate unlock
→ StartFirstDungeonRun(seed 1337)
→ one generated entrance + exit
→ grounded relocation
→ one encounter and typed JRPG result
→ reward choice
→ exit exactly once
→ second room
→ canonical save/checkpoint restart
~~~

Capture room IDs, seed, entrance ground trace, encounter result, reward transaction, exit count,
and save/read-back. Missing entrance/exit coverage in room maps is a content blocker, not a reason
to add another coordinator.

### 4. Lookdev and PCG pass

Use isolated material instances only. Keep the landscape on
MI_SeaAbove_CanonicalLandscape_Substrate; keep water on the existing Water V10 family and keep
the single MPC/audio writer intact. Validate before/after instance parameters and capture a scene
frame. Extend the existing PCG graphs only:

- Arrival: 0–400 cm hard exclusion, 400–900 cm light transition.
- Main traversal: 0–300 cm exclusion, 300–700 cm transition, full density beyond 700 cm.
- Battle/hero footprint: 1200 cm landmark-clear radius.
- Starskiff channel: 800 cm exclusion; water-edge dressing outside the channel.
- Never scatter across the real-ocean/false-ocean vertical illusion gap.

Use the three authored PCG_Spline corridors and World Field Bus fields
WorldField.Resonance, Tension, Moisture, Contact, Residue, Reaction, AnchorStability, and FilterFlow.
Do not rerun the historical hard-coded stage_seaabove_level_loop.py.

### 5. Real-input and package certification

Run one focused-player-input PIE traversal:

~~~text
PlayerStart → Quill → music-key phrase → visible cymatics response
→ Glide descent → dock landing → Starskiff board → move → disembark
→ Melusina control restored
~~~

Save assertion JSON beside every frame. Then perform a closed-editor Development package build,
launch the package outside the editor, and repeat the same route. Only after those artifacts exist
may the current package/golden-run rows be promoted.

## Known blockers and stop rules

- Do not mark probe-injected calls as real-input evidence.
- Do not certify the stale synthetic Sea Above heatmap; regenerate from live actor/nav/spline data.
- Do not add a dungeon coordinator, persistence subsystem, PCG framework, audio writer, or HUD writer.
- Do not save unrelated dirty material packages.
- Full suite temp-permission failures are environment failures; fix the harness separately.
- If the package build or owner-played golden run is absent, shipping status remains HOLD.

## Evidence outputs

- Docs/Evidence/SEA_ABOVE_LANDSCAPE_GAMEPLAY_PCG_INTEGRATION_2026-09-01.json
- Docs/Handoffs/SEA_ABOVE_GAMEPLAY_PATHS_AND_LEVEL_ORGANIZATION_2026-09-01.md
- Docs/P0_TASK_LEDGER.json
- Saved/gate_ledger.json
- Current package report plus player-input frames/assertions
