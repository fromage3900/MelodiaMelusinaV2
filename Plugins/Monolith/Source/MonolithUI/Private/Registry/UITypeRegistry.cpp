// Copyright tumourlove. All Rights Reserved.
// UITypeRegistry.cpp
//
// Implementation notes:
//   * `Types` is a TArray (cache-friendly iteration; the registry has ~50
//     entries in stock UMG plus whatever plugins add). `TokenIndex` is the
//     primary lookup map — keyed by FName so case-sensitive hashing works
//     out-of-the-box.
//   * `RefreshStaleEntries` is the hot-reload repair path. Walking the index
//     once and resolving any null `WidgetClass` against `FindFirstObject<UClass>`
//     keeps the registry stable across Live Coding cycles without forcing the
//     subsystem to re-scan everything (which would also rebuild PropertyMappings
//     unnecessarily).

#include "Registry/UITypeRegistry.h"

#include "MonolithUICommon.h"
#include "UObject/Class.h"
#include "UObject/UObjectGlobals.h"

void FUITypeRegistry::Reset()
{
    Types.Reset();
    TokenIndex.Reset();
}

void FUITypeRegistry::RegisterType(FUITypeRegistryEntry&& Entry)
{
    if (Entry.Token.IsNone())
    {
        UE_LOG(LogMonolithUISpec, Warning,
            TEXT("FUITypeRegistry::RegisterType called with empty token — skipping"));
        return;
    }

    if (int32* ExistingIdx = TokenIndex.Find(Entry.Token))
    {
        Types[*ExistingIdx] = MoveTemp(Entry);
    }
    else
    {
        const int32 NewIdx = Types.Add(MoveTemp(Entry));
        TokenIndex.Add(Types[NewIdx].Token, NewIdx);
    }
}

const FUITypeRegistryEntry* FUITypeRegistry::FindByToken(const FName& Token) const
{
    if (const int32* Idx = TokenIndex.Find(Token))
    {
        return &Types[*Idx];
    }
    return nullptr;
}

const FUITypeRegistryEntry* FUITypeRegistry::FindByClass(const UClass* WidgetClass) const
{
    if (!WidgetClass)
    {
        return nullptr;
    }

    for (const FUITypeRegistryEntry& Entry : Types)
    {
        if (Entry.WidgetClass.Get() == WidgetClass)
        {
            return &Entry;
        }
    }
    return nullptr;
}

int32 FUITypeRegistry::RefreshStaleEntries()
{
    int32 Refreshed = 0;
    for (FUITypeRegistryEntry& Entry : Types)
    {
        if (Entry.WidgetClass.IsValid())
        {
            continue;
        }

        // Resolve the same token against the freshly loaded UObject pool.
        // `FindFirstObject<UClass>` is the right tool because hot-reloaded
        // classes keep the same FName but live at a new address.
        UClass* RefreshedClass = FindFirstObject<UClass>(*Entry.Token.ToString(), EFindFirstObjectOptions::None);
        if (RefreshedClass)
        {
            Entry.WidgetClass = RefreshedClass;
            // Slot class may also have been hot-reloaded — null it out so the
            // next full `RescanWidgetTypes` pass re-resolves it from the CDO.
            // We deliberately don't re-resolve here to keep the refresh path
            // O(N) and free of CDO touches; the orchestrator will follow up
            // with a rescan when it next needs slot-class info.
            Entry.SlotClass = nullptr;
            ++Refreshed;
        }
    }
    return Refreshed;
}
