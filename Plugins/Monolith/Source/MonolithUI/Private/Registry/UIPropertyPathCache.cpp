// Copyright tumourlove. All Rights Reserved.
// UIPropertyPathCache.cpp
//
// LRU implementation. The fast path on hit is two TMap lookups (key index +
// re-validate name lookup) plus a property-name re-walk. Cap is 256; eviction
// is O(N) which is acceptable at this size.

#include "Registry/UIPropertyPathCache.h"

#include "MonolithUICommon.h"
#include "UObject/Class.h"
#include "UObject/UnrealType.h"
#include "UObject/UObjectGlobals.h"

FUIPropertyPathCache::FUIPropertyPathCache(int32 InCapacity)
    : CacheCapacity(FMath::Max(1, InCapacity))
{
}

FName FUIPropertyPathCache::MakeKey(const FName& RootStructName, const FString& PropertyPath)
{
    // Compose a single FName key — `<RootStructName>::<PropertyPath>`. FName is
    // case-insensitive in storage; PropertyPath segments are case-insensitive
    // FProperty names anyway (engine convention), so this is correctness-safe.
    return FName(*FString::Printf(TEXT("%s::%s"), *RootStructName.ToString(), *PropertyPath));
}

bool FUIPropertyPathCache::ResolveChain(UStruct* RootStruct, const FString& PropertyPath, FUIPropertyPathChain& OutChain)
{
    OutChain.PropertyChain.Reset();
    OutChain.StructChain.Reset();
    OutChain.bValid = false;

    if (!RootStruct || PropertyPath.IsEmpty())
    {
        return false;
    }

    // Split on '.' — each segment is one FProperty hop.
    TArray<FString> Segments;
    PropertyPath.ParseIntoArray(Segments, TEXT("."), /*bCullEmpty=*/true);
    if (Segments.Num() == 0)
    {
        return false;
    }

    UStruct* CurrentStruct = RootStruct;
    for (int32 i = 0; i < Segments.Num(); ++i)
    {
        if (!CurrentStruct)
        {
            return false;
        }

        FProperty* Prop = CurrentStruct->FindPropertyByName(FName(*Segments[i]));
        if (!Prop)
        {
            return false;
        }

        OutChain.PropertyChain.Add(Prop);
        OutChain.StructChain.Add(CurrentStruct);

        // Descend into the next struct/object for the next segment, if any.
        const bool bIsLast = (i == Segments.Num() - 1);
        if (!bIsLast)
        {
            if (FStructProperty* StructProp = CastField<FStructProperty>(Prop))
            {
                CurrentStruct = StructProp->Struct;
            }
            else if (FObjectProperty* ObjectProp = CastField<FObjectProperty>(Prop))
            {
                CurrentStruct = ObjectProp->PropertyClass;
            }
            else
            {
                // Cannot descend — the path nests through something we don't
                // navigate (TArray, TMap, primitive, etc.). Treat as failure.
                return false;
            }
        }
    }

    OutChain.bValid = true;
    return true;
}

bool FUIPropertyPathCache::RevalidateEntry(FCacheEntry& Entry, UStruct* FreshRoot) const
{
    // Re-walk the chain against the caller-supplied live root. Hot-reload
    // swaps UClass/UScriptStruct pointers but preserves FName; the caller's
    // `Root->GetClass()` always lands on the post-reload replacement, so
    // re-walking properties by name from that fresh pointer catches any
    // property-layout shift while sidestepping the FindObject-on-transient-
    // package lookup that returns nullptr for UClasses (`/Script/<Module>/`).
    if (!FreshRoot)
    {
        return false;
    }

    FUIPropertyPathChain FreshChain;
    if (!ResolveChain(FreshRoot, Entry.PropertyPath, FreshChain))
    {
        return false;
    }

    Entry.Chain = MoveTemp(FreshChain);
    return true;
}

void FUIPropertyPathCache::EvictLeastRecentlyUsed()
{
    if (Entries.Num() == 0)
    {
        return;
    }

    int32 OldestIdx = 0;
    uint64 OldestStamp = Entries[0].LastAccessStamp;
    for (int32 i = 1; i < Entries.Num(); ++i)
    {
        if (Entries[i].LastAccessStamp < OldestStamp)
        {
            OldestStamp = Entries[i].LastAccessStamp;
            OldestIdx = i;
        }
    }

    const FName OldestKey = MakeKey(Entries[OldestIdx].RootStructName, Entries[OldestIdx].PropertyPath);
    KeyIndex.Remove(OldestKey);
    Entries.RemoveAtSwap(OldestIdx, EAllowShrinking::No);

    // RemoveAtSwap moved the last element into OldestIdx — fix up its key
    // entry to point at the new index.
    if (OldestIdx < Entries.Num())
    {
        const FName MovedKey = MakeKey(Entries[OldestIdx].RootStructName, Entries[OldestIdx].PropertyPath);
        KeyIndex.Add(MovedKey, OldestIdx);
    }

    ++EvictionCount;
}

FUIPropertyPathChain FUIPropertyPathCache::Get(const FName& RootStructName, UStruct* RootStruct, const FString& PropertyPath)
{
    if (RootStructName.IsNone() || PropertyPath.IsEmpty() || !RootStruct)
    {
        FUIPropertyPathChain Empty;
        return Empty;
    }

    const FName Key = MakeKey(RootStructName, PropertyPath);

    // Hit path — bump LRU stamp and re-validate against the caller-supplied
    // live root (sidesteps the transient-package FindObject lookup that fails
    // for UClasses living in `/Script/<Module>/`).
    if (const int32* IdxPtr = KeyIndex.Find(Key))
    {
        const int32 Idx = *IdxPtr;
        FCacheEntry& Entry = Entries[Idx];

        if (RevalidateEntry(Entry, RootStruct))
        {
            Entry.LastAccessStamp = NextLRUStamp++;
            ++HitCount;
            return Entry.Chain;
        }

        // Re-validation failed (hot-reload swap). Evict and fall through.
        KeyIndex.Remove(Key);
        Entries.RemoveAtSwap(Idx, EAllowShrinking::No);
        if (Idx < Entries.Num())
        {
            const FName MovedKey = MakeKey(Entries[Idx].RootStructName, Entries[Idx].PropertyPath);
            KeyIndex.Add(MovedKey, Idx);
        }
        ++EvictionCount;
    }

    // Miss path — fresh resolve against the caller-supplied root.
    ++MissCount;

    FUIPropertyPathChain FreshChain;
    if (!ResolveChain(RootStruct, PropertyPath, FreshChain))
    {
        // Don't cache invalid chains — repeated bad paths shouldn't pollute.
        return FreshChain;
    }

    // Insert. Evict first if at cap.
    if (Entries.Num() >= CacheCapacity)
    {
        EvictLeastRecentlyUsed();
    }

    FCacheEntry NewEntry;
    NewEntry.RootStructName = RootStructName;
    NewEntry.PropertyPath = PropertyPath;
    NewEntry.Chain = FreshChain;
    NewEntry.LastAccessStamp = NextLRUStamp++;

    const int32 NewIdx = Entries.Add(MoveTemp(NewEntry));
    KeyIndex.Add(Key, NewIdx);

    return FreshChain;
}

void FUIPropertyPathCache::Reset()
{
    KeyIndex.Reset();
    Entries.Reset();
    NextLRUStamp = 1;
}

void FUIPropertyPathCache::ResetCounters()
{
    HitCount = 0;
    MissCount = 0;
    EvictionCount = 0;
}
