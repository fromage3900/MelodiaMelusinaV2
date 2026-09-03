# AI agent goals — 2026-08-02 (website publish day)

**Context: the site ships tonight regardless of polish level.** Every goal below is written to serve
that. Anything that does not make the site better tonight is explicitly deferred, not forgotten.

The owner's Claude budget is nearly exhausted. **Prefer the cheapest agent that can do the job**, and
prefer work that does not need the Unreal editor (it hung this session on a heavy PCG generate).

---

## The one thing that matters tonight

**Ship the site.** The portfolio work is already good enough to publish:

- 3 hero PCG graphs, two of them measurably novel (exact Penrose P3 tiling; tensor-swept nave vault)
- A 126 m walkable cathedral aisle, verified zero obstructions
- A working spline-driven scatter carve
- A published heatmap/plan/section artifact:
  https://claude.ai/code/artifact/86244ae1-3e81-4939-b0e8-cbdc013e53e1

**Do not start new features today.** Anything that is not "capture, caption, publish" is tomorrow.

---

## Per-agent goals

### Cline (has image viewing) — **highest leverage today**

**Goal: produce the portfolio capture set.** This is the only lane that directly ships the site.

1. Capture the three heroes at matched camera: `PCG_Hero_PenroseTiling` and `PCG_Hero_InfiniteNave`
   in `L_FallenMoon`; `PCG_Hero_TeaGarden` in `ZenForestTest` **if it generated** (unverified — the
   editor hung, see below).
2. Judge two look calls I could not, having no eyes on it:
   - `InkBlurStrength` is now **0.45** (was 0.28). Too soft?
   - `M_PP_MeluColorGrade` V2 split-tone at `SplitAmt 0.30`. Too strong?
3. **Outline jitter is still visible** — capture a slow orbit on the Penrose lattice (780 thin beams,
   the harshest silhouette in the project) so there is a reference clip for the next fix attempt.

Best shot for the site: the Penrose tiling. It is mathematically exact and rare in game portfolios.

### DeepSeek (Rider, compiler in the loop) — mechanical, no look decisions

1. **Promote `M_PP_MeluColorGrade` V2 consts to real parameters.** Recipe in
   `Docs/Handoffs/PPV_DEEP_STUDY_V4_2026-08-02.md`. Values unchanged at promotion so the look cannot
   drift. ⚠️ `update_custom_hlsl_node`'s `inputs` field **replaces all inputs** — re-wire all 16.
2. Author `MI_MeluColorGrade_*` profile variants once parameters exist.
3. **Do not touch** `M_PP_StorybookOutline_Premium_Candidate` — jitter work is unresolved and
   in-flight.

### Kiro (gameplay) — keep clear of PCG/PPV

**Kiro is actively working the Melody Token wallet integration** (owner-confirmed 2026-08-02).

⚠️ **A file survey run the same day wrongly reported it "not started" — do not repeat that check.**
It grepped only **C++ under `Plugins/`** for a `TokenPickup` class. Pickups and HUD are **Blueprint**
assets (`BP_` / `WBP_`), completely invisible to a C++ grep. To assess this lane, search `Content/`
for Blueprints referencing `UMelodiaTokenWalletSubsystem` — or just ask Kiro.

General lesson: **a C++-only search cannot tell you whether Blueprint work exists.** Absence of
evidence from the wrong search space is not evidence of absence.

Kiro *has* completed and verified: traversal input-authority gating (`IsMovementAllowed()`), Quill
scoped `Dialogue` input context push/pop, `DT_MelodiaTokens.json` pointed at the released material
paths, and `_TASK_QUEUE.md:93` wiring item 2c (OpenLevel→TravelTo, fingerprint-stable, 6/6 nodes).

`UMelodiaTokenWalletSubsystem` is released and Live-Coding patched. Console commands
`melodia.Wallet.Dump/Grant/Spend/AddMana/SpendMana` allow testing without building assets. Cline
independently verified idempotency/branch behaviour on Aug 1 — all checks pass.

**The untested case that reaches players:** grant with a GrantId → save → **fully exit the process**
→ relaunch → load → repeat the same grant must still be rejected. An in-memory guard passes the
reopen-dialogue test and still double-pays after relaunch.

### Gemini (Antigravity) — text in, table out

PCG triage is now much cheaper: the 2026-08-02 audit already classifies all 138 graphs by source-node
type, coordinate space, broken-mesh usage and compensating scale. See
`Docs/Handoffs/PCG_LIBRARY_REVIEW_2026-08-02.md`. Produce the Keep / Candidate / Retire table on top
of that data rather than re-deriving it.

---

## ⚠️ The root docs were stale — fixed today, but know why

All four "read these first" docs stopped updating between **Aug 1 11:08 and 15:52**, while
`Docs/Handoffs/` gained 10+ files across Aug 1 evening and all of Aug 2 (wallet release, Cline's
verification, the PCG session, mesh-scale repair). **Anyone starting fresh from `_SESSION_HANDOFF.md`
would have missed the entire wallet handoff and a full day of PCG work.**

