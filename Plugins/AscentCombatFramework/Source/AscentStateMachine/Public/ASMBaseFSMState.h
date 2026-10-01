// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include <GameFramework/Actor.h>
#include <GameplayTagContainer.h>

#include "ASMBaseFSMState.generated.h"


/**
 *
 */
UCLASS(Blueprintable, EditInlineNew)
class ASCENTSTATEMACHINE_API UASMBaseFSMState : public UObject {
    GENERATED_BODY()

    friend class UASMStateNode;
    friend class UASMStateMachine;

private:
    void Internal_OnEnter(class APlayerController* playerController, class UASMStateMachine* inFSM);

    void Internal_OnExit();

public:
    /*Triggers the provided transition , returns whether the transition is successful*/
    UFUNCTION(BlueprintCallable, Category = ASM)
    bool TriggerTransition(const FGameplayTag& transition);

    UFUNCTION(BlueprintPure, Category = ASM)
    AActor* GetActorOwner() const
    {
        return actorOwner;
    }

protected:
    UPROPERTY(BlueprintReadOnly, Category = ASM)
    class APlayerController* LocalController;

    UPROPERTY(BlueprintReadOnly, Category = ASM)
    class UASMStateMachine* FSM;

    UPROPERTY(BlueprintReadOnly, Category = ASM)
    AActor* actorOwner;

    UFUNCTION(BlueprintNativeEvent, Category = ASM)
    void OnEnter();
    virtual void OnEnter_Implementation();

    UFUNCTION(BlueprintNativeEvent, Category = ASM)
    void OnExit();
    virtual void OnExit_Implementation();

    UFUNCTION(BlueprintNativeEvent, Category = ASM)
    void OnUpdate(float deltaTime);
    virtual void OnUpdate_Implementation(float deltaTime);

    UFUNCTION(BlueprintNativeEvent, Category = ASM)
    void OnTransition(const UASMBaseFSMState* previousState);
    virtual void OnTransition_Implementation(const UASMBaseFSMState* previousState);

    UFUNCTION(BlueprintPure, Category = ASM)
    class APlayerController* GetLocalPlayerController() const
    {
        return LocalController;
    }

    UFUNCTION(BlueprintPure, Category = ASM)
    FORCEINLINE class UASMStateMachine* GetFSM() const
    {
        return FSM;
    }

    UFUNCTION(BlueprintPure, Category = ASM)
    UWorld* GetWorldContextObject() const;

    // UObject interface
    UWorld* GetWorld() const override { return LocalController ? LocalController->GetWorld() : nullptr; }
    // End of UObject interface
};
