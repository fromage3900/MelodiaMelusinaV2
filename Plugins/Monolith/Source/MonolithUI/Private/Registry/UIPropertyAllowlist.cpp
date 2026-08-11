// Copyright tumourlove. All Rights Reserved.
// UIPropertyAllowlist.cpp
//
// Implementation: lazy projection over `FUITypeRegistry::PropertyMappings`.
// First call for a given token populates two parallel mutable maps:
//   * `AllowedPaths` — the hot-path TSet used by `IsAllowed`.
//   * `AllowedPathsList` — a stable-ordered TArray for diagnostic dumps.
//
// Both maps share the same key (FName widget token). Keeping them parallel
// (rather than just rebuilding a TArray from the TSet on every call) avoids
// repeated allocations in the dump diagnostic path.

#include "Registry/UIPropertyAllowlist.h"
#include "Registry/UITypeRegistry.h"

FUIPropertyAllowlist::FUIPropertyAllowlist(const FUITypeRegistry& InRegistry)
    : Registry(InRegistry)
{
}

bool FUIPropertyAllowlist::IsAllowed(const FName& WidgetToken, const FString& JsonPath) const
{
    if (WidgetToken.IsNone() || JsonPath.IsEmpty())
    {
        return false;
    }

    if (!AllowedPaths.Contains(WidgetToken))
    {
        BuildCacheFor(WidgetToken);
    }

    const TSet<FString>* PathSet = AllowedPaths.Find(WidgetToken);
    return PathSet && PathSet->Contains(JsonPath);
}

const TArray<FString>& FUIPropertyAllowlist::GetAllowedPaths(const FName& WidgetToken) const
{
    if (!AllowedPathsList.Contains(WidgetToken))
    {
        BuildCacheFor(WidgetToken);
    }

    if (const TArray<FString>* List = AllowedPathsList.Find(WidgetToken))
    {
        return *List;
    }

    static const TArray<FString> Empty;
    return Empty;
}

void FUIPropertyAllowlist::Invalidate()
{
    AllowedPaths.Reset();
    AllowedPathsList.Reset();
}

void FUIPropertyAllowlist::BuildCacheFor(const FName& WidgetToken) const
{
    TSet<FString>& PathSet = AllowedPaths.FindOrAdd(WidgetToken);
    TArray<FString>& PathList = AllowedPathsList.FindOrAdd(WidgetToken);

    PathSet.Reset();
    PathList.Reset();

    const FUITypeRegistryEntry* Entry = Registry.FindByToken(WidgetToken);
    if (!Entry)
    {
        // Cache the empty set so repeated calls short-circuit.
        return;
    }

    PathList.Reserve(Entry->PropertyMappings.Num());
    for (const FUIPropertyMapping& Mapping : Entry->PropertyMappings)
    {
        bool bAlreadyInSet = false;
        PathSet.Add(Mapping.JsonPath, &bAlreadyInSet);
        if (!bAlreadyInSet)
        {
            PathList.Add(Mapping.JsonPath);
        }
    }
}
