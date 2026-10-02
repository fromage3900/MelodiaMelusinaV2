// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Items/ACFMeleeWeapon.h"
#include "ItemActors/ACFMeleeWeaponActor.h"

UACFMeleeWeapon::UACFMeleeWeapon()
{
    ItemActorClass = AACFMeleeWeaponActor::StaticClass();
    ItemInfo.ItemType = EItemType::MeleeWeapon;
    ItemInfo.Name = FText::FromString("Base Melee Weapon");
}
