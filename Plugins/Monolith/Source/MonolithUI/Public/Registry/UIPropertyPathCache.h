// Copyright tumourlove. All Rights Reserved.
// UIPropertyPathCache.h
//
// LRU cache for resolved property chains used by `FUIReflectionHelper`. The
// reflection helper otherwise re-walks the FProperty link list on every
// `set_widget_property` call — for nested paths like `Slot.LayoutData.Offsets.Left`
// that's four `FindPropertyByName` linear scans per call. With the cache, a
// repeat write to the same path on the same widget UClass is two TMap lookups
// plus a re-validate pass.
//
// Why re-validate on every hit (and not just on miss): hot-reload / Live Coding
// can replace the underlying UClass / UScriptStruct out from under us. The
// cached `FProperty*` and `UStruct*` pointers in a stale entry would then
// dangle — using them on the new memory layout is undefined behaviour at best,
// a crash at worst. The re-validate pass costs us one `FindObject<UStruct>`
// + N `FProperty::FindPropertyByName` calls per hit, which is the exact same
// cost as a miss-walk minus the descent into nested struct properties (we
// stop at the property level; we do NOT re-descend the whole chain because
// the chain is what we're validating).
//
// LRU eviction policy: cap at 256 entries. On insert-overflow, evict the
// entry with the oldest `LastAccessTimestamp`. Timestamp is a monotonic
// counter (we don't need wall-clock — strict ordering is enough).
//
// Thread safety: the cache is owned by `UMonolithUIRegistrySubsystem` (an
// editor subsystem). All current consumers are game-thread. If a future
// caller wants to drive this from a worker, wrap reads in an FRWScopeLock —
// not added yet because nothing currently reads off-thread.
//
// Clean-room: cache shape and re-validation rule are OURS. Hot-reload safety
// rule (re-find by name on hit) was derived from inspection of the
// `OnReloadComplete` / `RefreshStaleEntries` pattern already in use elsewhere
// in MonolithUI, NOT from any reference plugin.

#pragma once

#include "CoreMinimal.h"
#include "UObject/NameTypes.h"
#include "UObject/WeakObjectPtrTemplates.h"

class FProperty;
class UStruct;

/**
 * One resolved property chain. The chain is the sequence of FProperty hops
 * needed to walk from `RootStructName`'s root down to the leaf property whose
 * value the helper writes.
 *
 * For a flat path like "Visibility" the chain has length 1.
 * For "Slot.Padding" the chain has length 2:
 *   [0] FObjectProperty "Slot" (resolves UPanelSlot)
 *   [1] FStructProperty "Padding" (resolves FMargin)
 *
 * `StructChain` mirrors the property chain: entry [i] is the UStruct/UClass
 * whose property [i] resolves on. Used by the re-validation pass to look up
 * each property by name from a fresh root.
 *
 * Dotted-path semantics: each `.` segment is one FProperty lookup. Container
 * properties (TArray / TMap) are NOT navigated by the cache — those would
 * need a `[idx]` syntax we deliberately don't support. The reflection helper
 * rejects writes to array elements via the dotted path; callers can pass the
 * full container value as the JSON payload instead.
 */
struct MONOLITHUI_API FUIPropertyPathChain
{
    /** Resolved FProperty hops from root to leaf. Always non-empty when valid. */
    TArray<FProperty*> PropertyChain;

    /**
     * UStruct/UClass for each chain hop. `StructChain[i]` is the type that
     * `PropertyChain[i]` was found on. `StructChain.Num() == PropertyChain.Num()`.
     */
    TArray<UStruct*> StructChain;

    /** True when the chain resolved successfully. */
    bool bValid = false;
};

/**
 * LRU cache from `(RootStructName, PropertyPath)` -> resolved chain.
 *
 * Lifetime: owned by `UMonolithUIRegistrySubsystem` (held via TUniquePtr,
 * mirroring the `Allowlist` pattern). Cache survives across actions and
 * across hot-reload cycles (entries refreshed on hit; stale entries evicted).
 */
class MONOLITHUI_API FUIPropertyPathCache
{
public:
    /**
     * Default cap is 256 entries — large enough for the realistic working set
     * (~50 widget types x a handful of common paths each) without unbounded
     * growth from pathological scripted callers.
     */
    explicit FUIPropertyPathCache(int32 InCapacity = 256);

