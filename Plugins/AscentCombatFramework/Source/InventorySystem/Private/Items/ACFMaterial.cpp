// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 


#include "Items/ACFMaterial.h"
#include "Items/ACFItem.h"
#include "ACFItemTypes.h"

UACFMaterial::UACFMaterial()
{
	ItemInfo.ItemType = EItemType::Material;
	ItemInfo.Name = FText::FromString("Base Material");
	ItemInfo.MaxInventoryStack = 20;
}
