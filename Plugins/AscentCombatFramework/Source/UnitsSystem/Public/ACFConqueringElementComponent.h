// // Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFAssaultPoint.h"
#include "Components/ActorComponent.h"
#include "CoreMinimal.h"
#include "GameplayTagContainer.h"

#include "ACFConqueringElementComponent.generated.h"

UCLASS(ClassGroup = (ACF), meta = (BlueprintSpawnableComponent))
class UNITSSYSTEM_API UACFConqueringElementComponent : public UActorComponent {
    GENERATED_BODY()

public:
    // Sets default values for this component's properties
    UACFConqueringElementComponent();

    UPROPERTY(BlueprintAssignable, Category = ACF)
    FOnConquerStateChanged OnConquerStateChanged;

protected:
    // Called when the game starts
    virtual void BeginPlay() override;

    UPROPERTY(EditAnywhere, Category = ACF)
    FGameplayTag AssaultPointTag;

    UPROPERTY(EditAnywhere, Category = ACF)
    bool bShowOnlyInDisplayState = false;

    UPROPERTY(EditAnywhere, meta = (EditCondition = "bShowOnlyInDisplayState"), Category = ACF)
    EConqueredState DisplayInState;


private: 
    
    TObjectPtr<AACFAssaultPoint> relatedPoint;

    UFUNCTION()
    void HandleStateChanged(const EConqueredState& newState);
};
