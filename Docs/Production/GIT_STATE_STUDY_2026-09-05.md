# BS_GodFile Git & Systems State Study — 2026-09-05

Prepared for: owner (fall term, Epic Games professor lens, Houdini→UE lab workflow).
Method: live `git` probes (ancestry, tree-diff census per branch, gh PR state, port-9316
editor lock, ledger read). Every number below came from a command, not from prose.

---

## 1. The single most important fact: there are TWO unrelated histories

```
git merge-base origin/main HEAD   →   (empty — no common ancestor)
origin/main : 699 commits, tip 2fc1d056 (2026-09-05, "keep PR28 canon branch in active set")
local HEAD  : 732 commits, tip 999b42cf (2026-09-05, "docs: session closeout")  [codex/game-state-2026-09-04]
```

These are not "diverged" in the normal pull/rebase sense. They are **separate histories**
that share remote-name and file paths but have no join point. All the `push REJECTED /
non-ff` pain traces back to this.

- **Line B — origin/main (GitHub "V2" line).** Receives pushed/PR'd work: the
  2026-09-02 merge-train era (B00–B08), the three.js site/folio branches,
  weapon-gallery, endless-journey docs, collab/laptop reconciliation branches,
  the 101-branch remote prune tooling. Remote has 121 branches, 3 open PRs:
  #96 MERGEABLE, #94 MERGEABLE, #28 CONFLICTING.
- **Line A — local line (`codex/game-state-2026-09-04`).** Newer gameplay truth that
  never reached GitHub: material master convergence (nikki + orphan cleanup + flipbooks),
  4 live battle-trigger bug fixes + crash root-cause, wardrobe watch heartbeats,
  P0 ledger convergence (all 10 gates), session closeout 09-05. This is the line the
  editor and `Saved/gate_ledger.json` reflect.

### The abandoned bridge
`merge/unify-histories` (and clones `recovery/`+`backup/unify-histories-20260904`,
all tip `62b80fee`, 2026-09-04) merged the two lines **as they were on 09-04** — but
contains neither current tip. Both lines moved past it on 09-05. It is a stale bridge:
useful as a conflict map (it already resolved ~1,451-file overlap once), not as the merge.

### Content drift at the tips
`git diff --name-only origin/main HEAD` ≈ **1,471 files**, concentrated in:
`Content/__ExternalActors__` (350), `Content/Melodia` (281), `Content/EnvSandbox` (258),
`Saved/Audit` (75), `Content/Python` (55), plus Docs. Both sides have real content the
other lacks. Neither may be discarded.

### LFS landmine (why a naive merge will hurt)
- origin line tracks LFS (`.gitattributes` has 35 filter=lfs lines); several origin-side
  `.uasset` diffs show as **3-line LFS pointer** changes.
- `.git-rewrite/` exists in the repo root — a git-filter-repo pass happened and left
  residue. The two lines therefore have **different object storage models for the same
  paths** (raw on one side, pointer on the other). Expect
  `Encountered N files that should have been pointers, but weren't` on checkout/merge
  until normalized. This is mechanical to fix but must be part of the plan, not a surprise.

### Local branch census (43 local; classified by tree-diff, not ancestry)
Because histories are unrelated, `git branch --merged` is near-useless here; tree
distance to each line's tip is the honest classifier:

| Group | Branches | Meaning |
|---|---|---|
| ≡ Line A tip | `codex/game-state-2026-09-04` (=HEAD), `-checkpoint` | Current gameplay truth |
| On Line B (tree ≈ origin/main) | `codex/p0-closeout-lfs`, `codex/weapon-gallery`, `copilot/fix-runners-*`, `cursor/git-health-checkpoint`, `cursor/phone-party-trick`, `cursor/threejs-integration`, `docs/2026-09-02-endless-journey`, all four `feat/2026-09-02-*`, `integration/...front-door`, `integrate/...b07`, `cleanup/triage-from-origin` (merged) | Already represented on GitHub — delete candidates after unify |
| Stale-base docs (08-19…08-31 era, 2,600–6,900-file diff to both lines) | `cursor/nemotron-*`, `cursor/perforce-docs-*`, `cursor/zenforest-*`, `cursor/recruiter-sendoffs-*`, `cursor/branch-cleanup-*`, `docs/2026-08-29-*` (PR #28), `docs/2026-08-31-*`, `docs/toolchain-consolidation`, `codex/perforce-*`, `copilot/new-feature-implementation`, `rnd/blender52-music-gn-studio`, `claude/tonight-cymatic-*`, `claireon-test`, `feature/repo-lockin`, `feature/p0-closeout-2026-09-02` (anomalous tree — inspect before delete) | Cherry-pick surviving docs onto unified main, then delete |
| Line A work with unique files | `cleanup/integrate-batches-2026-09-03`, `docs/university-prep-2026-09-03`, `llm/fromage/BS_GodFile/shorewake-chapter-loop`, `recovery/main-merged-20260904` | Merge into Line A *before* unify, or cherry-pick after |
| Bridge artifacts | `merge/unify-histories`, `recovery/`+`backup/unify-histories-20260904` | Keep one as conflict map until unify succeeds; then delete |

---

## 2. The unification plan — safe, isolated batches

⛔ Preconditions (hard):
1. **UE editor must be closed for any merge touching `Content/`.** Port 9316 is
   *listening right now* (PID 45412). `git merge` of 1,400+ asset files with the editor
   open = locked-file failures mid-merge = the worst state to be in.
2. Bundle backups first (never `git clean`, never `checkout -- .` — AGENTS.md):
   `git bundle create ../pre_unify_A.bundle --branches` and a second for origin refs.
3. The final push to `origin main` requires **`--force-with-lease`** and is only safe
   because the unify merge makes origin's history a strict *ancestor* of the new tip —
   nothing on GitHub is lost. This is an OWNER SIGN-OFF action, matching the
   `melodia-git-unrelated-merge` skill. Sign-off asked, not assumed.

**Batch 0 — freeze.** No new commits on either line during the operation. Laptop/second
workstation (`/g/EnvironmentPortfolio-git/.git` exists — a real second clone) must push
last state to origin *before* unify or it becomes a third line.

**Batch 1 — converge Line A internally.** Merge into `codex/game-state-2026-09-04`,
one at a time, verifying each with tree diff before the next:
`llm/.../shorewake-chapter-loop` → `docs/university-prep-2026-09-03` →
`cleanup/integrate-batches-2026-09-03` → `recovery/main-merged-20260904`.
(Deliberately excludes the two `unify` and `checkpoint` branches — they're snapshots.)

**Batch 2 — LFS normalization.** Decide ONE model: uassets via LFS.
`git lfs migrate import --include="*.uasset,*.umap"`-style pass over the unified Line A,
`git lfs fetch --all origin` to pull the 699 commits' objects. Fix
`should have been pointers` at the boundary. Do this BEFORE the cross-line merge so the
merge resolves pointers, not raw-vs-pointer conflicts.

**Batch 3 — the cross-line merge.** From unified Line A:
`git merge origin/main --allow-unrelated-histories` — resolve using
`merge/unify-histories` (`62b80fee`) as the oracle for which side won each of the
1,451 files it already resolved; then hand-resolve the 09-04→09-05 delta (small).
**No `-X theirs`/`-X ours` blanket** — that flag silently deletes a year of art.
Verify: `git rev-list --count HEAD` ≈ 732 + 699 + batch commits + merges; both tips are
ancestors; `gate_ledger.json` shows the 09-05 passes (Line A wins for
`Saved/gate_ledger.json`, `Content/Melodia` materials, battle fixes; Line B wins for
`site/` three.js work, deploy tooling, docs indexes).

**Batch 4 — certify.** Editor open (after merge): full closed-editor `Build.bat`,
`pytest`/unittest contracts, one PIE smoke, then owner sign-off.

**Batch 5 — push + prune.** `git push --force-with-lease origin main`. Merge PRs #96,
#94 if their content survived Batch 3 (they were MERGEABLE *into old origin/main* —
re-check against unified tree; likely absorbed). Resolve #28 (docs-only → cherry-pick
the surviving docs, close PR). Delete every Line-B branch group + stale-base group
locally and remotely (the repo already has `ae6f5a18` reversible prune tooling on
origin — use it; deletion is reversible while reflogs hold).

**Batch 6 — hygiene.** `git gc --prune=now`, remove `.git-rewrite/`, single
`main` + a naming convention going forward: `chapter/<name>`, `sys/<name>`, `docs/<name>`.
One line, one truth.

Estimated destructive risk after Batch 0 freeze + bundles: **low**. The one-way doors
are Batch 5's force-push (mitigated: additive, verified ancestry, bundles) and remote
branch deletion (mitigated: reversible tooling + bundles).

---

## 3. System-by-system: what each pillar is, and where it will bite

The target — a **reusable chapter system** — means each chapter =
`Quill script + encounter allowlist entries + level/map slice + outfit/asset set + score`.
Here is each system's real state and its roadblock:

### 3.1 Narrative spine (QuillScript + `UMelodiaNarrativeSubsystem`)
- State: healthy and authority-clean. Seven-verb notification contract, allowlist
  `DA_MelodiaIntegrationConfig` carries all 27 authored IDs, five P0 `.qsc` compiled,
  contract tests 4/4. `melodia:item:` is still a **logging stub** (no inventory consumer).
