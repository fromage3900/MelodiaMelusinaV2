// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Components/ACFInputComponent.h"
#include "ACFInputConfigDataAsset.h"
#include "AbilitySystemComponent.h"
#include "AbilitySystemGlobals.h"
#include "Engine/LocalPlayer.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "GameplayAbilitySpec.h"
#include "InputMappingContext.h"
#include <GameFramework/PlayerState.h>
#include <AbilitySystemInterface.h>
#include "ACFActionTypes.h"
#include <GameplayAbilitySpecHandle.h>
#include <Engine/World.h>
#include <TimerManager.h>

UACFInputComponent::UACFInputComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
}

void UACFInputComponent::BeginPlay()
{
    Super::BeginPlay();

    // Bind to controller change events if we're on a Pawn
    APawn* PawnOwner = Cast<APawn>(GetOwner());
    if (PawnOwner) {
        PawnOwner->ReceiveControllerChangedDelegate.AddDynamic(this, &UACFInputComponent::OnControllerChanged);

        /*
        if (PawnOwner->GetController()) {
            // Setup input after a short delay to ensure everything is initialized
            GetWorld()->GetTimerManager().SetTimer(SetupTimerHandle, this, &UACFInputComponent::SetupInputBindings, 0.1f, false);
        }*/
    }
}

void UACFInputComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    // Clean up timer if active
    if (SetupTimerHandle.IsValid()) {
        GetWorld()->GetTimerManager().ClearTimer(SetupTimerHandle);
    }

    // Clean up bindings
    CleanupInputBindings();

    // Unbind from controller change events
    APawn* PawnOwner = Cast<APawn>(GetOwner());
    if (PawnOwner) {
        PawnOwner->ReceiveControllerChangedDelegate.RemoveDynamic(this, &UACFInputComponent::OnControllerChanged);
    }

    Super::EndPlay(EndPlayReason);
}

void UACFInputComponent::OnControllerChanged(APawn* Pawn, AController* OldController, AController* NewController)
{
    // Clean up old bindings
    CleanupInputBindings();

    // If we have a new controller, setup new bindings
    if (NewController) {
        // Small delay to ensure the controller is fully set up
        GetWorld()->GetTimerManager().SetTimer(SetupTimerHandle, this, &UACFInputComponent::SetupInputBindings, 0.1f, false);
    }
}

void UACFInputComponent::CleanupInputBindings()
{
    // Clear existing action bindings
    if (EnhancedInputComponent) {
        EnhancedInputComponent->ClearActionBindings();
    }

    // Clear active ability handles
    ActiveAbilityHandles.Empty();

    // Reset component references
    EnhancedInputComponent = nullptr;
    AbilitySystemComponent = nullptr;
}

void UACFInputComponent::SetupInputBindings()
{
    if (!InputConfigDataAsset) {
        UE_LOG(LogTemp, Warning, TEXT("ACFInputComponent: InputConfigDataAsset not configured"));
        return;
    }

    AActor* Owner = GetOwner();
    if (!Owner) {
        UE_LOG(LogTemp, Warning, TEXT("ACFInputComponent: Owner not found"));
        return;
    }

    // Find the PlayerController
    APawn* Pawn = Cast<APawn>(Owner);
    if (!Pawn) {
        UE_LOG(LogTemp, Warning, TEXT("ACFInputComponent: Owner is not a Pawn"));
        return;
    }

    APlayerController* PlayerController = Cast<APlayerController>(Pawn->GetController());
    if (!PlayerController) {
        UE_LOG(LogTemp, Warning, TEXT("ACFInputComponent: PlayerController not found"));
        return;
    }

    // Get the Enhanced Input Component
    EnhancedInputComponent = Cast<UEnhancedInputComponent>(PlayerController->InputComponent);
    if (!EnhancedInputComponent) {
        UE_LOG(LogTemp, Warning, TEXT("ACFInputComponent: Enhanced Input Component not found"));
        return;
    }

    // Get the Ability System Component
    AbilitySystemComponent = GetAbilitySystemComponent();
    if (!AbilitySystemComponent) {
        UE_LOG(LogTemp, Warning, TEXT("ACFInputComponent: Ability System Component not found"));
        return;
    }


    // Get bindings sorted by priority
    TArray<FACFInputAbilityBinding> allBindings;
    InputConfigDataAsset->GetBindings(allBindings);

    // Bind each input action to its related ability
    for (const FACFInputAbilityBinding& Binding : allBindings) {
        if (Binding.EnhancedInputAction && Binding.AbilityTag.IsValid()) {
            // Binding for when key is pressed
            EnhancedInputComponent->BindAction(
                Binding.EnhancedInputAction,
                ETriggerEvent::Started,
                this,
                &UACFInputComponent::OnInputPressed,
                Binding.AbilityTag);

            // Binding for when key is released
            EnhancedInputComponent->BindAction(
                Binding.EnhancedInputAction,
                ETriggerEvent::Completed,
                this,
                &UACFInputComponent::OnInputReleased,
                Binding.AbilityTag);

        }
    }
}

