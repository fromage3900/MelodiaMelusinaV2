# Rider + OpenCode + Ponytail Engineering Cockpit

**Purpose:** canonical native-engineering cockpit for Melodia Melusina.  
**Status authority:** `CURRENT_STATE.md`.  
**Runtime authority:** Unreal Engine.  
**Editor mutation authority:** one open Unreal Editor through the existing Monolith owner.  
**Decision/orchestration layer:** Jev when bounded judgment is useful.

This lane is the normal place to do serious UE5.8 engineering. It is not a side experiment.

---

## 1. Stack

```text
JetBrains Rider
  ├─ Unreal-aware code / Blueprint intelligence
  ├─ UHT-aware inspections
  ├─ native debugger + Unreal log
  ├─ RiderLink focused Unreal automation
  ├─ Qodana static analysis
  └─ OpenCode terminal / agent surface
        ├─ Ponytail UE5.8 rules + /ponytail commands
        ├─ project AGENTS.md + production playbook
        ├─ Monolith MCP -> the ONE Unreal Editor
        ├─ project filesystem / Git tools
        ├─ approved model providers
        └─ Jev as bounded director/orchestrator when judgment is needed
```

The layers compose. They do not replace one another.

- **Rider** understands the codebase and Unreal reflection.
- **Ponytail** injects a UE-aware "lazy senior" implementation/review discipline into OpenCode.
- **OpenCode** is the embedded coding-agent execution surface.
- **Qodana** is the canonical static-analysis gate.
- **RiderLink** runs focused Unreal automation against the intended editor session.
- **Monolith** is the only editor-mutation/readback owner.
- **Jev** selects among bounded legal strategies/actions when judgment is actually needed.
- **UBT/UHT/Unreal runtime** remain deterministic authorities.

---

## 2. Ponytail status and portability

The project configuration at `.opencode/opencode.jsonc` loads:

```text
./Tools/vendor/ponytail-ue58/.opencode/plugins/ponytail.mjs
```

Ponytail was adopted for the UE5.8 lane as a **machine-local vendored dependency**. The vendor directory is intentionally swallowed by the repository's `Tools/*` ignore policy and is not source-controlled here.

Therefore:

- configuration is tracked;
- the third-party checkout is machine-local;
- absence of `Tools/vendor/ponytail-ue58` on a fresh clone is expected;
- use `deploy/verify_rider_cockpit.ps1` to verify the lane;
- use its explicit `-InstallPonytail` switch to rehydrate Ponytail when authorized.

Do not make a missing local vendor checkout look like a game-repository regression.

Canonical upstream recorded by the project:

```text
https://github.com/prielgaier/ponytail-ue58.git
```

The project previously recorded the fork as MIT and UE5.8-aware. Re-check upstream before changing version/fork or committing a license-sensitive redistribution decision.

---

## 3. Ponytail commands

When OpenCode successfully loads the vendored plugin, the project expects these surfaces:

```text
/ponytail lite
/ponytail full
/ponytail ultra
/ponytail off
/ponytail-review
/ponytail-audit
```

Use them as review/implementation discipline around the current Melodia authority model.

### Recommended use

**lite**
- tiny `.cpp` implementation;
- local cleanup;
- focused test fix.

**full**
- reflected C++ change;
- subsystem work;
- multi-file integration;
- native/editor boundary work.

**ultra**
- difficult ownership/debugging problem;
- architecture-sensitive refactor that has a demonstrated blocker;
- deep review of a risky native seam.

**review**
- pre-PR review after deterministic gates;
- inspect for Unreal ownership mistakes, unnecessary abstraction, unsafe lifetime/reflection choices and BP/C++ boundary violations.

**audit**
- read-first codebase/feature audit before touching a mature subsystem.

Ponytail never outranks `AGENTS.md`, `CURRENT_STATE.md`, the working agreement, or named subsystem contracts.

---

## 4. Session preflight

Run:

```powershell
.\deploy\verify_rider_cockpit.ps1
```

Before write-capable agent work, additionally verify:

```powershell
git status --porcelain
git branch --show-current
git rev-parse HEAD
Get-Process UnrealEditor -ErrorAction SilentlyContinue
```

The cockpit must know the exact branch/head it owns.

### Branch lock

OpenCode/Ponytail may edit files and run commands, but it must **not autonomously switch branches, merge, rebase, pull, reset, clean, or commit** unless the task explicitly assigns that Git action.

