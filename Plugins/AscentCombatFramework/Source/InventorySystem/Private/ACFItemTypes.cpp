// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFItemTypes.h"
#include "Components/ACFArmorSlotComponent.h"

FModularPart::FModularPart(const TObjectPtr<UACFArmorSlotComponent>& inComp)
{
    meshComp = inComp;
    ItemSlot = inComp->GetSlotTag();
};


namespace FACFTags
{
	UE_DEFINE_GAMEPLAY_TAG(WeaponShoot, "Weapon.Shoot");
	UE_DEFINE_GAMEPLAY_TAG(WeaponPull,  "Weapon.Pull");
	UE_DEFINE_GAMEPLAY_TAG(WeaponReload,"Weapon.Reload");

}
