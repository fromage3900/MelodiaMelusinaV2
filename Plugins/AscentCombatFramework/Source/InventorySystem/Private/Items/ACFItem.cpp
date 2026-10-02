// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Items/ACFItem.h"
#include "GameFramework/Pawn.h"
#include "ItemActors/ACFItemActor.h"
#include "Net/UnrealNetwork.h"
#include <AbilitySystemComponent.h>
#include <ActiveGameplayEffectHandle.h>
#include <GameplayEffect.h>
#include <GameplayEffectTypes.h>
#include <UObject/UObjectGlobals.h>

// Sets default values
UACFItem::UACFItem()
{

    ItemInfo.ItemType = EItemType::Other;
}

TSubclassOf<AACFItemActor> UACFItem::GetItemActorClass_Implementation() const
{
    return nullptr;
}

UWorld* UACFItem::GetWorld() const
{
    if (ItemOwner) {
        return ItemOwner->GetWorld();
    }
    return nullptr;
}

UACFItemFragment* UACFItem::GetFragmentByClass(TSubclassOf<UACFItemFragment> FragmentClass) const
{
    if (!FragmentClass) {
        return nullptr;
    }

    for (UACFItemFragment* Fragment : Fragments) {
        if (Fragment && Fragment->IsA(FragmentClass)) {
            return Fragment;
        }
    }

    return nullptr;
}

void UACFItem::Serialize(FArchive& Ar)
{
	Super::Serialize(Ar);

	// Only persist fragment instance data when saving/loading game state
	if (Ar.IsSaveGame())
	{
		int32 FragmentCount = Fragments.Num();
		Ar << FragmentCount;

		if (Ar.IsLoading())
		{
			// Fragments array is already populated from CDO during NewObject.
			// We just deserialize SaveGame properties into existing fragment instances.
			for (int32 i = 0; i < FMath::Min(FragmentCount, Fragments.Num()); ++i)
			{
				if (Fragments[i])
				{
					Fragments[i]->Serialize(Ar);
				}
			}
			// Skip any extra serialized fragments if CDO changed
			for (int32 i = Fragments.Num(); i < FragmentCount; ++i)
			{
				// Create a throwaway object to consume the bytes
				UACFItemFragment* Throwaway = NewObject<UACFItemFragment>();
				Throwaway->Serialize(Ar);
			}
		}
		else // Saving
		{
			for (int32 i = 0; i < FragmentCount; ++i)
			{
				if (Fragments[i])
				{
					Fragments[i]->Serialize(Ar);
				}
			}
		}
	}
}