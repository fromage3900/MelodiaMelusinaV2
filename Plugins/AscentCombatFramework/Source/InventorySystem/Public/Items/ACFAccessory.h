// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include "Items/ACFEquippableItem.h"
#include "ACFAccessory.generated.h"

/**
 * 
 */
UCLASS()
class INVENTORYSYSTEM_API UACFAccessory : public UACFEquippableItem
{
	GENERATED_BODY()

public:

	UACFAccessory();

	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE FName GetAttachmentSocket() const {
		return AttachmentSocket;
	}

protected:

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
	FName AttachmentSocket;
	
};
