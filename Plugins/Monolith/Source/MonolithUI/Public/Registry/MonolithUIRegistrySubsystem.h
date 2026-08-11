// Copyright tumourlove. All Rights Reserved.
// MonolithUIRegistrySubsystem.h
//
// UEditorSubsystem owning the live `FUITypeRegistry` and `FUIPropertyAllowlist`.
// Single source of truth for "which UMG widgets are exposed to the spec/builder
// pipeline, and what property paths are safe to write on each".
//
// Why an EDITOR subsystem (not a runtime one): the spec/builder pipeline is
// editor-only — `build_ui_from_spec` mutates `UWidgetBlueprint` assets which
// only exist with `WITH_EDITOR=1`. Cooked builds never hit this code path, so
// gating the entire subsystem to the editor keeps shipping binaries lean.
//
// Population timing — three-stage:
//   1) `Initialize`: walks `TObjectIterator<UClass>` for everything currently
//      loaded. Catches stock UMG and any plugin loaded before the editor
//      subsystem framework comes up.
//   2) `FCoreDelegates::OnPostEngineInit`: re-walks AFTER all post-init plugin
//      modules have loaded. Catches the late-loading marketplace case
//      (CommonUI, third-party UMG widget packs).
//      NOTE: The OnPostEngineInit listener is registered from
//      `FMonolithUIModule::StartupModule` rather than from this subsystem's
//      `Initialize`, because editor subsystems initialise AFTER OnPostEngineInit
//      has already fired. Module startup runs earlier.
//   3) `FCoreUObjectDelegates::ReloadCompleteDelegate`: refreshes weak-pointer-
//      stale entries when a Live Coding / hot-reload cycle replaces UClass
//      pointers. Refresh is non-destructive — re-resolves the same token to the
//      new UClass via `FindFirstObject<UClass>(Token)`.
//
// Curated mappings come from `RegisterCuratedMappings` which seeds a hand-
// authored set of common widget-property bindings (VerticalBox slot padding,
// TextBlock text/font, Image brush, etc.). Plugin widgets discovered via the
// reflection walk get a default empty mapping list; explicit curated mappings
// for plugin widgets (e.g. URoundedBorder) are added inside the same function.

#pragma once

#include "CoreMinimal.h"
#include "EditorSubsystem.h"
#include "Registry/UITypeRegistry.h"
#include "Registry/UIPropertyAllowlist.h"
#include "Registry/UIPropertyPathCache.h"
#include "MonolithUIRegistrySubsystem.generated.h"

// UE 5.7: declared without underlying type at UObject/UObjectGlobals.h:3216 — match exactly.
enum class EReloadCompleteReason;

UCLASS()
class MONOLITHUI_API UMonolithUIRegistrySubsystem : public UEditorSubsystem
{
    GENERATED_BODY()

public:
    /** Subsystem entry point. Performs the initial reflection walk + curated mappings. */
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;

    /** Unbinds the reload-complete delegate. */
    virtual void Deinitialize() override;

    /**
     * Convenience accessor — null-safe pointer to the global instance.
     * Returns nullptr in a non-editor or pre-init context. Callers that want
     * a hard guarantee should use `GEditor->GetEditorSubsystem<...>()` directly
     * and handle the null themselves.
     */
    static UMonolithUIRegistrySubsystem* Get();

    /** Read-only access to the type registry. */
    const FUITypeRegistry& GetTypeRegistry() const { return TypeRegistry; }

    /** Read-only access to the property allowlist (built over the type registry). */
    const FUIPropertyAllowlist& GetAllowlist() const { return *Allowlist; }

    /**
     * Mutable access to the property path cache. Mutable because Get() bumps
     * LRU stamps and updates hit/miss counters — the cache itself is logically
     * read-mostly but physically write-on-read. Lifetime-tied to the subsystem.
     *
     * Returns nullptr only between Deinitialize and the next Initialize, which
     * shouldn't happen in any normal action call path. Callers may pass the
     * pointer directly to FUIReflectionHelper.
     */
    FUIPropertyPathCache* GetPathCache() { return PathCache.Get(); }
    const FUIPropertyPathCache* GetPathCache() const { return PathCache.Get(); }

    /**
     * Force a full re-scan of all loaded widget UClasses + curated mapping
     * re-seed. Called by `FMonolithUIModule::StartupModule` from the
     * `OnPostEngineInit` callback so late-loaded plugins are picked up.
     * Public so tests can drive a re-scan when injecting synthetic classes.
     */
    void RescanWidgetTypes();

    /**
     * Refresh weak-pointer-stale registry entries after a Live Coding /
     * hot-reload cycle. Re-binds each entry's `WidgetClass` to the freshly
     * loaded UClass of the same token name. Returns the count of refreshed
     * entries. Invalidates the allowlist cache.
     */
    int32 RefreshAfterReload();

private:
    /** Walk every loaded UClass derived from UWidget; populate `TypeRegistry`. */
    void PopulateFromReflectionWalk();

    /**
     * Seed curated property mappings on registry entries. Called after the
     * reflection walk so every entry exists before mappings attach. Adding
     * a mapping for a token whose entry is missing is a no-op (the widget's
     * UClass may not be loaded in a stripped build).
     */
    void RegisterCuratedMappings();

    /**
     * Convenience: derive container kind + max children from the widget's CDO.
     * Pure function — pulled out so test code can exercise the classification
     * rule without spinning up the subsystem.
     */
    static void ClassifyWidgetClass(
        UClass* WidgetClass,
        EUIContainerKind& OutKind,
        int32& OutMaxChildren,
        UClass*& OutSlotClass);

    /** ReloadCompleteDelegate handler — refreshes stale entries. */
    void OnReloadComplete(EReloadCompleteReason Reason);

    /** Live registry. */
    FUITypeRegistry TypeRegistry;

    /** Lazy projection — held by unique pointer because FUIPropertyAllowlist holds a const-ref. */
    TUniquePtr<FUIPropertyAllowlist> Allowlist;

    /**
     * Resolved-property-chain LRU cache. Owned at the subsystem level so it
     * survives across actions and across hot-reload cycles (entries that go
     * stale are detected and re-resolved on the next Get). Phase C addition.
     *
     * Held by TUniquePtr to mirror the Allowlist pattern (avoids forcing
     * full FUIPropertyPathCache definition into this header — only the
     * forward declaration in UIPropertyPathCache.h is needed at the header
     * boundary). Cap is the FUIPropertyPathCache default (256).
     */
    TUniquePtr<FUIPropertyPathCache> PathCache;

    /** Reload-complete delegate handle (registered in Initialize, removed in Deinitialize). */
    FDelegateHandle ReloadCompleteHandle;
};