- Roadblock for chapters: the allowlist is a *single* data asset — every chapter edits
  the same `.uasset` → merge conflict magnet (this is exactly how the two lines drifted
  apart in `Content/`). Mitigation: per-chapter allowlist child assets, or accept it
  as the one owned-by-main file. Also: `bRelaxedAllowlistInEditor=true` means chapter
  typos pass in PIE and die in shipping — a per-chapter checklist item with it OFF.

### 3.2 Battle/rhythm (TurnBasedJRPG + MelodiaRhythmCombatSubsystem)
- State: all 10 P0 gates have ledger rows (verified 09-02, Line A). Battle-trigger
  bugs fixed 09-05. Rhythm is owner-locked WORKED — highway is *functional but clunky*;
  note presentation feel is the known debt.
- Roadblock: gates `package_launch` certification is aging; rhythm feels "clunky" per
  owner PIE — that's a T3D presentation task, not an architecture one. The real risk
  is the **two-writers-on-HUD class of defect** (AGENTS rule: `bExecutionDrivingHighway`
  ownership) — every new chapter's custom encounter must ride the existing seam, never
  push its own highway. For an Epic professor review, this ownership protocol is a
  *strength to present*, if the doc stays current.

### 3.3 Wardrobe (outfits = presentation + gameplay meaning)
- State: equip roundtrip + gameplay hook + presentation swap gates pass; canonical
  Shorewake asset is `Saved/CANONICALSHOREWAKEOUTFITWEIGHTEDUNWRAPPED.usdc` (270k v,
  28 mats) living in `Saved/` — **outside Content, partially outside versioning**, and
  `Content/Melodia` differs 281 files between the lines right now.
- Roadblock: the Blender→UE garment route (retopo → Substance/hand-paint → rig → MI) is
  the slowest lane and the one the two-workstation split hits hardest. A reusable chapter
  needs an *outfit intake contract* (slot names, material master names — the 09-05
  toon-master convergence just made masters stable, so pin chapters to masters, not
  per-outfit one-offs). Name-match sensitivity is live (university-prep branch rewired
  10 V2 accessory slots to name-match) — renaming anything in Blender breaks the seam
  silently.

### 3.4 World/materials (Sea Above, KaleidoNave, PCG, cymatics)
- State: masters converged (09-05, Line A). EnvSandbox + `__ExternalActors__` (World
  Partition) = 608 of the 1,471-line-diff files. `world_field_bus_pie` and
  `sea_above_dressed_map` gates have recent rows. Height-aware PCG placement mandatory.
- Roadblock: **World Partition external actors are the git-ugliest files in the repo**
  (thousands of tiny actor uassets, churn on every editor save). Two people/two
  machines editing one map = guaranteed conflict soup. Chapter system mitigates this:
  one `.umap`/one data-layer region per chapter, owned by one writer at a time, and
  `gitattributes lockable` (already upgraded on Line B). Houdini→UE: keep heightfield/
  mesh handoff via FBX/usdc into a staging folder, never direct Content edits from two
  tools at once.

### 3.5 Audio/music (MusicClock, beat maps, instruments, Melusina voice)
- State: MIDI beat-grid imported properly (never hand-build `UMidiFile` — crashed the
  editor once), Harmony/MusicClock live, instrument treatment skills exist, rhythm
  grading stays classical (quantum only pre-play ranking, per policy).
- Roadblock: audio assets are LFS-size bombs waiting to happen, and instrument meshes
  + their animations live across the C:/G:/ boundary (Exports/MelusinaInstruments).
  A chapter needs an *audio manifest* (song→beatmap→lane-set) as a plain JSON/text
  asset so merges are reviewable diffs, not binary.

### 3.6 Save/game-state (narrative record, checkpointing)
- State: `melodiaNarrativeRecord` field on BP_JRPGSaveGame, `melodia:stat:` idempotency
  per IntentId proven, save/reject-inconsistent-wardrobe fix rode
  `feat/2026-09-02-runtime-persistence-closure` (Line B side — must survive Batch 3!).
- Roadblock: chapter reusability means the narrative record must key by chapter id or
  old saves poison new chapters. Also `Saved/` is where gate ledgers AND canonical usdc
  live — decide once what of `Saved/` is versioned (Audit json/md: yes, per rule 26;
  everything else: no).

