# IModularFeatures Bridge Pattern

**Plugin:** Monolith | **Engine:** UE 5.7 | **Validated:** MonolithBABridge (2026-03-27)

---

## Purpose

When a **core** Monolith module (e.g., `MonolithBlueprint`) needs to optionally call into a
third-party C++ API, it cannot take a compile-time dependency on that API — users who don't
have the third party plugin installed would fail to build.

The IModularFeatures bridge solves this:

- The abstract interface lives in `MonolithCore` (always compiled in)
- The implementation lives in a bridge module that **does** depend on the third party
- The core module calls `IsAvailable()` at runtime before touching the interface

Zero compile-time coupling. The bridge module is absent if the third party isn't installed.

---

## When to Use This vs FMonolithToolRegistry

These are complementary patterns. Choose based on who the caller is.

| Scenario | Pattern |
|----------|---------|
| AI agent calls optional MCP actions (`gba_query`, `combograph_query`) | `FMonolithToolRegistry` — see `OPTIONAL_MODULE_ARCHITECTURE.md` |
| Core C++ calls optional C++ API at action time | **IModularFeatures bridge (this doc)** |
| Both — optional module owns MCP actions AND core needs its C++ API | Both patterns simultaneously |

**Rule of thumb:** If the consumer is a JSON MCP action dispatching to another namespace, use
the registry. If the consumer is C++ inside a core module calling a typed API, use
IModularFeatures.

---

## Existing Implementation: IMonolithGraphFormatter

The only current bridge. Enables `MonolithBlueprint`'s `auto_layout` action to delegate to
Blueprint Assist's formatter when BA is installed.

### Files

| Role | File |
|------|------|
| Abstract interface | `Source/MonolithCore/Public/IMonolithGraphFormatter.h` |
| Bridge module | `Source/MonolithBABridge/Private/MonolithBABridgeModule.cpp` |
| Implementation | `Source/MonolithBABridge/Private/MonolithBAFormatterImpl.h/.cpp` |
| Consumer | `Source/MonolithBlueprint/Private/MonolithBlueprintLayoutActions.cpp` |

### Interface (MonolithCore)

```cpp
// IMonolithGraphFormatter.h — in MonolithCore, no BA dependency
class IMonolithGraphFormatter : public IModularFeature
{
public:
    static FName GetModularFeatureName()
    {
        static const FName Name(TEXT("MonolithGraphFormatter"));
        return Name;
    }

    virtual bool SupportsGraph(UEdGraph* Graph) const = 0;
    virtual bool FormatGraph(UEdGraph* Graph, int32& OutNodesFormatted, FString& OutErrorMessage) = 0;
    virtual FMonolithFormatterInfo GetFormatterInfo(UEdGraph* Graph) const = 0;

    static bool IsAvailable()
    {
        return IModularFeatures::Get().IsModularFeatureAvailable(GetModularFeatureName());
    }

    static IMonolithGraphFormatter& Get()
    {
        return IModularFeatures::Get().GetModularFeature<IMonolithGraphFormatter>(
            GetModularFeatureName());
    }
};
```

### Bridge Module Registration

```cpp
// MonolithBABridgeModule.cpp — depends on BlueprintAssist, NOT in MonolithCore
void FMonolithBABridgeModule::StartupModule()
{
    if (!GetDefault<UMonolithSettings>()->bEnableBlueprintAssist) return;

#if WITH_BLUEPRINT_ASSIST
    Formatter = MakeUnique<FMonolithBAFormatterImpl>();
    IModularFeatures::Get().RegisterModularFeature(
        IMonolithGraphFormatter::GetModularFeatureName(),
        Formatter.Get());
#endif
}

void FMonolithBABridgeModule::ShutdownModule()
{
#if WITH_BLUEPRINT_ASSIST
    if (Formatter.IsValid())
    {
        IModularFeatures::Get().UnregisterModularFeature(
            IMonolithGraphFormatter::GetModularFeatureName(),
            Formatter.Get());
        Formatter.Reset();
    }
#endif
}
```

The bridge module also uses `#if WITH_BLUEPRINT_ASSIST` (set by its `Build.cs` via
`Directory.Exists()`) so it compiles even when BA is absent — it just registers nothing.

### Consumer Pattern

