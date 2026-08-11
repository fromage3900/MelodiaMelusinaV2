// Copyright tumourlove. All Rights Reserved.
// UIPropertyAllowlist.h
//
// Per-type set of dotted property paths that the spec/builder pipeline is
// permitted to write through the safe reflection helper. NOT a parallel
// store — the allowlist is a projection over `FUITypeRegistry::PropertyMappings`,
// generated lazily on first lookup and rebuilt whenever the underlying
// registry mutates.
//
// Why a projection rather than a direct walk on every call: lookup is hot
// (every property write goes through it). Reading a `TSet<FString>` is O(1);
// re-walking the registry's `PropertyMappings` would be O(N) per call.
//
// The allowlist is the front gate of the Phase C `FUIReflectionHelper`. Any
// property path not in the allowlist for a given type is rejected with a
// `NotInAllowlist` reason — except when the caller passes `raw_mode=true`,
// which bypasses the gate. `raw_mode` is opt-in for the legacy
// `set_widget_property` path that pre-dates the allowlist.

#pragma once

#include "CoreMinimal.h"

class FUITypeRegistry;
struct FUITypeRegistryEntry;

/**
 * Per-type allowlist projection. Holds an internal cache keyed by widget
 * token; cache entries are populated on first `IsAllowed` call for that type.
 *
 * Lifetime: owned by `UMonolithUIRegistrySubsystem`. The subsystem calls
 * `Invalidate` whenever the underlying registry changes (init / OnPostEngineInit
 * re-scan / hot-reload refresh).
 */
class MONOLITHUI_API FUIPropertyAllowlist
{
public:
    /**
     * Construct against a backing type registry. The registry must outlive
     * the allowlist — the subsystem owns both, so this is automatic.
     */
    explicit FUIPropertyAllowlist(const FUITypeRegistry& InRegistry);

    /**
     * Test whether a property path is permitted for the given widget type.
     * Returns false for unknown types (no registry entry) AND for known
     * types whose mapping list does not include the path.
     */
    bool IsAllowed(const FName& WidgetToken, const FString& JsonPath) const;

    /**
     * Read-only view of all permitted paths for a type. Builds the cache
     * entry on demand. Returns an empty array for unknown tokens.
     */
    const TArray<FString>& GetAllowedPaths(const FName& WidgetToken) const;

    /**
     * Drop all cache entries. Called by the subsystem after a registry
     * mutation. Cheap — cache rebuilds lazily on the next `IsAllowed` call.
     */
    void Invalidate();

private:
    /**
     * Build the per-type cache entry by walking the registry's
     * `PropertyMappings` for that type.
     */
    void BuildCacheFor(const FName& WidgetToken) const;

    const FUITypeRegistry& Registry;

    // Mutable: lazy population during a const `IsAllowed` call.
    mutable TMap<FName, TSet<FString>> AllowedPaths;
    // Mirror in TArray form for `GetAllowedPaths` callers that want stable order.
    mutable TMap<FName, TArray<FString>> AllowedPathsList;
};
