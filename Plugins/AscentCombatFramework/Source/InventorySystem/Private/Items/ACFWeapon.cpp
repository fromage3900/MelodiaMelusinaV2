// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Items/ACFWeapon.h"
#include "Components/ACFEquipmentComponent.h"
#include "ItemActors/ACFItemActor.h"

UACFWeapon::UACFWeapon()
{
}

TSoftObjectPtr<USkeletalMesh> UACFWeapon::GetWeaponMesh() const
{
    return WeaponMesh ;
}

TSubclassOf<AACFItemActor> UACFWeapon::GetItemActorClass_Implementation() const
{
    return ItemActorClass.LoadSynchronous();
}

bool UACFWeapon::CanBeEquipped_Implementation(UACFEquipmentComponent* equipComp)
{
    return equipComp->GetAllowedWeaponTypes().Contains(GetWeaponType());
}

void UACFWeapon::OnItemEquipped_Implementation()
{
    Super::OnItemEquipped_Implementation();
}

void UACFWeapon::OnItemUnEquipped_Implementation()
{
    Super::OnItemUnEquipped_Implementation();
}