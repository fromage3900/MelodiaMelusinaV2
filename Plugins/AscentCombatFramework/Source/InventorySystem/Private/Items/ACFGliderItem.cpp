// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Items/ACFGliderItem.h"
#include "ItemActors/ACFGliderActor.h"

UACFGliderItem::UACFGliderItem()
{
    GliderActorClass = AACFGliderActor::StaticClass();
}

TSubclassOf<AACFItemActor> UACFGliderItem::GetItemActorClass_Implementation() const
{
    return GliderActorClass;
}
