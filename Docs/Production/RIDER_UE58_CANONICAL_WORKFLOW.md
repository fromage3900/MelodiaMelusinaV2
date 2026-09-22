# JetBrains Rider + Unreal Engine 5.8 — Canonical Workflow

**Purpose:** production runbook for UE C++ work in Melodia.  
**Status authority:** `CURRENT_STATE.md`.  
**Runtime authority:** Unreal Editor / packaged build, not the IDE.

Rider is the preferred C++ navigation, inspection, debugger and focused-test surface. Use it to reduce uncertainty before touching engine state.

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

## 3. Focused automation from Rider

For native tests such as `IMPLEMENT_SIMPLE_AUTOMATION_TEST`:

- prefer the smallest relevant test group;
- use Rider/RiderLink against the single intended editor session when appropriate;
- record the exact test path and result;
- use commandlet/headless execution when a clean isolated process is the acceptance condition.

Examples of useful focused families include Melodia integration, Wardrobe, runtime persistence and chapter-specific tests. Use the current test names from source rather than copying stale commands from old reports.

Rider test success proves the native test. It does not replace a process-restart, PIE-input or packaged proof when those are the acceptance criteria.

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

## 10. Qodana/static analysis

Static analysis is a review layer, not runtime certification.

Use the repository's tracked configuration and exclude generated/vendor code. Because prior research documented uncertainty between local JetBrains profiles/modes, validate the actual installed invocation before canonizing a command.

Do not block an urgent proven runtime fix on speculative IDE tooling configuration. Do not publish a "clean" claim from a scan that silently excluded the edited module.

---

## 11. Rider + World Compiler

Rider should help agents understand the C++/editor boundaries around World Compiler, not tempt them to rewrite it natively.

The compiler remains:

`Tools/world_compiler.py`

The UE application lane remains:

`Tools/world_compiler_ue_driver.py` + `Content/Python/world_compiler_ue.py`

Use Rider when the task actually reaches native types such as a bookmark/data asset, integration subsystem, row-struct contract or engine-facing C++ seam.

A biome or setpiece is normally recipe/data/content work, not a C++ task.

---

## 12. Rider + Rokoko

Rokoko animation ingestion is not a Rider-owned pipeline.

Rider is useful only if the animation task exposes a native binding/runtime defect. The production import path is the guarded Unreal Python importer:

`Content/Python/import_rokoko_mocap_batch.py`

Do not replace it with native import code because Rider makes C++ convenient.

---

## 13. Before opening a PR

For native work, report:

- existing owner modified;
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
