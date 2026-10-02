// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Actors/ACFCharacter.h"
#include "CoreMinimal.h"
#include <GameFramework/PlayerController.h>
#include <GameplayTagContainer.h>

#include "ACFPlayerController.generated.h"

class UACFTeamComponent;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnPossessedCharacterChanged, const class APawn*, pawn);


/**
 * Custom PlayerController for ACF framework.
 * Handles possession logic, camera input tracking, and team assignment.
 */
UCLASS()
class ASCENTCOMBATFRAMEWORK_API AACFPlayerController : public APlayerController, public IACFEntityInterface, public IGenericTeamAgentInterface {
    GENERATED_BODY()

public:
    AACFPlayerController();

    /**
     * Returns the currently possessed ACFCharacter
     * @return Pointer to the currently possessed AACFCharacter, or nullptr if none
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE class AACFCharacter* GetPossessedACFCharacter() const { return PossessedCharacter; }

    /**
     * Returns the current accumulated camera rotation input
     * @return Current camera input rotation
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE FRotator GetCameraInput() const { return RotationInput; }

    /**
     * Returns the seconds elapsed since the last camera input
     * @return Seconds since last camera movement input
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE float GetSecondsFromLastCameraInput() const { return secondsFromLastCameraInput; }

    /**
     * Returns the X axis camera sensitivity
     * @return Float representing horizontal sensitivity
     */
    UFUNCTION(BlueprintPure, BlueprintNativeEvent, Category = ACF)
    float GetXSensitivity() const;

    /**
     * Returns the Y axis camera sensitivity
     * @return Float representing vertical sensitivity
     */
    UFUNCTION(BlueprintPure, BlueprintNativeEvent, Category = ACF)
    float GetYSensitivity() const;



    /**
     * Called when the possessed character changes
     */
    UPROPERTY(BlueprintAssignable, Category = ACF)
    FOnPossessedCharacterChanged OnPossessedCharacterChanged;

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

protected:
    /**
     * Called when the possessed pawn dies
     */
    UFUNCTION(BlueprintNativeEvent, Category = ACF)
    void OnPossessedPawnDeath();

    UPROPERTY(BlueprintReadOnly, Category = ACF)
    TObjectPtr<AACFCharacter> PossessedCharacter;

    // Called when the game starts
    virtual void BeginPlay() override;

    // Called every frame
    virtual void Tick(float DeltaSeconds) override;

    // Called when a new pawn is possessed
    virtual void OnPossess(APawn* aPawn) override;

    // Enables or disables components on the possessed character
    void EnableCharacterComponents(bool bEnabled);

    // Called when the pawn is unpossessed
    virtual void OnUnPossess() override;

    IACFEntityInterface* PossessedEntity;

private:
    float secondsFromLastCameraInput = 0.f;

    FDateTime lastInput;

    void HandleNewEntityPossessed();

	virtual void OnRep_Pawn() override;
};
