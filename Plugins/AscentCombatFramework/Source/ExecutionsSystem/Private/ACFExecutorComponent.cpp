// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#include "ACFExecutorComponent.h"
#include "ATSBaseTargetComponent.h"
#include "Actors/ACFCharacter.h"
#include "Animation/ACFAnimInstance.h"
#include "CCMCameraFunctionLibrary.h"
#include "CCMPlayerCameraManager.h"
#include "Components/ACFAbilitySystemComponent.h"
#include "Components/ACFDamageHandlerComponent.h"
#include "Components/ACFEquipmentComponent.h"
#include "Components/ACFRagdollComponent.h"
#include "Game/ACFFunctionLibrary.h"
#include "Game/ACFTypes.h"
#include "Items/ACFWeapon.h"
#include <Animation/AnimMontage.h>
#include <GameFramework/Actor.h>
#include <GameFramework/Controller.h>
#include "UObject/CoreNet.h"
#include "Net/UnrealNetwork.h"

// Sets default values for this component's properties
UACFExecutorComponent::UACFExecutorComponent()
{
    // Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
    // off to improve performance if you don't need them.
    PrimaryComponentTick.bCanEverTick = false;

    // ...
}

void UACFExecutorComponent::BeginPlay()
{
    Super::BeginPlay();
}

void UACFExecutorComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    //

    DOREPLIFETIME(UACFExecutorComponent, currentBestExec);
}


void UACFExecutorComponent::OnCombinedAnimStarted(const FGameplayTag& animTag)
{
    if (GetCharacterOwner()->HasAuthority()) {
        SetCharacterActionsLock(GetCharacterOwner(), true, false);
        SetCharacterActionsLock(GetCharacterSlave(), true, currentBestExec.bCanBeHitDuringAnim);
    }

    if (currentBestExec.CameraEvent != NAME_None) {
        ACCMPlayerCameraManager* cameraManager = UCCMCameraFunctionLibrary::GetLocalCinematicCameraManager(this);
        if (cameraManager) {
            cameraManager->TriggerCameraSequence(GetCharacterOwner(), currentBestExec.CameraEvent);
        }
    }
}

void UACFExecutorComponent::OnCombinedAnimEnded(const FGameplayTag& animTag)
{
    if (GetCharacterOwner()->HasAuthority()) {
        SetCharacterActionsLock(GetCharacterOwner(), false, false);

        if (currentBestExec.bIsFatal) {
            AACFCharacter* acfChar = Cast<AACFCharacter>(GetCharacterSlave());
            if (acfChar) {
                acfChar->KillCharacter();
            }
        }
        else {
			SetCharacterActionsLock(GetCharacterSlave(), false, currentBestExec.bCanBeHitDuringAnim);
        }
    }
}

bool UACFExecutorComponent::TryExecuteCharacter(class ACharacter* target)
{
    if (!GetCharacterOwner()) {
        return false;
    }

    if (!target || !IsValid(target)) {
        return false;
    }

    const AACFCharacter* acfChar = Cast<AACFCharacter>(target);
    if (!acfChar) {
        return false;
    }

    if (!acfChar->IsAlive()) {
        return false;
    }
    const FGameplayTag animTag = GetBestExecutionTagForCharacter(ExecutionsByDirectionAndMovesetAction, target);
    return TryPlayCombinedAnimation(target, animTag);
}

bool UACFExecutorComponent::TryExecuteCurrentTarget()
{
    if (!GetCharacterOwner() || !GetCharacterOwner()->GetController()) {
        return false;
    }

    const UATSBaseTargetComponent* targetComp = GetCharacterOwner()->GetController()->FindComponentByClass<UATSBaseTargetComponent>();
    if (targetComp) {
        ACharacter* target = Cast<ACharacter>(targetComp->GetCurrentTarget());
        if (target) {
            return TryExecuteCharacter(target);
        }
    }
    return false;
}

FGameplayTag UACFExecutorComponent::GetBestExecutionTagForCharacter(const TMap<ERelativeDirection, FExecutions>& execMap, class ACharacter* target)
{
    if (!GetCharacterOwner() || !target) {
        return FGameplayTag();
    }

    const ERelativeDirection relDir = GetCharacterRelativedDirection(target);
    const AACFCharacter* acfChar = Cast<AACFCharacter>(GetCharacterOwner());

    const FGameplayTag actualTag = acfChar->GetActionsComponent()->GetCurrentMovesetActionsTag();

    if (TryGetBestExecutionTag(actualTag, execMap, relDir, currentBestExec)) {
        return currentBestExec.AnimationTag;
    }

    if (TryGetBestExecutionTag(actualTag, execMap, ERelativeDirection::EAny, currentBestExec)) {
        return currentBestExec.AnimationTag;
    }

    return FGameplayTag();
}

bool UACFExecutorComponent::TryGetBestExecutionTag(const FGameplayTag& actualTag, const TMap<ERelativeDirection, FExecutions>& execMap,
    ERelativeDirection dir, FExecution& outExec)
{
    if (execMap.Contains(dir)) {

        const FExecutions exec = execMap.FindChecked(dir);
        if (exec.ExecutionsByMovesetAction.Contains(actualTag)) {

            const FExecutionArray array = exec.ExecutionsByMovesetAction.FindChecked(actualTag);
     

            TArray<float> outWeights;
            for (int32 i = 0; i < array.ExecutionTag.Num(); ++i) {
                outWeights.Add(array.ExecutionTag[i].Weight);
            }
            const int32 index = UACFFunctionLibrary::ExtractIndexWithProbability(outWeights);
  
            if (array.ExecutionTag.IsValidIndex(index)) {
                outExec = array.ExecutionTag[index];
                return true;
            }
        }
    }
    return false;
}

void UACFExecutorComponent::SetCharacterActionsLock(ACharacter* target, bool lockstatus, bool canBeHit)
{
    if (target) {
        AACFCharacter* acfChar = Cast<AACFCharacter>(target);
        if (acfChar) {
            if (lockstatus) {
                acfChar->SetIsImmortal(!canBeHit) ;
            } else {
                acfChar->SetIsImmortal(false);
            }
        }
        UACFAbilitySystemComponent* actionComp = target->FindComponentByClass<UACFAbilitySystemComponent>();
        if (actionComp) {
            if (lockstatus) {
                actionComp->LockActionsTrigger();
            } else {
                actionComp->UnlockActionsTrigger();
            }
        }
    }
}
