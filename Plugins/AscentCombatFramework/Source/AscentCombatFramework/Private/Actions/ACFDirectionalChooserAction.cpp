// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Actions/ACFDirectionalChooserAction.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Components/ACFAbilitySystemComponent.h"
#include "Chooser.h"
#include "ChooserFunctionLibrary.h"
#include "Animation/AnimMontage.h"
#include "Kismet/KismetMathLibrary.h"

UACFDirectionalChooserAction::UACFDirectionalChooserAction()
{
    bBindActionToAnimation = false;
    bAutoCommit = false;
    CachedInputDirection = 0.0f;

    // Create our tags wrapper
    TagsWrapper = CreateDefaultSubobject<UACFGameplayTagsWrapper>(TEXT("TagsWrapper"));
}

float UACFDirectionalChooserAction::GetInputDirection() const
{
    ACharacter* CurrentCharacter = GetCharacterOwner();

    if (!CurrentCharacter)
    {
        UE_LOG(LogTemp, Warning, TEXT("DirectionalAction: No valid character owner!"));
        return 0.0f;
    }

    // Get character movement component
    UCharacterMovementComponent* MovementComp = CurrentCharacter->GetCharacterMovement();
    if (!MovementComp)
    {
        UE_LOG(LogTemp, Warning, TEXT("DirectionalAction: No valid movement component!"));
        return 0.0f;
    }

    // Get the movement vector from velocity
    FVector MovementVector = MovementComp->Velocity;
    if (MovementVector.IsNearlyZero())
    {
        // If no velocity, use the acceleration
        MovementVector = MovementComp->GetCurrentAcceleration();
    }

    // If still no movement, return 0 (forward)
    if (MovementVector.IsNearlyZero())
    {
        UE_LOG(LogTemp, Verbose, TEXT("DirectionalAction: No movement detected"));
        return 0.0f;
    }

    // Project to horizontal plane and normalize
    MovementVector.Z = 0.0f;
    MovementVector.Normalize();

    // Get forward and right vectors of the character
    const FVector ForwardVector = CurrentCharacter->GetActorForwardVector();
    const FVector RightVector = CurrentCharacter->GetActorRightVector();

    // Calculate dot products
    const float ForwardDot = FVector::DotProduct(ForwardVector, MovementVector);
    const float RightDot = FVector::DotProduct(RightVector, MovementVector);

    // Calculate angle using atan2
    float Angle = FMath::RadiansToDegrees(FMath::Atan2(RightDot, ForwardDot));

    return Angle;
}

void UACFDirectionalChooserAction::SetChooserParams_Implementation()
{
    // Call parent implementation first
    Super::SetChooserParams_Implementation();

    // Update cached direction
    CachedInputDirection = GetInputDirection();

    // Create a new wrapper if needed
    if (!TagsWrapper)
    {
        TagsWrapper = NewObject<UACFGameplayTagsWrapper>(this);
    }

    // Update tags
    TagsWrapper->Tags = ChooserTags;
}