```cpp
// MonolithBlueprintLayoutActions.cpp — zero BA dependency
bool bBAAvailable = IMonolithGraphFormatter::IsAvailable()
    && IMonolithGraphFormatter::Get().SupportsGraph(Graph);

if (bBAAvailable)
{
    int32 NodesFormatted = 0;
    FString ErrorMessage;
    if (IMonolithGraphFormatter::Get().FormatGraph(Graph, NodesFormatted, ErrorMessage))
    {
        // success path
    }
}
```

Always call `IsAvailable()` before `Get()`. `Get()` asserts if nothing is registered.

---

## How to Add a New Bridge Interface

Use this checklist when a core module needs to call into a new optional third-party API.

### 1. Define the interface in MonolithCore

Create `Source/MonolithCore/Public/IMonolithYourFeature.h`:

```cpp
#pragma once
#include "CoreMinimal.h"
#include "Features/IModularFeature.h"
#include "Features/IModularFeatures.h"

class IMonolithYourFeature : public IModularFeature
{
public:
    static FName GetModularFeatureName()
    {
        static const FName Name(TEXT("MonolithYourFeature"));
        return Name;
    }

    // Your virtual methods here
    virtual void DoThing() = 0;

    static bool IsAvailable()
    {
        return IModularFeatures::Get().IsModularFeatureAvailable(GetModularFeatureName());
    }

    static IMonolithYourFeature& Get()
    {
        return IModularFeatures::Get().GetModularFeature<IMonolithYourFeature>(
            GetModularFeatureName());
    }
};
```

No third-party headers. Only engine types. This header is safe to include anywhere.

### 2. Create the bridge module

Add `Source/MonolithYourBridge/` with:

- `MonolithYourBridge.Build.cs` — depends on `MonolithCore` + optional third party
  (use `Directory.Exists()` pattern from `OPTIONAL_MODULE_ARCHITECTURE.md` section 3.1)
- `MonolithYourBridgeModule.cpp` — registers/unregisters the implementation
- `MonolithYourFeatureImpl.h/.cpp` — concrete implementation behind `#if WITH_YOUR_PLUGIN`

Add the module to `Monolith.uplugin`:
```json
{
    "Name": "MonolithYourBridge",
    "Type": "Editor",
    "LoadingPhase": "Default"
}
```

> Use `Default` loading phase, not `PostEngineInit`. MonolithCore starts its HTTP server at
> `PostEngineInit`. Bridge modules must be registered before that. See
> `OPTIONAL_MODULE_ARCHITECTURE.md` section 12.2.

### 3. Implement the interface

```cpp
// MonolithYourFeatureImpl.h
#if WITH_YOUR_PLUGIN
#include "SomeThirdPartyHeader.h"

class FMonolithYourFeatureImpl : public IMonolithYourFeature
{
public:
    virtual void DoThing() override { /* call third party API */ }
};
#endif
```

### 4. Call from the consumer

```cpp
#include "IMonolithYourFeature.h"

if (IMonolithYourFeature::IsAvailable())
{
    IMonolithYourFeature::Get().DoThing();
}
```

The consumer (`MonolithBlueprint`, `MonolithMesh`, etc.) includes only
`IMonolithYourFeature.h` — no bridge or third-party headers.

### 5. Add a settings toggle

Add `bEnableYourPlugin` to `UMonolithSettings` in `MonolithSettings.h`. Check it in
`StartupModule()` before registering (see bridge module pattern above). This lets users
disable the integration without uninstalling the plugin.

---

## Module Graph

```
MonolithCore
  └── IMonolithGraphFormatter.h   (interface, no deps)

MonolithBABridge
  ├── depends on: MonolithCore, BlueprintAssist (optional via Build.cs)
  └── registers: FMonolithBAFormatterImpl → IMonolithGraphFormatter feature slot

MonolithBlueprint
  ├── depends on: MonolithCore only
  └── calls: IMonolithGraphFormatter::IsAvailable() / Get()
```

The bridge module is the only node that knows about both sides. Core modules stay clean.

---

## Key Constraints

- **Never** include third-party headers in the interface file (`IMonolithYourFeature.h`)
- **Always** check `IsAvailable()` before `Get()` — `Get()` will assert on failure
- **Always** unregister in `ShutdownModule()` — leaked registrations cause stale pointers
- **Use `TUniquePtr`** for the implementation instance in the bridge module (see bridge pattern above)
- The feature name string (`TEXT("MonolithGraphFormatter")`) must match exactly between
  `GetModularFeatureName()`, `RegisterModularFeature()`, and `UnregisterModularFeature()`