### 3.7 Web/portfolio lane (three.js folio, Pages, atmosphere)
- State: entirely on Line B (4 feat/* site branches, PRs 94/96 neighborhood).
- Roadblock: none for the game; the hazard is that site work and game work share one
  repo, so every Batch-3 conflict is game-vs-site noise. If it bothers you in fall,
  that's the moment to split the portfolio into its own repo — after unify, never before.

### 3.8 CI/gates
- State: echo pipeline + `record_gate.py` + ledgers; `static_gates` chain is
  editor-gated. CI yml fixes live on Line B (`copilot/fix-runners`).
- Roadblock: after force-push, CI runs against the unified tree for the first time in
  the unified repo's life — expect red on day one; budget one evening for green-up.

---

## 4. G: ↔ Git sync protocol (lab Houdini + laptop prep + this workstation)

Ground truth from disk: `G:\EnvironmentPortfolio\BS_GodFile_STALE_G_do_not_launch` (the
renamed stale copy — its texture/mesh LoadError floods are why it must stay dead),
`G:\BS_GodFile_Mirror\`, `G:\BS_GodFile_Archive\`, and **`G:\EnvironmentPortfolio-git\.git`
— a real second git repo on G:**. That last one is a future third history line unless
given rules.

Proposed standing protocol — **git is the spine, G: is the foundry:**

1. **Source of truth:** `C:\EnvironmentPortfolio\BS_GodFile` (git) for everything
   tracked: `Source/`, `Content/` (tracked subset), `Docs/`, `Tools/`, `Saved/Audit/`.
   G: drives never hold a second clone of the game repo while I work; the G: repo
   becomes either the *laptop-sync drop* (bundles in/out) or gets retired — owner's call.
2. **G: = staging for fat and in-progress binaries:** Houdini hipnis, Blender .blends,
   Substance .sbsar/.sbs, raw FBX/usdc bakes, 4K texture working sets. None of that
   enters Content/ until it passes intake. Naming: `G:\Foundry\<chapter>\<asset>\<date>\`.
3. **One-way intake, always via the workstation:** G:\Foundry → copy into
   `Content/.../Staging/` (or importer script) → editor import → save the .uasset →
   git commit. The *uasset* is versioned; the source .hip/.blend optionally goes to
   LFS or stays on G: with a `MANIFEST.json` sidecar (path, hash, date, version).
   That manifest is the professor-defensible paper trail.
4. **Laptop (2D/audio asset prep):** clone via **sparse checkout** (Line B already
   learned this lesson — `f0fa8b73 fix(sync): make sparse laptop checkouts include
   current house/discovery state`). Laptop commits only to `Tools/`, `Docs/`, audio
   `Content/Audio`-adjacent paths it owns; never `Content/Melodia` materials or maps
   it can't open at the labs. Push small, push often, rebase-onto-main daily.
5. **Lab machine (Houdini→UE):** treat it like the laptop until it can hold 151 GB.
   Bring bundles, not clones: `git bundle create lab.rday.bundle main` on the way in,
   a thin `collab/lab/*` branch pushed from wherever UE lives on the way out.
6. **Never** two machines editing the same `.umap`/WBP/DA between syncs. Map ownership
   per chapter + lockable attributes makes this visible instead of tragic.
7. **Large-file discipline before fall:** anything >50 MB that must be versioned is
   LFS-only; anything that must NOT be versioned is gitignored at the pattern level,
   not by one-off deletions.

---

## 5. Recommended fall ordering (roadmap)

1. **Week 0 (now): execute Batches 0–6** — one calm evening, editor closed, bundles made.
   Everything else is blocked behind a unified main; the longer the two lines breathe,
   the uglier Batch 3 gets. This is the highest-leverage hour available.
2. **Chapter contract doc:** formalize `chapter = script + allowlist-delta + map-region +
   outfit-set + audio-manifest` with the five intake seams named (3.1–3.6 above), as the
   artifact you show the professor.
3. **Prove reusability with Chapter 2:** build the next chapter purely through the
   contract, zero engine-code changes. Where it forces a code edit, that's the seam to fix.
4. **Rhythm note-presentation pass** (the known "clunky") + fresh `package_launch`
   certification for the term-demo build.
5. **Optional:** portfolio repo split (3.7) after two chapters live on unified main.

## 6. Open owner decisions (nothing below was done silently)

- [ ] Sign-off for Batch 5 `--force-with-lease origin main` (additive; verified ancestry first).
- [ ] Fate of `G:\EnvironmentPortfolio-git` second clone: designate as lab-drop only, or retire.
- [ ] `-X theirs` forbidden blanket — confirm hand-resolution budget (est. 1–2 sessions).
- [ ] Whether `feature/p0-closeout-2026-09-02` (anomalous tree) gets asset-inspection before prune.
- [ ] `Saved/` versioning line: Audit json/md yes (rule 26) — confirm canonical usdc lives there or moves to LFS-tracked `Content/Melodia/Wardrobe/Sources/`.
