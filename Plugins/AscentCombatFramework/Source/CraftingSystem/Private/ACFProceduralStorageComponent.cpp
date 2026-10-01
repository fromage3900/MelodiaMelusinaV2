// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 


#include "ACFProceduralStorageComponent.h"
#include "Kismet/GameplayStatics.h"
#include "GameFramework/GameState.h"
#include "ACFItemsManagerComponent.h"

void UACFProceduralStorageComponent::GenerateStorageItems_Implementation()
{
	if (bGenerated) {
		return;
	}
	UACFItemsManagerComponent* itemsManager = GetItemsManager();
	if (itemsManager) {
		TArray<FBaseItem> items;
		if (!itemsManager->GenerateItemsFromRules(ItemGenerationRules, items)) {
			UE_LOG(LogTemp, Warning, TEXT("Something went wrong in items generation! - UACFProceduralStorageComponent"));
		}
		bGenerated = true;
		AddItems(items);
	}
	else {
		UE_LOG(LogTemp, Error, TEXT("No Items manager in your game state! - UACFProceduralStorageComponent"));
	}
}

bool UACFProceduralStorageComponent::GenerateStorageItems_Validate()
{
	return true;
}


UACFItemsManagerComponent* UACFProceduralStorageComponent::GetItemsManager() const
{
    const APlayerController* gameState = UGameplayStatics::GetPlayerController(this, 0);
    if (gameState) {
        return gameState->FindComponentByClass<UACFItemsManagerComponent>();
    }
    return nullptr;
}