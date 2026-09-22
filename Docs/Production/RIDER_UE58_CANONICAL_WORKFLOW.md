# JetBrains Rider + Unreal Engine 5.8 — Canonical Workflow

**Purpose:** production runbook for UE C++ work in Melodia.  
**Status authority:** `CURRENT_STATE.md`.  
**Runtime authority:** Unreal Editor / packaged build, not the IDE.
**Canonical agent cockpit:** [`RIDER_PONYTAIL_ENGINEERING_COCKPIT.md`](RIDER_PONYTAIL_ENGINEERING_COCKPIT.md).

Rider is the preferred C++ navigation, inspection and debugger surface. **RiderLink and Qodana are canonical always-available companions:** RiderLink is the focused live-editor automation bridge; Qodana is the tracked static-analysis quality gate. Use the trio routinely to reduce uncertainty before touching or promoting engine state.

---

## 1. Discovery before editing

Before adding a class, function, tag, subsystem or module:

1. Search the repository for the existing owner.
2. Use Rider Find Usages on the relevant `UCLASS`, `UFUNCTION`, `UPROPERTY`, gameplay tag and enum.
3. Inspect Blueprint/reflection usages exposed by Rider's Unreal integration.
4. Identify whether the requested behavior is content/data, editor automation, or native runtime logic.
5. Change the existing owner when one exists.

A missing text match is not proof that a Blueprint-facing API is unused. Prefer Unreal-aware usage discovery over grep alone for reflected symbols.

---

## 1.5 UHT-aware inspection

For reflected UE declarations, Rider's UnrealHeaderTool-aware analysis is part of the canonical inner loop.

Use it before the build rung for:

- `UCLASS` / `USTRUCT` / `UENUM` declarations;
- `UFUNCTION` / `UPROPERTY` changes;
- Blueprint-native / implementable events;
- reflected containers and metadata;
- generated-header-sensitive changes.

Required shape:

```text
edit -> Rider/UHT inspection clean -> Qodana -> UBT when required -> RiderLink -> runtime
```

Do not wait for a full build to discover a reflection error Rider can already surface.

---

## 1.6 Blueprint-aware architectural discovery

Treat Rider's Unreal-aware usage index as an architectural query surface, not just navigation.

Before adding, renaming, moving or deleting reflected API, inspect:

- derived Blueprint classes;
- Blueprint implementations/overrides;
- usages of `UFUNCTION` / `UPROPERTY`;
- Blueprint-authored property overrides;
- delegate bindings;
- gameplay-tag usages;
- module and include ownership.

This matters in Melodia because text search cannot prove absence from Blueprint assets and duplicate short asset names have existed. A grep miss is not dead-code evidence.
---

## 2. Build mode decision

### Live Coding is acceptable only for compatible body-level iteration

Use it for a narrow function-body change when no reflected/module topology changes and when the current editor state is disposable.

### Close Unreal and run a full Development Editor build when changing

- `UCLASS`, `USTRUCT`, `UENUM`, `UFUNCTION`, `UPROPERTY` declarations;
- generated-header dependencies;
- module or plugin topology;
- `.Build.cs` dependencies;
- shader directory registration;
- startup/load phase;
- new native files/classes that UHT/UBT must discover;
- anything that produced suspicious stale-type behavior after Live Coding.

Canonical target:

```text
BS_GodFileEditor Win64 Development
```

Do not call a reflected/module change green because Live Coding accepted it.

---

## 3. RiderLink — canonical focused live-editor test bridge

RiderLink is assumed available as part of the normal Melodia engineering workflow.

For native tests such as `IMPLEMENT_SIMPLE_AUTOMATION_TEST`:

- prefer the smallest relevant test group;
- use RiderLink against the single intended editor session whenever live-editor context is appropriate;
- launch the existing test from Rider rather than inventing another RPC/test harness;
- record the exact test path and result;
- use commandlet/headless execution only when a clean isolated process is itself part of the acceptance condition.

Examples of useful focused families include Melodia integration, Wardrobe, runtime persistence and chapter-specific tests. Use the current test names from source rather than copying stale commands from old reports.

Rider test success proves the native test. It does not replace a process-restart, PIE-input or packaged proof when those are the acceptance criteria.

---

## 3.1 Persistent Rider test sessions

The repository has enough native automation that focused Rider sessions should be reused by subsystem rather than reconstructed ad hoc.

Recommended session families:

- **Integration:** `Melodia.Integration.*`;
- **Rhythm / music:** current `Melodia.Rhythm*` and `Melodia.MusicClock.*` tests;
- **Wardrobe / traversal:** current Wardrobe and Magical Transform test families;
- **Gameplay core:** progression, quest, NPC, economy and core-rule families;
- **Persistence:** current save/restore/idempotency families discovered from source.

Use Rider's test discovery as the current name authority. Do not copy stale test names from old handoffs.

RiderLink is appropriate when the running editor is intentionally part of the test context. Use isolated commandlet/process execution when process isolation is itself the acceptance condition.
---

## 3.2 Ponytail/OpenCode agent discipline

When delegating native implementation/review from inside Rider, use the canonical cockpit rather than a context-free coding agent:

`Rider -> OpenCode -> Ponytail UE5.8 -> Qodana/UBT/RiderLink -> UE proof`.

Preflight:

```powershell
.\deploy\verify_rider_cockpit.ps1
```

Ponytail is machine-local at `Tools/vendor/ponytail-ue58`; the tracked OpenCode config references its plugin. A fresh clone can explicitly rehydrate it with `-InstallPonytail`.