- `_SESSION_HANDOFF.md` — **rewritten today**, now current.
- `_TASK_QUEUE.md` (Aug 1 11:08) — predates the wallet release entirely, **has no pickup/HUD row at
  all**. Kiro's top task is not even tracked. Row added today.
- `Docs/QUEUE.md` (Jul 31) — claims `_DECISION_LOG.md` is "through Decision 011"; it is actually
  through **037a**. Badly stale pointer.
- `_DECISION_LOG.md` (Aug 1 12:29) — the wallet-authority decision described at length in the Kiro
  handoffs was **never logged here**. Worth appending so it is not re-litigated.

**Process lesson: handoff docs in `Docs/Handoffs/` are where the work actually gets recorded, and the
root index docs drift behind within hours.** Check mtimes before trusting any root doc.

## Open P0s (surveyed 2026-08-02, ranked)

Most are "fixed but never PIE-walked" — they need a play session, not more code.

| # | Item | Where |
|---|---|---|
| 1 | **Melody Token pickup/HUD unimplemented** despite being unblocked ~20 h | `KIRO_MELODY_TOKEN_INTEGRATION_2026-08-01.md` |
| 2 | Death routes to stock JRPG menu — fixed via CDO, **not PIE-walked** | `_TASK_QUEUE.md:30` |
| 3 | Dreamstate portal → KaleidoNave — fixed, **not PIE-walked** | `_TASK_QUEUE.md:29` |
| 4 | Stock battle widget package instantiated at runtime — reopened | `_TASK_QUEUE.md:35` |
| 5 | Attack/Skill/Item/Flee input parity unverified | `_TASK_QUEUE.md:36` |
| 6 | Victory/Defeat/Fled result matrix unverified | `_TASK_QUEUE.md:37` |
| 7 | `BP_JRPGSaveGame` full-restart persistence unverified | `_TASK_QUEUE.md:38` |
| 8 | Canonical save round-trip — **gates everything downstream** | `_TASK_QUEUE.md:96` |
| 9 | Packaged build never launch-tested outside the editor | `_TASK_QUEUE.md:49` |

**Palette authority is SETTLED, not open:** `MPC_Melodia_Palette` is canonical; `MPC_Portfolio_Palette`
is not the authority. Decided 2026-08-01 and recorded in `CLAUDE_TO_KIRO_STATE_2026-08-01.md`. It was
briefly re-listed here as an open decision — that was an error. **Do not re-raise it.**

Items 1–9 above are mostly "fixed but never PIE-walked" — one focused play session, not more code.

## Highest-leverage engineering tasks (ranked, for after tonight)

1. **Fix the 29-mesh scale problem properly — 18 done, 11 left.** ~49 % of graphs spawn a
   broken-scale mesh. ⚠️ **Check for compensating scale in the graphs first** — that double-correction
   is what produced the 3200 m colonnade.
2. **Diagnose `PCGVolumeSampler`** — emits zero project-wide, blocking **40 graphs**. Single highest
   unlock in the library.
3. **Outline jitter.** Root causes identified and partly mitigated, still visible. Untested lead: the
   outline recomputes edges *after* TSR has resolved, so no UV compensation can fully fix it —
   test whether it belongs earlier in the chain.
4. **Controller knobs.** `BP_MelodiaPCGControl` has 11 knobs and none of them drive anything.
   `PCGAttributeFiltering` exposes no threshold pin; two routes documented in
   `Docs/Handoffs/PCG_TEAGARDEN_HERO_2026-08-02.md`.
5. **Duplicate level assets** — `/Game/L_InfiniteScore` vs `/Game/EnvSandbox/Environments/L_InfiniteScore`
   (same for `L_MelusinaMorning`). The PPV stack was applied to the EnvSandbox copy only. **Check
   which one the GameMode loads before the next capture.**
6. 15 graphs with compensating scale; 3 WORLD-space graphs; 8 empty spawners.

---

## Known-unstable — read before driving the editor

- **The editor hung** on a `PCGSpawnActor` generate into `ZenForestTest` (633k foliage instances +
  World Partition external actors, with `delete_actors_before_generation` on). Not a crash. **Test
  actor-spawning graphs in a light level first.**
- **Never save `ZenForestTest`.** Owner art sits dirty there. The Infinite Nave and Tea Garden were
  both placed but deliberately left unsaved.
- `L_SakuraPath` and `L_MelusinaMorning` are approval-gated for the remaining mesh repairs.
- Verify positionally, never by instance count. Three wrong conclusions this session came from
  trusting a count over a position.

---

## Canonical reference

`Docs/Handoffs/PCG_SESSION_WINS_2026-08-02.md` is the consolidated record — silent-default traps,
PCGEx shape rules, the spline carve recipe, the Penrose method, mesh-scale repair, PPV state, the
traversal envelope, and verification discipline. **Start there** rather than re-deriving.