    /**
     * Resolve the property chain for `(RootStructName, PropertyPath)`.
     *
     * `RootStructName` is the FName cache key (e.g. `Root->GetClass()->GetFName()`).
     * `RootStruct` is the live UStruct the caller already holds (almost always
     * `Root->GetClass()`, which is a `UClass* → UStruct*` upcast). Passing it
     * in directly avoids a `FindObject<UStruct>(nullptr, ...)` lookup that
     * would otherwise probe the transient package and fail for UClasses (whose
     * outer is `/Script/<ModuleName>/`, not the transient package). This was
     * the root cause of the spurious `PropertyNotFound` warnings on nested
     * paths like `Config.Shape.CornerRadii` for `UEffectSurface`.
     *
     * On hit: re-validates the cached chain against the supplied `RootStruct`
     * (catches hot-reload pointer swaps — the FName key survives but the
     * UStruct* changes). If revalidation fails, the entry is evicted and the
     * lookup falls through to a fresh resolve using the supplied `RootStruct`.
     *
     * On miss: walks the property link list from `RootStruct` downward,
     * splitting `PropertyPath` on `.`. Each hop must be either a flat
     * FProperty or a FStructProperty/FObjectProperty whose nested `Struct`
     * (or `PropertyClass`) hosts the next segment. Returns an `bValid=false`
     * chain if any hop fails — the helper turns that into a `PropertyNotFound`
     * apply result.
     *
     * Hit and miss counters increment regardless of validity (a missed lookup
     * still costs a walk, and the diagnostic wants to see the rate).
     */
    FUIPropertyPathChain Get(const FName& RootStructName, UStruct* RootStruct, const FString& PropertyPath);

    /** Wipe the cache. Cheap — entries rebuild lazily. */
    void Reset();

    /** Number of entries currently in the cache. */
    int32 Num() const { return Entries.Num(); }

    /** Configured cap. */
    int32 Capacity() const { return CacheCapacity; }

    /** Cache hit count since construction (or last `ResetCounters`). */
    int64 GetHitCount() const { return HitCount; }

    /** Cache miss count since construction (or last `ResetCounters`). */
    int64 GetMissCount() const { return MissCount; }

    /** Cache eviction count since construction (or last `ResetCounters`). */
    int64 GetEvictionCount() const { return EvictionCount; }

    /** Reset hit/miss/eviction counters without dropping cache contents. */
    void ResetCounters();

private:
    /** One stored cache entry. Holds the chain plus an LRU timestamp. */
    struct FCacheEntry
    {
        FName RootStructName;
        FString PropertyPath;
        FUIPropertyPathChain Chain;
        /**
         * Monotonic LRU stamp — incremented every time this entry is touched
         * (either on insert or on hit). Eviction picks the smallest stamp.
         */
        uint64 LastAccessStamp = 0;
    };

    /**
     * Walk the property link list from `RootStruct` following the dotted
     * `PropertyPath`. Populates `OutChain.PropertyChain` and
     * `OutChain.StructChain`. Returns true if every hop resolved.
     *
     * Pure function — extracted so both Get (miss path) and the re-validate
     * pass call into the same routine.
     */
    static bool ResolveChain(
        UStruct* RootStruct,
        const FString& PropertyPath,
        FUIPropertyPathChain& OutChain);

    /**
     * Re-walk the chain against the caller-supplied `FreshRoot` (the live
     * UStruct from the caller's UObject->GetClass()). Returns true if the
     * cached entry remains valid against the fresh root. On false, the
     * caller evicts.
     *
     * Why caller-supplied (not re-find by name): UClasses live in
     * `/Script/<Module>/` packages, so `FindObject<UStruct>(nullptr, Name)`
     * targeting the transient package returns nullptr and we'd never validate.
     * Hot-reload safety is preserved: the caller's `Root->GetClass()` always
     * yields the post-reload-replaced UClass, so the chain re-walk catches
     * any property-layout shift that survived the reload.
     */
    bool RevalidateEntry(FCacheEntry& Entry, UStruct* FreshRoot) const;

    /** Pop the oldest entry (smallest LRU stamp). Increments EvictionCount. */
    void EvictLeastRecentlyUsed();

    /** Build the cache key for the lookup map. */
    static FName MakeKey(const FName& RootStructName, const FString& PropertyPath);

    /**
     * Map key -> index into `Entries`. Indices stay stable for the life of
     * an entry; eviction does an O(N) compaction (cap is 256 so this is fine).
     */
    TMap<FName, int32> KeyIndex;
    TArray<FCacheEntry> Entries;
    int32 CacheCapacity = 256;

    /** Monotonic LRU stamp source. Incremented on every Get call. */
    uint64 NextLRUStamp = 1;

    /** Diagnostic counters. */
    int64 HitCount = 0;
    int64 MissCount = 0;
    int64 EvictionCount = 0;
};
