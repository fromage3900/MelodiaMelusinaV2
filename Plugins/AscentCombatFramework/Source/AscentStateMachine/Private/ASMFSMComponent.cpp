// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ASMFSMComponent.h"
#include "ASMBaseFSMState.h"
#include "Net/UnrealNetwork.h"

// Sets default values for this component's properties
UASMFSMComponent::UASMFSMComponent()
{
    // Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
    // off to improve performance if you don't need them.
    PrimaryComponentTick.bCanEverTick = true;
    SetIsReplicatedByDefault(true);
}

// Called when the game starts
void UASMFSMComponent::BeginPlay()
{
    Super::BeginPlay();
//     if (StateMachine) {
//         FSM = DuplicateObject<UASMStateMachine>(StateMachine, GetOuter());
//     }
}

void UASMFSMComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    Super::EndPlay(EndPlayReason);

    if (StateMachine) {
        StateMachine->StopFSM();
    }
}

// void UASMFSMComponent::GetLifetimeReplicatedProps(TArray< FLifetimeProperty >& OutLifetimeProps) const
// {
// 	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
//
// }

void UASMFSMComponent::TickComponent(float DeltaTime, enum ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

    if (StateMachine && StateMachine->IsActive()) {
        StateMachine->DispatchTick(DeltaTime);
        if (pendingTransition != FGameplayTag()) {
            StateMachine->TriggerTransition(pendingTransition);
            pendingTransition = FGameplayTag();
        }
    }
}

void UASMFSMComponent::PostInitProperties()
{
    Super::PostInitProperties();

    SetComponentTickEnabled(true);
}

void UASMFSMComponent::StartFSM()
{
    if (StateMachine) {
        StateMachine->StartFSM(GetOwner(), bShouldDisplayDebugInfo);
    } else {
        UE_LOG(LogTemp, Error, TEXT("Invalid State Machine - UASMFSMComponent::StartFSM"));
    }
}

void UASMFSMComponent::StopFSM()
{
    if (StateMachine) {
        StateMachine->StopFSM();
    } else {
        UE_LOG(LogTemp, Error, TEXT("Invalid State Machine - UASMFSMComponent::StopFSM"));
    }
}

void UASMFSMComponent::TriggerTransition(const FGameplayTag& transition)
{
    pendingTransition = transition;
}

void UASMFSMComponent::ClientTriggerTransition_Implementation(const FGameplayTag& transition)
{
    TriggerTransition(transition);
}

bool UASMFSMComponent::ClientTriggerTransition_Validate(const FGameplayTag& transition)
{
    return true;
}

FName UASMFSMComponent::GetCurrentStateName() const
{
    if (StateMachine) {
        return StateMachine->GetCurrentStateName();
    } else {
        UE_LOG(LogTemp, Error, TEXT("Invalid State Machine - UASMFSMComponent::GetCurrentStateName"));
    }
    return NAME_None;
}

UASMBaseFSMState* UASMFSMComponent::GetCurrentState() const
{
    if (StateMachine) {
        return StateMachine->GetCurrentState();
    } else {
        UE_LOG(LogTemp, Error, TEXT("Invalid State Machine - UASMFSMComponent::GetCurrentState"));
    }
    return nullptr;
}

void UASMFSMComponent::SetFsmTickEnabled(bool bIsEnabled)
{
    bCanFsmTick = bIsEnabled;
}

void UASMFSMComponent::SynchedStopFSM_Implementation()
{
    Internal_SynchedStop();
}


void UASMFSMComponent::SynchedStartFSM_Implementation()
{
    Internal_SynchedStart();
}



void UASMFSMComponent::SynchedTriggerTransition_Implementation(const FGameplayTag& transition)
{
    Internal_SynchedTriggerTransition(transition);
}


void UASMFSMComponent::Internal_SynchedTriggerTransition_Implementation(const FGameplayTag& transition)
{
    TriggerTransition(transition);
}

void UASMFSMComponent::Internal_SynchedStart_Implementation()
{
    StartFSM();
}



void UASMFSMComponent::Internal_SynchedStop_Implementation()
{
    StopFSM();
}

