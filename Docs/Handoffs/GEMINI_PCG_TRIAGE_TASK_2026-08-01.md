# Task brief — Gemini (Antigravity): PCG library triage

**Lane:** bulk classification from evidence. Text in, table out.
**You cannot touch assets, the editor, or `.uasset` files.** Anything requiring engine state goes to
Claude/Kiro/Codex. Your output is a decision table someone else executes.

## Correction to your intake, so you don't redo finished work

Phase A is **partially complete and the result inverts the premise.**
`Saved/Audit/pcg_portfolio_audit.json` was generated headless and reports:

```
dead_systems: []      critical_count: 0      clean: true      inventory_count: 136
```

Independently, 17 of the 18 assets declared required by `pcg_portfolio_standards.py` exist on disk.
The only miss is `SMC_Baroque_ScatterKit` (a scatter *collection*, not a graph).

**So "most PCG is unusable" is not supported by evidence.** The likely source of that impression is
named in `pcg_false_zero_audit.py`'s own docstring: `PCGComponent.generate(True)` is **ASYNC**, so
counting instances in the same script returns **0**. A healthy graph checked that way looks dead.
Treat "reported zero points" as *unproven*, not as *broken*, unless the count came from a separate
call after async settle.

**The real problem is different: the library is unused, not broken.** A survey of the four route
levels found only **two** PCG components total —
`PCG_Dreamstate_DistantRuin` (L_KaleidoNave) and `PCG_Morning_MemoryDressing` (L_MelusinaMorning,
extent 270×270, essentially a garnish). `L_FallenMoon` and `ZenForestTest` have **zero**. Meanwhile
127 graphs sit in the library.

## Your task

Classify all 127 `PCG_*` graphs into exactly three buckets, **citing evidence per graph**.

Inputs:
- `Saved/Audit/pcg_portfolio_audit.json` (136-entry inventory, plugin health, level volumes)
- `Content/Python/pcg_portfolio_standards.py` (canonical library layout + required set)
- Graph paths on disk under `/Game/EnvSandbox/PCG/**` and `/Game/_PROJECT/PCG/**`

Buckets:

| Bucket | Definition |
|---|---|
| **Keep** | in `Universal`, `Greybox`, `Collections`, or a shipping `Styles/*` folder, and named in the standards set or plausibly reusable |
| **Candidate** | structurally fine but unused/unreferenced — the likely majority |
| **Retire** | in `_Dev`, `_Scratch`, `_Experiments`, `Legacy_Portfolio`, or an obvious duplicate (e.g. `PCG_RockScatter` vs `PCG_Universal_RockScatter`) |

Known distribution: Universal 33 · Baroque 31 · WP 16 · Escher 14 · Sakura 4 · Greybox 2 ·
scratch-ish 10 · `_Deprecated` **1**.

## Rules

- **Never recommend deletion.** Retire means *move to `_Deprecated`* — reversible. This project has
  repeatedly found "dead" assets that a `.umap` still referenced.
- **Do not infer health from a zero point count** — see the async note above.
- Flag duplicate-looking pairs rather than picking a winner; the owner decides.
- If evidence is missing for a graph, put it in **Candidate** and say what evidence is needed. Do not
  guess.

## Deliverable

One markdown table: `graph path | bucket | evidence | note`. Plus a short list of the duplicate pairs
you found. Nothing else.

## Second task if you finish

You correctly identified **86 rows of dead `DataStructures` JSON** unwired from C++. Produce a
conversion spec — for each JSON file: target `UDataTable` row struct, field-by-field mapping, and
which hardcoded function it would replace (e.g. `GetDemoEnemies()`). **Spec only, no code** — the C++
lands in Rider/DeepSeek's lane with the compiler in the loop.
