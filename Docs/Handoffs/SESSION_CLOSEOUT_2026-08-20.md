# Session Closeout — 2026-08-20 — The Paradigm Shift

**Theme:** the project stopped describing itself as an AI studio and started describing itself as
a game. Then two of the four pillars got wired together.

**Authority produced this session:** [`../../PROJECT.md`](../../PROJECT.md) ·
[`../ORCHESTRA_CONVERGENCE_2026-08-20.md`](../ORCHESTRA_CONVERGENCE_2026-08-20.md) ·
[`../ORCHESTRA_CONTRACT_2026-08-20.md`](../ORCHESTRA_CONTRACT_2026-08-20.md) ·
[`../MELUSINA_ANIMATION_PIPELINE_REVIEW_2026-08-20.md`](../MELUSINA_ANIMATION_PIPELINE_REVIEW_2026-08-20.md)

---

## 1. The shift, in one paragraph

`PROJECT.md` was a PBR material-library charter and `README.md` advertised "two active tracks"
plus a ten-model agent ecosystem. The most recent work was pitching the project to Nous Research
and NVIDIA as an AI research platform. That is now inverted: **Melodia Melusina is a game.**
QuillScript and the TurnBased JRPG template are absolute authority layers; rhythm rides on top of
JRPG command input; wardrobe is a core pillar; music acts as a key in the world. The AI tooling
is explicitly demoted to a tool that may not set direction.

Owner's framing, which corrected the initial reading: OMORI's shape, an enhanced musical layer
for combat *and* world puzzles à la Zelda / Infinity Nikki, with QuillScript and TurnBasedJRPG at
the core. The systems were not incomplete — they were being built in parallel and never joined.

---

## 2. Governance rewritten

| File | Change |
|---|---|
| `PROJECT.md` | Replaced the material-library charter with the authority statement + four-pillar map. PBR work demoted to "Wardrobe visual spine (M1–M4, DONE)". |
| `README.md` | One track. Environment-art platform reframed as "the world-building toolchain that feeds it". |
| `_VERTICAL_SLICE_SCOPE.md` | **Wardrobe and rhythm moved out of "Explicitly deferred" into core pillars.** Historical correction blocks preserved verbatim. |
| `AGENTS.md` | Core vision replaced; added must-not rows against building a fifth wardrobe track / fourth rhythm path / second HUD writer. Now 31,321 bytes — **1.4 KB under the 32 KB subagent cap.** |
| `DOC_INDEX.md` | New "Read these four, in this order" section; career/portfolio marked as carrying no project authority. |

---

## 3. Three corrections the evidence forced

Recorded because each one overturned a confident assumption:

1. **The shipping gates are closed.** `runtime`, `save_load`, `repeat_consume` and
   `package_launch` all have **PASS rows** in `Saved/gate_ledger.json` (two owner-verified) since
   2026-08-14. `_TASK_QUEUE.md` and `_VERTICAL_SLICE_SCOPE.md` still listed three as open — six
   days stale. Both reconciled. `static_gates` remains **FAIL** on two material baseline drifts.
2. **"MelodiaCore is quarantined" does not mean its contents are dead.**
   `MelodiaRhythmHUDWidget` and `MelodiaRhythmReactivitySubsystem` are both load-bearing on the
   shipping path — six live call sites between them. Only `MelodiaRhythmExecutionComponent` is
   genuinely dead. Two of three assumed-dead verdicts were wrong.
3. **The world-puzzle pillar exists.** It is filed under `Source/BS_GodFile/Piano/`, not
   `Puzzle/` or `Challenge/`. Complete music-as-key system: PCG-spawned piano keys with real MIDI
   notes, steppable note nodes with spring physics, pattern scoring, `OnPatternCompleted`, real
   content in `Content/EnvSandbox/PCG/Musical/`, and a Python authoring pipeline with its own test.

---

## 4. Gates re-pointed

Added an `orchestra` stage to `specs/echo_pipeline.json` with six convergence gates —
`rhythm_owner`, `hud_single_writer`, `wardrobe_equip_roundtrip`, `rhythm_grade_to_result`,
`music_world_key`, `wardrobe_gameplay_hook`. All render **OPEN** in `echo_run.py status`.

`_TASK_QUEUE.md` re-prioritised: the game at P0, convergence hygiene at P1, and Glacier / LFS /
`.gitignore` / DDC / Perforce demoted to **P2 infrastructure** under a header stating they do not
block the game. All queue history preserved inside the existing `<details>` fold.

