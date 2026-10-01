// // Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.


#include "ACFCraftingFunctionLibrary.h"
#include <Kismet/GameplayStatics.h>


UACFItemsManagerComponent* UACFCraftingFunctionLibrary::GetItemManager(UObject* WorldContextObject, int32 playerIndex /*= 0*/)
{
    const APlayerController* playercont = UGameplayStatics::GetPlayerController(WorldContextObject, playerIndex);
    if (playercont) {
        return playercont->FindComponentByClass<UACFItemsManagerComponent>();
    }
    UE_LOG(LogTemp, Error, TEXT("Missing Item Manager Component in Player Controller - UACFItemSystemFunctionLibrary::GetItemManager"));


    return nullptr;
}