void UACFInputComponent::OnInputPressed(FGameplayTag AbilityTag)
{
    if (!AbilitySystemComponent) {
        return;
    }

    // Find all abilities with the specified tag
    TArray<FGameplayAbilitySpec*> AbilitySpecs;
    AbilitySystemComponent->GetActivatableGameplayAbilitySpecsByAllMatchingTags(
        FGameplayTagContainer(AbilityTag),
        AbilitySpecs,
        false);

    // Activate the first ability found with the tag
    for (FGameplayAbilitySpec* Spec : AbilitySpecs) {
        if (Spec && Spec->Ability) {
            // Try to activate the ability
            bool bSuccess = AbilitySystemComponent->TryActivateAbility(Spec->Handle);

            if (bSuccess) {
                // Save the handle to potentially cancel it later
                ActiveAbilityHandles.Add(AbilityTag, Spec->Handle);

                UE_LOG(LogTemp, Log, TEXT("ACFInputComponent: Ability activated with tag %s"),
                    *AbilityTag.ToString());
            }

            break; // Activate only the first ability found
        }
    }
}

void UACFInputComponent::OnInputReleased(FGameplayTag AbilityTag)
{
    if (!AbilitySystemComponent) {
        return;
    }

    // If the ability requires being held down, cancel it on release
    if (FGameplayAbilitySpecHandle* Handle = ActiveAbilityHandles.Find(AbilityTag)) {
        // Check if the ability is still active
        FGameplayAbilitySpec* Spec = AbilitySystemComponent->FindAbilitySpecFromHandle(*Handle);
        if (Spec && Spec->IsActive()) {
            // Cancel the ability
            AbilitySystemComponent->CancelAbilityHandle(*Handle);

            UE_LOG(LogTemp, Log, TEXT("ACFInputComponent: Ability cancelled with tag %s"),
                *AbilityTag.ToString());
        }

        // Remove the handle from the map
        ActiveAbilityHandles.Remove(AbilityTag);
    }
}

UAbilitySystemComponent* UACFInputComponent::GetAbilitySystemComponent() const
{
    AActor* Owner = GetOwner();
    if (!Owner) {
        return nullptr;
    }

    // First try to see if the Owner has an AbilitySystemComponent directly
    UAbilitySystemComponent* ASC = Owner->FindComponentByClass<UAbilitySystemComponent>();
    if (ASC) {
        return ASC;
    }

    // Try with the PlayerState if the Owner is a Pawn
    APawn* Pawn = Cast<APawn>(Owner);
    if (Pawn) {
        APlayerState* PlayerState = Pawn->GetPlayerState();
        if (PlayerState && PlayerState->Implements<UAbilitySystemInterface>()) {
            return UAbilitySystemGlobals::GetAbilitySystemComponentFromActor(PlayerState);
        }
    }

    return nullptr;
}
