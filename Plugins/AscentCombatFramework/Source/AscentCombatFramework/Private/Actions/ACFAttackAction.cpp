// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Actions/ACFAttackAction.h"
#include "ATSBaseTargetComponent.h"
#include "ATSTargetPointComponent.h"
#include "Actions/ACFActionAbility.h"
#include "Actors/ACFCharacter.h"
#include "Animation/ACFAnimInstance.h"
#include "Components/ACFAbilitySystemComponent.h"
#include "Components/ACFCharacterMovementComponent.h"
#include "Components/ActorComponent.h"
#include "Game/ACFFunctionLibrary.h"
#include "Interfaces/ACFEntityInterface.h"
#include "Kismet/KismetSystemLibrary.h"
#include "MotionWarpingComponent.h"
#include "RootMotionModifier.h"
#include <ATSBaseTargetComponent.h>
#include <GameFramework/Actor.h>
#include <GameFramework/CharacterMovementComponent.h>
#include <GameFramework/Controller.h>
#include <Kismet/KismetMathLibrary.h>

UACFAttackAction::UACFAttackAction()
{
    ActionConfig.MontageReproductionType = EMontageReproductionType::EMotionWarped;
}

void UACFAttackAction::ActivateAbility(const FGameplayAbilitySpecHandle Handle, const FGameplayAbilityActorInfo* ActorInfo,
    const FGameplayAbilityActivationInfo ActivationInfo, const FGameplayEventData* TriggerEventData)
{
    SetupAttack();
    Super::ActivateAbility(Handle, ActorInfo, ActivationInfo, TriggerEventData);
}

void UACFAttackAction::SetupAttack()
{
    storedReproType = ActionConfig.MontageReproductionType;
    if (GetCharacterOwner() && bCheckWarpConditions && GetCharacterOwner()->GetController() && ActionConfig.MontageReproductionType == EMontageReproductionType::EMotionWarped) {
        const UMotionWarpingComponent* motionComp = GetCharacterOwner()->FindComponentByClass<UMotionWarpingComponent>();
        const UATSBaseTargetComponent* targetComp = GetCharacterOwner()->GetController()->FindComponentByClass<UATSBaseTargetComponent>();
        if (motionComp && targetComp && animMontage) {
            AActor* target = targetComp->GetCurrentTarget();
            IACFEntityInterface* entity = Cast<IACFEntityInterface>(target);
            IACFEntityInterface* ownerEntity = Cast<IACFEntityInterface>(GetCharacterOwner());
            if (target && entity && GetCharacterOwner()) {
                const float entityExtent = IACFEntityInterface::Execute_GetEntityExtentRadius(target);
                // const float ownerExtent = IACFEntityInterface::Execute_GetEntityExtentRadius(GetCharacterOwner());

                FVector ownerLoc = GetCharacterOwner()->GetActorLocation();
                ownerLoc.Z = target->GetActorLocation().Z;
                const FVector diffVector = target->GetActorLocation() - ownerLoc;

                const float distance = GetCharacterOwner()->GetDistanceTo(target);

                const float warpDistance = distance - entityExtent; //- ownerExtent;
                const FVector finalPos = UACFFunctionLibrary::GetPointAtDirectionAndDistanceFromActor(GetCharacterOwner(), diffVector, warpDistance, ActionConfig.WarpInfo.bShowWarpDebug);

                FRotator finalRot = UKismetMathLibrary::FindLookAtRotation(GetCharacterOwner()->GetActorLocation(), target->GetActorLocation());
                finalRot.Pitch = 0.f;
                finalRot.Roll = 0.f;
                const FRotator deltaRot = finalRot - GetCharacterOwner()->GetActorForwardVector().Rotation();
                if (maxWarpDistance > warpDistance
                    && warpDistance > minWarpDistance
                    && maxWarpAngle > FMath::Abs(deltaRot.Yaw)) {

                    warpTrans = FTransform(finalRot, finalPos);

                    currentTargetComp = targetComp->GetCurrentTargetPoint();
                    SetMontageReproductionType(EMontageReproductionType::EMotionWarped);
                } else {
                    SetMontageReproductionType(EMontageReproductionType::ERootMotion);
                }
            } else {
                SetMontageReproductionType(EMontageReproductionType::ERootMotion);
            }
        }
    }
}

bool UACFAttackAction::TryGetTransform(FTransform& outTranform) const
{
    if (!IsValid(GetCharacterOwner()) || !IsValid(GetCharacterOwner()->GetController())) {
        return false;
    }
    const UATSBaseTargetComponent* targetComp = GetCharacterOwner()->GetController()->FindComponentByClass<UATSBaseTargetComponent>();
    if (targetComp) {
        AActor* target = targetComp->GetCurrentTarget();

        if (target) {
            const float entityExtent = IACFEntityInterface::Execute_GetEntityExtentRadius(target);
            // const float ownerExtent = IACFEntityInterface::Execute_GetEntityExtentRadius(GetCharacterOwner());

            FVector ownerLoc = GetCharacterOwner()->GetActorLocation();
            ownerLoc.Z = target->GetActorLocation().Z;
            const FVector diffVector = target->GetActorLocation() - ownerLoc;

            const float distance = GetCharacterOwner()->GetDistanceTo(target);

            const float warpDistance = distance - entityExtent; // - ownerExtent;
            const FVector finalPos = UACFFunctionLibrary::GetPointAtDirectionAndDistanceFromActor(GetCharacterOwner(), diffVector, warpDistance, false);

            FRotator finalRot = UKismetMathLibrary::FindLookAtRotation(GetCharacterOwner()->GetActorLocation(), finalPos);
            finalRot.Roll = 0.f;
            finalRot.Pitch = 0.f;
            outTranform = FTransform(finalRot, finalPos);
            return true;
        }
    }
    return false;
}


USceneComponent* UACFAttackAction::GetWarpTargetComponent_Implementation()
{
    return currentTargetComp;
}

FTransform UACFAttackAction::GetWarpTransform_Implementation()
{
    return warpTrans;
}

void UACFAttackAction::OnActionStarted_Implementation()
{

    Super::OnActionStarted_Implementation();
}

void UACFAttackAction::OnActionEnded_Implementation()
{

    AACFCharacter* acfCharacter = Cast<AACFCharacter>(GetCharacterOwner());

    ActionConfig.MontageReproductionType = storedReproType;

    Super::OnActionEnded_Implementation();
}

