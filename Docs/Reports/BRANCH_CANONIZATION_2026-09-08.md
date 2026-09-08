# Branch Canonization Ledger — 2026-09-08

**Purpose:** record the branch state before the September 8 canonicalization pass and prevent old refs from being mistaken for current project truth.

## Game repository baseline

Canonical repository: `fromage3900/MelodiaMelusinaV2`  
Pre-canonization `main`: `ab263f807d2c4bb8f0e91ea72f80e3c65705de49`

### Branches safe to supersede / normalize

These branches were reviewed against current `main`. Their useful work is already represented on `main`, landed through later commits, or moved to the correct separate repository:

| Branch | Pre-cleanup tip | Decision |
|---|---|---|
| `docs/choral-sheep-reference-boards-2026-09-08` | `6127d9ac491224fc44f52f478cec8ae98aab1a9c` | superseded; boards are on current main |
| `docs/git-archaeology-closeout-2026-09-08` | `b71af569ddf9100627b1d4b053fe28bb1cb150f0` | superseded; closeout landed on main |
| `docs/repo-authority-cleanup-2026-09-08` | `2f561565b9ba2b3165f7227a32c07a32d5efd755` | superseded by current authority docs |
| `docs/superseded-td-plans-2026-09-08` | `dc4eab2cbf677e1a9570e8e0a7daf7ebe2c57eed` | superseded; TD plans marked historical on main |
| `docs/td-live-performance-contract-2026-09-08` | `0ebe28c38c87cd14fe676481f3b222ca2e571ce7` | contract landed in canonical TD repo; core copy not authority |
| `docs/td-research-cross-repo-landing-2026-09-08` | `999c020bd429b74834f9f94eb2de66bdee0d8103` | handoff reconciled on main / TD repo |
| `feature/melodia-studio-3d-pipeline` | `cf0f7419d5224ddf4c2083385cb442fe8e94c47c` | fully behind main |
| `feature/semester-render-queue-2026-09-07` | `27c5c4cc8f32f0767784d038119d68193e7b1cc9` | render queue tooling present on main |
| `fix/capstone-day-plan-convergence-2026-09-08` | `d73b6b43dd6128117b45c1f3710ebf91569bc986` | fixes represented on main |
| `fix/render-queue-ps51-2026-09-07` | `e5d9d0cc7ba9d529b97ba410a19d00783ff1439a` | PS5.1 fixes represented on main |
| `fix/repo-authority-workspace-vs-repo-2026-09-08` | `679e26cf144d8ce75c194964219ef055c82d1a88` | final authority wording already on main |

### Preserved recovery / operational refs

| Branch | Tip | Why it remains separate |
|---|---|---|
| `cleanup/root-trim-docs-2026-09-06` | `aac8c1905a5d7e8d687a90d8068b3983053a7599` | 51-ahead historical cleanup line; contains recoverable Humber prep material |
| `collab/laptop/longterm` | `825fb91c92038f61965c0bb8e102d225f5b465b3` | 126-ahead diverged laptop history; extract deliberately only |
| `docs/stale-session-start-fix-2026-09-06` | `0f9d8b8b1ea656f3a4820d18d8b92fd934306fc8` | old recovery line with potentially unique material |
| `integration/semester-closeout-salvage-2026-09-07` | `53660c0e4c70e63c911ef24e8a63bd92ed7dac55` | salvage branch with broad binary/source changes; never merge wholesale |
| `render-queue` | `9b6785b3167d81c335382d2fbe90de8340c84afd` | operational job-manifest branch by design |

### Recovery note

`Humber_FinalYear_Prep/Capstone_Portfolio_Tracker.md` exists on `cleanup/root-trim-docs-2026-09-06` at blob `318a09322ab113d665d787d06803272c50719d67`.

That historical tracker does **not** contain the later Gemini-reported Shot 6 wording and should not be promoted without updating it against current capstone truth.

The previously reported:
- twelve `MI_ChoralSheep_Coat_PC*` material instances;
- game-repo `shot6_hand_track.txt`;
- game-repo `shot6_audio_beats.txt`;

were not present on current game `main` during this reconciliation.

## Website repository baseline

Canonical repository: `fromage3900/my-site`  
Pre-canonization `main`: `d76aa9e3c4d675686d5ca54772f00c6f07aad18d`

All non-main website branches were inspected. Current `main` already contains newer/canonical forms of the relevant atmosphere, Living Worlds, repository-authority, validation, and sendoff work.

Pre-cleanup tips:

| Branch | Tip |
|---|---|
| `docs/repo-authority-cleanup-2026-09-08` | `77e6095b5497b01d3075cec0d2203ae26a5b5034` |
| `feat/2026-09-02-melodia-atmosphere` | `38d410b087b52347471f8576ce57facd7fa82129` |
| `feat/2026-09-02-melodia-browser-constellation` | `e6604a2f5b75754a7d96cebd022dfe3fa922bf83` |
| `feature/melodia-atmosphere-root` | `741b7c4153c915a589710c01c4b956575540a9ec` |
| `feature/melodia-living-worlds-threejs` | `f99a596773bdf815d8f44087fd1dd0d2428ee051` |
| `fix/pages-validate-missing-refs` | `e66a19e40a5a3f13919c0af464997bb0f8da7376` |
| `fix/repo-authority-workspace-vs-repo-2026-09-08` | `77d7327e24dbe8c7128418828f387193c8ceee29` |
| `portfolio-sendoff-20260813` | `0fd0307c9ca6094da9124a8729e65d6a6d1e0759` |

These are superseded by the current site `main` and may be normalized to the post-canonization main tip.

## TouchDesigner reference

Canonical `MelodiaTouchDesigner/main` observed during this pass: `d73983388adf2a6add79738642c41f323883c9fc`.

Latest current facts used by the cross-repo pipeline:
- six-state Chladni Fleece scene and rendered TD evidence landed;
- canonical UE/TD OSC semantics use `:9000`;
- UE integration material/telemetry prep landed;
- UE→TD `UE_Beauty` Spout ingest remains VERIFY LIVE unless newer runtime evidence is captured.

## Rule going forward

A stale branch name is not a task list.

Before reviving any branch:
1. compare it to current `main`;
2. identify one unique file/change;
3. migrate only that unit with provenance;
4. never merge a recovery branch wholesale merely to make the branch count smaller.
