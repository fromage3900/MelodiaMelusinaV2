// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "AIController.h"
#include "CoreMinimal.h"
#include "Interfaces/ACFEntityInterface.h"

#include "ACFRiderAIController.generated.h"

/**
 *
 */
UCLASS()
class MOUNTSYSTEM_API AACFRiderAIController : public AAIController, public IACFEntityInterface {
    GENERATED_BODY()

public:
    AACFRiderAIController();

protected:
    virtual void UpdateControlRotation(float DeltaTime, bool bUpdatePawn = true) override;

    virtual void OnPossess(APawn* InPawn) override;

    virtual void OnUnPossess() override;

    UPROPERTY(EditDefaultsOnly, Category = ACF)
    bool bOverrideControlWithMountRotation = true;

    UPROPERTY(EditDefaultsOnly, meta = (EditCondition = "bOverrideControlWithMountRotation == true"), Category = ACF)
    FRotator OffsetRotCorrection;

    UPROPERTY(EditDefaultsOnly, meta = (EditCondition = "bOverrideControlWithMountRotation == true"), Category = ACF)
    FRotator ClampMin;

    UPROPERTY(EditDefaultsOnly, meta = (EditCondition = "bOverrideControlWithMountRotation == true"), Category = ACF)
    FRotator ClampMax;

    virtual void GetPlayerViewPoint(FVector& out_Location, FRotator& out_Rotation) const override;

    /// <summary>
    /// /Combat Team Interface
    /// </summary>

    // IACFEntityInterface - Main implementation (source of truth)
    virtual FGameplayTag GetEntityCombatTeam_Implementation() const override;
    virtual void AssignTeamToEntity_Implementation(FGameplayTag inCombatTeam) override;

    // IGenericTeamAgentInterface - Read from TeamComponent
    virtual FGenericTeamId GetGenericTeamId() const override;
    virtual void SetGenericTeamId(const FGenericTeamId& TeamID) override;
    virtual ETeamAttitude::Type GetTeamAttitudeTowards(const AActor& OtherTeam) const override;

    /// <summary>
    /// /End Combat Team Entity
    /// </summary>
private:
    void SetRiderCompReference();

    TObjectPtr<class AController> GetMountController() const;
    TObjectPtr<class UACFRiderComponent> riderComp;
    TObjectPtr<class AController> MountController;
};