Historical background agents have switched branches mid-integration. Treat that as a known failure class.

At session start, give the agent:

- repository;
- exact branch;
- starting HEAD;
- allowed write paths;
- forbidden write paths;
- whether commit/push is authorized;
- editor lock state.

If branch or HEAD changes unexpectedly, stop mutation and reconcile.

---

## 5. Canonical native loop

For a normal native change:

```text
1. Rider Find Usages / Code Vision / Blueprint usage discovery
2. identify existing owner seam
3. Ponytail audit/review mode if the seam is unfamiliar or risky
4. Jev decision only if multiple legal strategies remain genuinely ambiguous
5. implement the smallest change
6. Rider/UHT inspections clean
7. Qodana on the owned native/shader scope
8. closed-editor UBT if reflection/module topology requires it
9. RiderLink focused automation session
10. Monolith / PIE runtime proof
11. restart/package proof when the acceptance gate requires it
12. Ponytail review
13. PR / evidence
```

Never skip directly from agent-generated source to PIE.

---

## 6. Rider as architectural query surface

Before declaring a native API unused or adding another one, use Rider's Unreal-aware intelligence.

Check:

- native Find Usages;
- derived `UCLASS` relationships;
- Blueprint implementations / overrides;
- `UFUNCTION` usages;
- `UPROPERTY` usages and Blueprint-authored overrides;
- delegate bindings;
- gameplay-tag usage;
- module/include ownership.

This is especially important in Melodia because plain text search can miss Blueprint/content references and duplicate short asset names have historically existed.

A "no grep result" is not evidence that reflected API is dead.

---

## 7. UHT inspection rung

For reflected declarations, treat UnrealHeaderTool-aware inspection as a first-class inner-loop gate.

Applies especially to:

- `UCLASS`;
- `USTRUCT`;
- `UENUM`;
- `UFUNCTION`;
- `UPROPERTY`;
- Blueprint callable/native/implementable events;
- reflected container/property changes.

Required order:

```text
edit
-> Rider/UHT inspection clean
-> Qodana
-> full UBT when required
-> focused automation
-> runtime
```

A Live Coding patch is never the acceptance proof for reflected topology.

---

## 8. Qodana

Authority:

`qodana.yaml`

Current project profile:

- `ide: QDJB`;
- `qodana.recommended`;
- explicit Unreal/C++ inspections;
- generated/content/vendor/plugin exclusions;
- repository failure thresholds.

Use Qodana routinely for project-owned native/shader changes.

Do not create a different per-agent analyzer profile because an agent prefers another linter.

Qodana answers static-quality questions. It does not answer whether gameplay ran.

---

## 9. RiderLink test sessions

The repo already contains a large native Unreal automation surface.

Create/reuse focused Rider test sessions rather than running an undifferentiated universe of tests.

Recommended conceptual sessions:

### Melodia Integration
```text
Melodia.Integration.*
```

### Rhythm / music
```text
Melodia.Rhythm*
Melodia.MusicClock.*
```

### Wardrobe / traversal
```text
Melodia.Wardrobe*
Melodia.Magical*
```

### Gameplay core
```text
Melodia.Progression.*
Melodia.Quest.*
Melodia.NPC.*
Melodia.CoreRules.*
Melodia.Economy.*
```

### Persistence
Use the exact current `Melodia.*` persistence/restore tests discovered by Rider from source.

RiderLink is preferred when one running editor is the intended context. Use a headless/isolated process when process isolation itself is part of the acceptance gate.

---

## 10. OpenCode inside Rider

The tracked project config is:

`.opencode/opencode.jsonc`

It owns project-level OpenCode behavior for this lane.

The current configuration includes:

- Ponytail plugin path;
- a primary coding model through Bedrock Mantle;
- optional local Ollama models;
- Monolith;
- Blender MCP;
- filesystem/Git tooling;
- build vs plan agent modes.

### Important configuration rule

The tracked config may describe workstation-local executables and endpoints. A fresh clone must validate availability instead of assuming every absolute path exists.

Use `deploy/verify_rider_cockpit.ps1`.

Do not duplicate OpenCode config into another tracked Rider-specific copy unless a concrete compatibility requirement exists.

---

## 11. Monolith boundary

OpenCode can see Monolith through MCP, but the normal single-writer rule still applies.

Correct:

```text
OpenCode/Ponytail reasons
-> Monolith performs bounded editor action
-> Monolith reads back
-> test/runtime evidence records result
```

Incorrect:

- start another Unreal MCP graph writer;
- launch a second Unreal Editor;
- use arbitrary Python world references across repeated PIE calls;
- treat agent confidence as asset state;
- mutate a Blueprint from two agent surfaces simultaneously.

---

## 12. Jev + Ponytail

These solve different problems.

### Ponytail
UE implementation/review discipline:
- prefer existing engine/project patterns;
- avoid needless frameworks;
- respect BP/C++ boundaries;
- inspect before changing;
- review UE-specific code quality.

### Jev
bounded judgment:
- choose between legal implementation strategies;
- choose next verification step;
- select authored candidate;
- arbitrate cost/risk tradeoffs;
- direct specialist workers.

Useful pattern:

```text
Rider/Ponytail establishes the technically legal options
-> Jev chooses among those options when the decision is subjective/strategic
-> OpenCode/Rider implements
-> deterministic gates prove it
```

Do not ask Jev whether the build compiled or Qodana passed.

---

## 13. Agent model choice

Model choice is subordinate to workflow authority.

The tracked OpenCode config currently exposes Bedrock Mantle and local Ollama options. Use `Tools/model_router.py` and current project policy when choosing a model.

A stronger model does not gain permission to:

- change branches unexpectedly;
- create a second architecture owner;
- bypass Qodana/build/tests;
- mutate Unreal outside the one-writer contract;
- promote a claim beyond its evidence rung.

---

## 14. Shader lane

For tracked `.usf/.ush` work, use:

`.claude/skills/melodia-shader-rider/SKILL.md`

Canonical flow:

```text
Rider shader authoring
-> Rider/Ponytail review
-> Qodana for touched C++ consumer surface
-> closed-editor build when module registration changed
-> UE shader compile
-> material/Niagara consumer proof
-> visible runtime evidence
```

Do not hand-edit compiled content assets.

---

## 15. Performance/debug lane

Use Rider's native debugger for code-state questions and Unreal Insights for runtime performance.

Recommended sequence:

```text
reproduce
-> debugger / breakpoint / data inspection
-> instrument existing owner when needed
-> TRACE_CPUPROFILER_EVENT_SCOPE
-> Unreal Insights
-> smallest fix
-> Qodana/build/test
-> reproduce again
```

Do not redesign architecture from a guessed hotspot.

---

## 16. Git / multi-agent coexistence

The Rider cockpit is a powerful write-capable lane. It must coexist safely with jcode, cloud agents, phone agents and other workers.

Rules:

1. one branch owner for overlapping paths;
2. no autonomous branch switching;
3. no agent commits unless explicitly authorized;
4. no concurrent editing of the same `.cpp/.h` with a jcode worker;
5. editor mutation remains serial even if source editing parallelizes;
6. before any merge, re-check branch, HEAD, diff and CI;
7. use fresh-main recuts rather than merging ancient agent branches wholesale.

---

## 17. What this lane should replace

Use this cockpit instead of:

- ad-hoc "ask an agent to edit C++" sessions with no UE context;
- custom one-off test RPCs when RiderLink can run the native test;
- bespoke lint profiles instead of Qodana;
- generic code-agent UE rules when Ponytail is available;
- grep-only reflection archaeology;
- background Git agents with implicit branch authority;
- multiple editor mutation surfaces.

It does **not** replace:

- World Compiler for authored procedural worlds;
- Hython for deterministic DCC forging;
- guarded Rokoko import for performance capture;
- Monolith for editor mutation;
- Jev for bounded judgment;
- Unreal runtime/package evidence.

---

## 18. Acceptance for a cockpit-driven native PR

Report:

- branch + starting and ending HEAD;
- owner seam changed;
- Rider reflected/Blueprint usage discovery performed;
- Ponytail mode/command used when applicable;
- UHT inspection result for reflected changes;
- Qodana result;
- UBT target/result;
- RiderLink test session/tests run;
- PIE/runtime proof;
- restart/package proof if required;
- Ponytail review findings addressed or explicitly parked;
- known remaining limitation.

The intended culture is:

**Rider understands it -> Ponytail keeps it UE-sane -> Jev resolves bounded judgment -> Qodana inspects it -> UBT compiles it -> RiderLink tests it -> Monolith/UE proves it.**