---

## 5. Local models became production workers

Five lanes added to `Tools/model_router.py` — `wardrobe_catalog`, `beatmap_author`,
`quill_author`, `asset_qa`, `anim_bindings` — all local-only via `LOCAL_ONLY_CLASSES`, so game
content never silently reaches a paid cloud endpoint.

New `Tools/run_production_lanes.py` + `specs/mcp/production_tasks.v1.json`: six real game tasks
judged by **binary contract acceptance, not score**, and no lane records its own ledger row.

### The 60.35% / 0% benchmark was a harness bug

`run_math_models.py::_tool_catalog` emitted only `name: description[:140]` and **discarded each
tool's `inputSchema`** — then validated the model's arguments against the schema it had withheld.
That is the entire cause of the 16 identical `'blueprint_name' is a required property` failures.
Fixed at the cause (`_format_schema`); the catalog now emits `REQUIRED:` per tool.

### Two models quarantined

- `qwen2.5-coder:14b` — **corrupt weights on disk**, emits repeated tokens. I had initially made
  it primary for `asset_qa`; corrected after finding the evidence in
  `OLLAMA_SETUP_FIX_2026-08-20.md`. Now in `BLOCKED`.
- `deepseek-coder:6.7b` — 1/8, no structured output. In `BLOCKED`.

Router `REQUEST_TIMEOUT` is now env-configurable and production runs default to **1200s**,
matching the measured cold-load cost (model store on a 32 MB/s HDD; a 21 GB tag needs ~11 min).

**Not verified live:** Ollama answers `/api/tags` but could not serve a completion this session.
Plumbing is verified (`model_router test --class wardrobe_catalog` passes for
`qwen2.5-coder:7b`); the host is not.

---

## 6. AI-studio writing repurposed

24 `Docs/Career/` and `Docs/Portfolio/` files got a "downstream of the game — carries no project
authority" banner. `MELODIA_STUDIO_STARTUP_PARAGRAPH.md` rewritten to lead with the game (and its
Blender 5.1 → 5.2 stale fact corrected). `Docs/Career/README.md` reframed.

**A stale duplicate was found and defused.** `BS_GodFile/Docs/MELUSINA_AGENT_TEST_HARNESS.md` had
its unbacked 98.8% TCA figures withdrawn on 2026-08-19 — but a second copy at
`Docs/MELUSINA_AGENT_TEST_HARNESS.md` (repo root, 2026-08-18) predates that correction and still
presents them as measured results addressed to a named research org. That copy is now marked
**STALE DUPLICATE — DO NOT SEND, DO NOT CITE**. The maintained copy was reframed as a
game-development appendix.

---

## 7. Puzzle integration — the adapter that was specified but never written

**New:** `Source/BS_GodFile/MelodiaIntegration/MelodiaPCGNarrativeChallengeBridgeComponent.{h,cpp}`

`specs/blueprints/fixtures/first_resonance_world_challenge.v1.json` names
`UMelodiaNarrativeSubsystem` as its `runtime_authority` and sat at `status: contract_spec_only`.
The allowlist already contained `challenge.first_resonance_echo`, its completion flag and its
reward. The design existed; the adapter did not.

The component mirrors `UMelodiaPCGWaterGameplayBridgeComponent` exactly — attach to an
`APCGHeroMusicGraphHost`, bind `OnPatternCompleted`, commit through
**`CommitWorldChallenge`** (one atomic transaction: flag + reward + consumed intent).

Boundaries held deliberately:
- No combat contact — preserves the `PCGHeroMusic.cpp:624` presentation-only boundary.
- No direct save write, per `adapter_must_not_write_save_object_directly`.
- **No local "already fired" bool.** `ConsumedIntentIds` is SaveGame-flagged and is the single
  truth; a local flag would silently disagree after a reload.

**Not compiled.** It is a new `UCLASS` with `GENERATED_BODY`, so Live Coding cannot register it —
only a closed-editor build can, and the editor was open. `source.lint_header` reports clean and
every referenced symbol was verified present.

---

## 8. Wardrobe integration — the chain was coded and empty

`DA_MelodiaCosmeticCatalog` held **5 cosmetics and 0 resonant forms**, every `resonant_form_id`
null. The first outfit is `resonant_form_policy: decorative_only` by design, so no equipped item
could grant anything. The entire wardrobe→traversal path — provider registration, registry,
caller, shared capability constants — was already implemented and carrying no data.

