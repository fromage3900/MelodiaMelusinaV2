// Copyright tumourlove. All Rights Reserved.
// UITypeRegistry.h
//
// Catalog of every UMG widget UClass surfaced to the spec/builder pipeline,
// keyed by short token name (e.g. "VerticalBox", "TextBlock", "EffectSurface").
// Populated by `UMonolithUIRegistrySubsystem` via a TObjectIterator walk; not
// hand-maintained.
//
// Naming rule (clean-room): the public-facing token is the UClass display name
// with the leading `U` stripped (e.g. `UVerticalBox` -> `"VerticalBox"`). Where
// a class has a `DisplayName` meta tag we honour it; otherwise we strip the
// engine prefix. Unknown class? Caller falls back to `CustomClassPath` on the
// FUISpecNode.
//
// Container kind drives builder layout decisions: a "Panel" can host many
// children, a "Content" wrapper exactly one, a "Leaf" zero. We derive this
// from `IsChildOf(UContentWidget)` (one-child) -> `IsChildOf(UPanelWidget)`
// (many-child if `CanHaveMultipleChildren()`) -> else leaf.
//
// Curated property mappings live alongside the registry entries — each entry
// owns an array of `(JsonPath, EngineProperty)` pairs that the
// `FUIPropertyAllowlist` projects into a per-type `TSet<FString>`. The
// allowlist is generated, NOT a parallel storage — the registry is the source
// of truth.
//
// Thread safety: read-only after `UMonolithUIRegistrySubsystem::Initialize`.
// All mutation goes through `RegisterType`/`Reset` which the subsystem only
// calls during init, OnPostEngineInit re-scans, and reload events. Concurrent
// readers during a re-scan will see a momentarily inconsistent view; if that
// becomes a real issue, gate via the subsystem's RegistryLock (not added yet
// because nothing currently reads from a non-game thread).

#pragma once

#include "CoreMinimal.h"
#include "Templates/SubclassOf.h"
#include "UObject/WeakObjectPtr.h"

class UClass;
class UWidget;

/**
 * Container kind classification for a widget UClass. Drives the builder's
 * placement logic when constructing a node's parent slot.
 */
enum class EUIContainerKind : uint8
{
    /** Leaf widget — no children allowed (e.g. UTextBlock, UImage). */
    Leaf,
    /** Single-child wrapper (e.g. UBorder, USizeBox, UScaleBox). */
    Content,
    /** Multi-child panel (e.g. UVerticalBox, UCanvasPanel). */
    Panel,
};

/**
 * One curated property mapping. The `JsonPath` is the spec-side dotted token
 * (e.g. "Slot.Padding", "CornerRadii", "Background.Color") and `EnginePath`
 * is the engine-side reflection-friendly path that the Phase C reflection
 * helper resolves against the live UWidget.
 *
 * For widgets where the JSON token is identical to the engine property name
 * the two strings match — keeping them as separate fields (rather than a
 * single string) preserves the option to diverge per-type without churn.
 */
struct MONOLITHUI_API FUIPropertyMapping
{
    /** Spec-side dotted token surfaced to LLMs / authoring tools. */
    FString JsonPath;

    /** Engine-side reflection path resolved by the property setter. */
    FString EnginePath;

    /** Human-readable description for diagnostics output. */
    FString Description;

    FUIPropertyMapping() = default;
    FUIPropertyMapping(const FString& InJsonPath, const FString& InEnginePath, const FString& InDescription = FString())
        : JsonPath(InJsonPath)
        , EnginePath(InEnginePath)
        , Description(InDescription)
    {
    }
};

/**
 * Registry entry for a single widget UClass. Owned by `FUITypeRegistry::Types`
 * — pointer lifetime is the lifetime of the registry itself.
 *
 * `WidgetClass` uses `TWeakObjectPtr` so that hot-reload / class-replacement
 * leaves a null pointer rather than a dangling raw `UClass*`. Subsystem
 * re-scan logic checks for null and refreshes the entry against the new
 * `UClass` of the same name.
 */
struct MONOLITHUI_API FUITypeRegistryEntry
{
    /** Public-facing token (e.g. "VerticalBox"). Case-sensitive in the lookup map. */
    FName Token;

    /** UClass of the widget. Weak so hot-reload can null this and the subsystem refreshes. */
    TWeakObjectPtr<UClass> WidgetClass;

    /** Container classification. */
    EUIContainerKind ContainerKind = EUIContainerKind::Leaf;

    /**
     * Maximum allowed children for this type. -1 means unbounded (panel),
     * 1 means single-child (content), 0 means leaf. The validator uses this
     * to refuse spec trees that overflow a content widget.
     */
    int32 MaxChildren = 0;

    /** Slot UClass produced by `UPanelWidget::GetSlotClass()` on the CDO. nullptr for leaves. */
    TWeakObjectPtr<UClass> SlotClass;

    /**
     * Curated property mappings. Order matters only for diagnostic output —
     * the allowlist projection is set-based and order-insensitive.
     */
    TArray<FUIPropertyMapping> PropertyMappings;
};

/**
 * Catalogue of registered widget types. Owned by `UMonolithUIRegistrySubsystem`.
 *
 * The registry is the source of truth for both type discovery and the
 * property allowlist — see `FUIPropertyAllowlist::IsAllowed` which projects
 * over `Types[X].PropertyMappings`.
 */
class MONOLITHUI_API FUITypeRegistry
{
public:
    /** Wipe the registry. Subsystem calls this at the start of any scan pass. */
    void Reset();

    /**
     * Register a single type. Replaces any existing entry with the same token.
     * Used by both the auto-walk and any manual override path.
     */
    void RegisterType(FUITypeRegistryEntry&& Entry);

    /** Lookup by token. Returns nullptr if not registered. */
    const FUITypeRegistryEntry* FindByToken(const FName& Token) const;

    /** Lookup by UClass. O(N) — registry sizes are small (~50 types) so this is fine. */
    const FUITypeRegistryEntry* FindByClass(const UClass* WidgetClass) const;

    /** Number of registered types. */
    int32 Num() const { return Types.Num(); }

    /** Read-only view of every registered entry. */
    const TArray<FUITypeRegistryEntry>& GetAll() const { return Types; }

    /**
     * Refresh weak-pointer-stale entries by re-resolving the UClass via
     * `FindFirstObject<UClass>(Token)`. Called from the reload-complete path
     * to repair entries whose `WidgetClass` went null after a hot-reload.
     * Returns the number of entries refreshed.
     */
    int32 RefreshStaleEntries();

private:
    TArray<FUITypeRegistryEntry> Types;
    TMap<FName, int32> TokenIndex;
};