Git safety is mandatory: the cockpit owns the assigned branch/head only. No autonomous switch, merge, rebase, reset, clean or commit unless the task explicitly authorizes it.
---

## 4. Native debugger workflow

Use Rider's debugger for defects that are expensive to infer from logs.

Good breakpoint sites:

- canonical narrative commit/restore boundaries;
- travel/allowlist dispatch;
- JRPG action selection/result seams;
- Wardrobe ownership/equip transitions;
- PhraseBus ingest/dispatch;
- World Compiler native/editor consumer boundaries when native code is involved.

Use conditional breakpoints and data inspection rather than adding permanent debug state.

Detach cleanly when possible; do not terminate the only healthy editor unless the test requires process death.

---

## 5. Reflection, Blueprint and content reachability

Rider's Unreal integration is especially useful for answering:

- Which Blueprints derive from this class?
- Which assets reference this property/function?
- Is this reflected API exposed or overridden?
- Which module owns the symbol?
- Is an include/dependency actually needed?

Still verify runtime reachability through the project's dedicated reachability tools and live tests where relevant. A reflected reference can be dead content.

---

## 6. IWYU and include hygiene

Use Rider's Unreal-aware inspections to remove unnecessary includes and identify forward-declaration opportunities.

Rules:

- do not perform broad mechanical include churn in the same PR as a runtime fix;
- do not "fix" generated/vendor/plugin source outside the named scope;
- after include changes, run the same build configuration that ships the edited module.

Unity builds can hide missing includes. Treat successful non-representative editor hot reload as insufficient proof.

---

## 7. UObject pointer modernization

Prefer UE5-safe pointer patterns where the existing module/style requires them, including `TObjectPtr<T>` for reflected UObject member storage.

Do not perform repo-wide pointer modernization opportunistically. Apply it only inside the touched owner or a dedicated cleanup PR with build/test proof.

Rider quick-fixes can accelerate the edit; project semantics still decide whether the migration is correct.

---

## 8. Shader work

Rider is the preferred text editor for tracked `.usf` / `.ush` source.

Current project shader source is owned by the tracked native module, including `Source/MelodiaShader/Shaders/`.

For shader/module work:

1. inspect the existing virtual shader path registration;
2. edit the tracked shader source;
3. run a closed-editor build if module/load registration changed;
4. launch Unreal and allow the real shader compiler to validate;
5. capture the visible material/render result.

IDE syntax success is not shader-runtime proof.

---

## 9. Profiling and traces

For native hotspots, add or use existing:

`TRACE_CPUPROFILER_EVENT_SCOPE(Name)`

Then inspect the real execution in Unreal Insights.

Profile actual gameplay/editor behavior before redesigning architecture for performance.

Do not optimize a guessed bottleneck based only on static inspection.

---

## 10. Qodana — canonical static-analysis gate

Qodana is an always-available canonical quality layer for Melodia native/shader work.

The repository already tracks the authority at `qodana.yaml`:

- `ide: QDJB`;
- profile `qodana.recommended`;
- explicit C++ inspection set;
- generated/content/vendor/plugin exclusions;
- failure thresholds of critical 0 / high 5 / any 30.

Use that tracked configuration rather than inventing a per-agent lint profile. Run Qodana as a normal pre-review gate for changes in the owned native/shader surface, then investigate findings in Rider.

Qodana is static-analysis evidence, not runtime certification. A clean Qodana run does not replace UBT, RiderLink/focused tests, PIE, restart or packaged proof.

---

## 11. Rider + Jev

Jev is the canonical decision/orchestration companion when native work presents a real bounded judgment call: implementation strategy, test ordering, risk/cost tradeoff, or next verification action.

Correct shape:

```text
Rider discovers the real owner and constraints
  -> Jev selects among bounded legal strategies when judgment is needed
  -> Rider implements the selected strategy
  -> Qodana + UBT + RiderLink/focused tests
  -> Unreal runtime evidence
```

Jev never substitutes for compiler/test results and does not mutate the editor directly. See `Docs/Production/JEV_CANONICAL_WORKFLOW.md`.

---

## 12. Rider + World Compiler

Rider should help agents understand the C++/editor boundaries around World Compiler, not tempt them to rewrite it natively.

The compiler remains:

`Tools/world_compiler.py`

The UE application lane remains:

`Tools/world_compiler_ue_driver.py` + `Content/Python/world_compiler_ue.py`

Use Rider when the task actually reaches native types such as a bookmark/data asset, integration subsystem, row-struct contract or engine-facing C++ seam.

A biome or setpiece is normally recipe/data/content work, not a C++ task.

---

## 13. Rider + Rokoko

Rokoko animation ingestion is not a Rider-owned pipeline.

Rider is useful only if the animation task exposes a native binding/runtime defect. The production import path is the guarded Unreal Python importer:

`Content/Python/import_rokoko_mocap_batch.py`

Do not replace it with native import code because Rider makes C++ convenient.

---

## 14. Before opening a PR

For native work, report:

- existing owner modified;
- cockpit preflight branch/head recorded for agent-driven native work;
- Ponytail review/audit used when applicable;
- Rider/UHT inspection clean for reflected changes;
- Rider/usage discovery performed;
- whether reflected/module declarations changed;
- exact build target and result;
- focused tests run;
- live PIE/runtime evidence if required;
- process-restart evidence if required;
- packaged evidence if required;
- known remaining limitation.

The strongest Rider workflow is not "write C++ faster." It is:

**find the real owner faster -> make a smaller change -> run the right build -> prove it in Unreal.**
