// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "ACFHUD.generated.h"

class UUserWidget;

/**
 * 
 */
UCLASS()
class ASCENTCOMBATFRAMEWORK_API AACFHUD : public AHUD
{
	GENERATED_BODY()

protected:

	UPROPERTY(EditAnywhere, Category = ACF)
	TSubclassOf<UUserWidget> HUDClass;

	UPROPERTY(BlueprintReadWrite, Category = ACF)
	UUserWidget* HUDWidget;

	virtual void BeginPlay() override;

	virtual void PostInitProperties() override;

	virtual void PostRender() override;

public: 

	UFUNCTION(BlueprintCallable, Category = ACF)
    void SetHudEnabled(bool bEnabled);
	
private: 

	void InitHUD();

	bool enabled;
};
