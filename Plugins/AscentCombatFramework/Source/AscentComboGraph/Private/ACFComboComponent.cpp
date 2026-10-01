// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFComboComponent.h"
#include "Components/ACFAbilitySystemComponent.h"
#include "Graph/ACFComboGraph.h"
#include <EnhancedInputComponent.h>
#include <EnhancedPlayerInput.h>
#include <InputAction.h>
#include <Net/UnrealNetwork.h>
#include <UObject/CoreNet.h>

// Sets default values for this component's properties
UACFComboComponent::UACFComboComponent()
{
    // Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
    // off to improve performance if you don't need them.
    PrimaryComponentTick.bCanEverTick = false;
    SetIsReplicatedByDefault(true);
    bIsInputBufferEnabled = false;
    bIsPerformingCombo = false;
    // ...
}

void UACFComboComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(UACFComboComponent, LastTagInput);
    DOREPLIFETIME(UACFComboComponent, bIsPerformingCombo);
}

void UACFComboComponent::StartCombo(UACFComboGraph* comboToStart, const FGameplayTag& triggeringAction)
{
    if (IsExecutingAnyCombo()) {
        StopCurrentCombo();
    }
    if (comboToStart) {
        FActionState action;
        if (actionsComp->GetAbilityByTag(triggeringAction)) {
            // Duplicate the asset so each character has its own independent graph state
            currentCombo = DuplicateObject(comboToStart, GetOwner());
            currentCombo->SetCharacterOwner(Cast<ACharacter>(GetOwner()));
            currentCombo->StartCombo(triggeringAction);
            bIsPerformingCombo = currentCombo->IsActive();
        }
    }
}

void UACFComboComponent::StopCombo(UACFComboGraph* comboToStop)
{
    // Compare by class: currentCombo is a DuplicateObject of comboToStop (same class, different pointer)
    if (currentCombo && comboToStop && currentCombo->GetClass() == comboToStop->GetClass()) {
        StopCurrentCombo();
    }
}

void UACFComboComponent::SetInputBufferOpened(bool bEnabled)
{
    bIsInputBufferEnabled = bEnabled;
}

bool UACFComboComponent::IsExecutingCombo(UACFComboGraph* combo) const
{
    // Compare by class: currentCombo is a DuplicateObject of the source asset (same class, different pointer)
    return IsExecutingAnyCombo() && currentCombo && combo && currentCombo->GetClass() == combo->GetClass();
}

bool UACFComboComponent::IsExecutingAnyCombo() const
{
    return bIsPerformingCombo;
}

// Called when the game starts
void UACFComboComponent::BeginPlay()
{
    Super::BeginPlay();

    actionsComp = GetOwner()->FindComponentByClass<UACFAbilitySystemComponent>();
    if (!actionsComp) {
        UE_LOG(LogTemp, Error, TEXT("Missing ACTIONS Comp!  - UACFComboComponent"));
    }
}

void UACFComboComponent::SetupPlayerInputComponent(UEnhancedInputComponent* EnhancedInputComponent)
{
    if (EnhancedInputComponent != nullptr) {
        for (const TPair<UInputAction*, FGameplayTag>& Pair : ComboInputs) {
            UInputAction* input = Pair.Key;

            EnhancedInputComponent->BindAction(input, ETriggerEvent::Started, this,
                &UACFComboComponent::HandleComboInputReceived, input);
        }
    } else {
        UE_LOG(LogTemp, Warning, TEXT("Missing Enhanced Input Comp!  - UACFComboComponent"));
    }
}

void UACFComboComponent::HandleComboInputReceived(UInputAction* input)
{
    const FGameplayTag* foundTag = ComboInputs.Find(input);
    // pre setting it locally to avoid network delays, server check will eventually rollback it in
    // ability end
    // checking also is another input have been sent to avoid spamming
    if (foundTag && GetLastTagInput() != *foundTag && Internal_InputReceived(*foundTag)) {

        SendInputReceived(*foundTag);
    }
}

void UACFComboComponent::SendInputReceived_Implementation(const FGameplayTag& tagInput)
{
    Internal_InputReceived(tagInput);
}

void UACFComboComponent::ClearInputTag()
{
    LastTagInput = FGameplayTag();
}

void UACFComboComponent::StopCurrentCombo()
{
    Internal_StopCombo(); // Sempre sul server

    // Notifica l'owner client di fermare la combo (solo se non siamo in single player)
    if (GetOwner()->GetNetMode() != NM_Standalone && !GetOwner()->HasLocalNetOwner()) {
        ClientStopCombo();
    }
}

void UACFComboComponent::Internal_StopCombo()
{
    if (currentCombo) {
        currentCombo->StopCombo();
        currentCombo = nullptr;
        bIsPerformingCombo = false;
        ClearInputTag();
    }
}

bool UACFComboComponent::Internal_InputReceived(const FGameplayTag& tagInput)
{
    if (bIsPerformingCombo && bIsInputBufferEnabled && currentCombo) {
        LastTagInput = tagInput; // Handle player input
        return true;
    }
    return false;
}

void UACFComboComponent::ClientStopCombo_Implementation()
{
    Internal_StopCombo();
}
