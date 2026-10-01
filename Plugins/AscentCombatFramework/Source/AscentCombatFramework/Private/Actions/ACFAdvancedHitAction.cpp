// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Actions/ACFAdvancedHitAction.h"
#include "ACFActionsFunctionLibrary.h"
#include "Actions/ACFActionAbility.h"
#include "Actors/ACFCharacter.h"
#include "Animation/ACFAnimInstance.h"
#include "Components/ACFAbilitySystemComponent.h"
#include "Components/ACFCharacterMovementComponent.h"
#include "Game/ACFFunctionLibrary.h"
#include "Kismet/KismetMathLibrary.h"

UACFAdvancedHitAction::UACFAdvancedHitAction()
{
    HitDirectionToMontageSectionMap.Add(EHitDirection::EFront, FName("Front"));
    HitDirectionToMontageSectionMap.Add(EHitDirection::EBack, FName("Back"));
    HitDirectionToMontageSectionMap.Add(EHitDirection::ERight, FName("Right"));
    HitDirectionToMontageSectionMap.Add(EHitDirection::ELeft, FName("Left"));
    ActionConfig.bStopBehavioralThree = true;
    ActionConfig.MontageReproductionType = EMontageReproductionType::EMotionWarped;
    NetExecutionPolicy = EGameplayAbilityNetExecutionPolicy::LocalPredicted;
}

FTransform UACFAdvancedHitAction::GetWarpTransform_Implementation()
{
    FVector location = GetCharacterOwner()->GetActorLocation();
    FRotator rot = GetCharacterOwner()->GetActorForwardVector().Rotation();

    if ( animMontage) {
        
        const FVector damageMomentum = UACFFunctionLibrary::GetActorsRelativeDirectionVector(CharacterOwner, StoredPayload.TargetActor );
        
        if (!damageMomentum.IsNearlyZero()) {
            const FVector offset = damageMomentum * hitWarpDistance;
            location += offset;
        }

        if (StoredPayload.TargetActor) {
            rot = UKismetMathLibrary::FindLookAtRotation(location, StoredPayload.TargetActor->GetActorLocation());
        }

        rot.Pitch = 0.f;
        rot.Roll = 0.f;
    }

    return FTransform(rot, location, FVector(1.f));
}

void UACFAdvancedHitAction::OnActionStarted_Implementation()
{
    Super::OnActionStarted_Implementation();

    AACFCharacter* acfCharacter = Cast<AACFCharacter>(GetCharacterOwner());

    if (acfCharacter) {
        UACFAbilitySystemComponent* actionsMan = acfCharacter->GetActionsComponent();
        if (actionsMan) {
            // Cleans the input buffer when staggered
            actionsMan->StoreAbilityInBuffer(FGameplayTag());
        }
    }
}

void UACFAdvancedHitAction::OnActionEnded_Implementation()
{
    Super::OnActionEnded_Implementation();
}

FName UACFAdvancedHitAction::GetMontageSectionName_Implementation()
{
    if (!HasValidPayload()) {
		return Super::GetMontageSectionName_Implementation();
    }
    const EACFDirection direction =   UACFFunctionLibrary::GetHitDirectionByHitResult(GetTriggerPayload().TargetActor, GetTriggerPayload().HitResult);

    switch (direction) {
    case EACFDirection::Front:
        return GetMontageSectionFromFront(GetTriggerPayload().HitResult);
    case EACFDirection::Back:
        return GetMontageSectionFromHitDirectionSafe(EHitDirection::EBack);
    case EACFDirection::Left:
        return GetMontageSectionFromHitDirectionSafe(EHitDirection::ELeft);
    case EACFDirection::Right:
        return GetMontageSectionFromHitDirectionSafe(EHitDirection::ERight);
    }

    return GetMontageSectionFromHitDirectionSafe(EHitDirection::EFront);
}

FName UACFAdvancedHitAction::GetMontageSectionFromHitDirectionSafe(const EHitDirection hitDir) const
{
    const FName* section = HitDirectionToMontageSectionMap.Find(hitDir);

    if (section) {
        return *section;
    }

    return NAME_None;
}

FName UACFAdvancedHitAction::GetMontageSectionFromFront(const FHitResult& damageReceived) const
{
    const FName boneName = damageReceived.BoneName;

    for (const auto& section : FrontDetailsSectionByBoneNames) {
        if (section.BoneNames.Contains(boneName)) {
            return section.SectionName;
        }
    }

    return GetMontageSectionFromHitDirectionSafe(EHitDirection::EFront);
}
