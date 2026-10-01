// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Items/ACFArmor.h"
#include "Components/ACFArmorSlotComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/SkinnedMeshComponent.h"

UACFArmor::UACFArmor()
{
    ItemInfo.ItemType = EItemType::Armor;
    ItemInfo.Name = FText::FromString("BaseArmor");
    ArmorComponentClass = UACFArmorSlotComponent::StaticClass();
}

TSoftObjectPtr<USkinnedAsset> UACFArmor::GetArmorMesh_Implementation(AActor* actorOwner) const
{
    if (ArmorMeshes.IsValidIndex(0)) {
        return ArmorMeshes[0];
    }
    return nullptr;
}
