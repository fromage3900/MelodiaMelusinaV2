// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Components/ActorComponent.h"
#include "CoreMinimal.h"

#include "ACFTopDownControllerComponent.generated.h"


UCLASS(ClassGroup = (ACF), meta = (BlueprintSpawnableComponent))
class CHARACTERCONTROLLER_API UACFTopDownControllerComponent : public UActorComponent {
    GENERATED_BODY()

public:
    // Sets default values for this component's properties
    UACFTopDownControllerComponent();
    /** Input handlers for SetDestination action. */
    /*    UFUNCTION(BlueprintCallable, Category = ACF)*/
   

    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetDestinationTriggered();

    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetDestinationReleased();

protected:
    // Called when the game starts
    virtual void BeginPlay() override;

    /** Click Input Action */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
    bool bEnabled;

    /** Time Threshold to know if it was a short press */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)

    float ShortPressThreshold;
    /** Click Input Action */
//     UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
//     UInputAction* SetDestinationClickAction;

    /** FX Class that we will spawn when clicking */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = Input)
    class UNiagaraSystem* FXCursor;

private:
    float FollowTime; // For how long it has been pressed

    FVector CachedDestination;

     void OnInputStarted();

     class APlayerController* GetOwnerController() const;
};