Authored the missing link (catalog 4522 → 5232 bytes):

| Field | Value |
|---|---|
| `form_id` | `form.first_resonance_echo` |
| `required_flag_ids` | `[challenge.first_resonance_echo.completed]` |
| `granted_capabilities` | `[Glide]` |
| `restricted_context_ids` | `[battle_session]` |
| linked cosmetic | `Cos_Accessories_MelusinaV2` |

Owner intends this to become a **money pouch** accessory.

### The chain these two halves complete

```
play the piano pattern
  -> OnPatternCompleted
  -> CommitWorldChallenge                     (new adapter)
  -> flag challenge.first_resonance_echo.completed
  -> FormUnlockedAgainst() passes             (new catalog data)
  -> equipping the accessory grants Glide
  -> MelodiaTraversalComponent opens a closed route
```

Music opens a door; the outfit carries the meaning; combat is never touched —
`restricted_context_ids: [battle_session]` enforces the last part in data as well as code.

### Gotcha worth keeping

`save_asset(only_if_is_dirty=False)` **returned success and wrote nothing.** The catalog is
LFS-`lockable`, so it sits read-only on disk. `CURRENT_STATE.md` warns about the dirty-flag
no-op but not this case. Always check the mtime. `GitSourceControl` is off and `github.com` is
unreachable, so no LFS lock could be taken; the flag was cleared locally.

---

## 9. Animation pipeline review

Full findings: [`../MELUSINA_ANIMATION_PIPELINE_REVIEW_2026-08-20.md`](../MELUSINA_ANIMATION_PIPELINE_REVIEW_2026-08-20.md).
Read-only — no animation asset was modified.

Headline: the rig, skeleton (465 bones), blendspace and Kawaii/CopyBone chain are sound. **The
state machine is not.** `Speed`, `bIsGliding` and `bJumpWindup` are never assigned anywhere in
the ABP, which makes `Locomotion` and `Glide` unreachable — `Idle → Locomotion` requires
`Speed > 10.0`. The one blendspace player correctly property-bound to `RuntimeGroundSpeed` is
orphaned outside the pose chain.

`BP_Melusina` carries the deprecated `MelodiaOutfitComponent` and has **neither**
`MelodiaWardrobeComponent` **nor** `MelodiaTraversalComponent`. The V2 mesh promotion is still
open (still `SK_Melusina`, not `SK_Melusina_V2_Body`).

Four independent blockers now stand between the money pouch and an observable effect — see §8 of
that review. None of them invalidate the data authored today.

---

## 10. State at close

### Gates
- Shipping: `runtime`, `save_load`, `repeat_consume`, `package_launch` — **PASS**
- Quality: `static_gates` — **FAIL** (2 material baseline drifts)
- Orchestra: all six — **OPEN**. Nothing was recorded this session.

### Files changed
- Identity: `PROJECT.md`, `README.md`, `_VERTICAL_SLICE_SCOPE.md`, `AGENTS.md`, `DOC_INDEX.md`
- New: 2 orchestra docs, this closeout, the animation review, `run_production_lanes.py`,
  `production_tasks.v1.json`, the narrative challenge bridge (`.h`/`.cpp`)
- Edited: `echo_pipeline.json`, `_TASK_QUEUE.md`, `model_router.py`, `run_math_models.py`
- Repurposed: 24 career/portfolio docs, both MATH copies, `MODEL_WORKFLOW_EVALUATION_REPORT.md`
- Asset: `DA_MelodiaCosmeticCatalog.uasset`

### Untouched
No never-touch file was edited. `Config/DefaultEngine.ini` shows a mid-session mtime, but the
diff is the known `G:` → `C:` DDC repoint — pre-existing work, not from this session. No
`.uasset` deleted, no Blueprint modified, no directory moved.

---

## 11. Next session — start here

1. **Close the editor and build.** The narrative bridge has never been compiled.
   ```
   Build.bat BS_GodFileEditor Win64 Development -Project=".../BS_GodFile.uproject" -WaitMutex
   ```
2. **Fix `Speed`** (animation review §9 item 1) — one binding, and it is the difference between
   Melusina being able to walk or not.
3. **Add the two components to `BP_Melusina`** and set `bRequireCapabilityProviderForGlide = true`.
4. Then PIE the full chain: play the pattern → flag commits once → equip the pouch → Glide →
   reload → confirm no double-grant.
5. Only then record `music_world_key` and `wardrobe_gameplay_hook`.

Do not record a gate before step 4.
