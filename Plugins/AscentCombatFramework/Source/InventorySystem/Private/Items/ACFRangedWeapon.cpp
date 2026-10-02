// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Items/ACFRangedWeapon.h"
#include "ItemActors/ACFRangedWeaponActor.h"

UACFRangedWeapon::UACFRangedWeapon()
{
    ItemInfo.ItemType = EItemType::RangedWeapon;
    ItemInfo.Name = FText::FromString("Base Ranged Weapon");
    ItemActorClass = AACFRangedWeaponActor::StaticClass();
}
