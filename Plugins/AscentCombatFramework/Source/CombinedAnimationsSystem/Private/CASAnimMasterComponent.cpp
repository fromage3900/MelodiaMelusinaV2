// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "CASAnimMasterComponent.h"
#include "Animation/AnimMontage.h"
#include "Animation/AnimSequence.h"
#include "CASAnimSlaveComponent.h"
#include "CASTypes.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/Character.h"
#include "Kismet/KismetSystemLibrary.h"
#include "MotionWarpingComponent.h"
#include "Net/UnrealNetwork.h"
#include "RootMotionModifier.h"
#include "RootMotionModifier_SkewWarp.h"
#include <Animation/AnimInstance.h>
#include <Kismet/KismetMathLibrary.h>

// Sets default values for this component's properties
UCASAnimMasterComponent::UCASAnimMasterComponent()
{
    // Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
    // off to improve performance if you don't need them.
    PrimaryComponentTick.bCanEverTick = false;
    SetIsReplicatedByDefault(true);
    WarpSyncPoint = "WarpPoint";
    // ...
}

void UCASAnimMasterComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    //

    DOREPLIFETIME(UCASAnimMasterComponent, bIsPlayingCombAnim);
    DOREPLIFETIME(UCASAnimMasterComponent, currentAnim);
}

bool UCASAnimMasterComponent::TryPlayCombinedAnimation(ACharacter* otherCharachter, const FGameplayTag& combineAnimTag)
{
    if (!CanPlayCombinedAnimWithCharacter(otherCharachter, combineAnimTag)) {
        return false;
    }

    PlayCombinedAnimation(otherCharachter, combineAnimTag);
    return true;
}

void UCASAnimMasterComponent::PlayCombinedAnimation_Implementation(class ACharacter* otherCharachter, const FGameplayTag& combineAnimTag)
{
    const FCombinedAnimsMaster* animConfig = GetCombinedAnimTag(combineAnimTag);

    UMotionWarpingComponent* warpComponent = characterOwner->FindComponentByClass<UMotionWarpingComponent>();
    if (animConfig && animConfig->MasterAnimMontage && warpComponent) {
        currentAnim = FCurrentCombinedAnim(*animConfig, combineAnimTag, otherCharachter);

        StartAnim();

        bIsPlayingCombAnim = true;
        return;
    }
}

bool UCASAnimMasterComponent::PlayCombinedAnimation_Validate(class ACharacter* otherCharachter, const FGameplayTag& combineAnimTag)
{
    return true;
}

bool UCASAnimMasterComponent::CanPlayCombinedAnimWithCharacter(ACharacter* otherCharachter, const FGameplayTag& combineAnimTag)
{
    if (bIsPlayingCombAnim || !otherCharachter || !IsValid(otherCharachter)) {
        return false;
    }

    if (combineAnimTag == FGameplayTag()) {
        return false;
    }

    if (!MasterAnimsConfig) {
        UE_LOG(LogTemp, Warning, TEXT("NO Anim Data Table! -UCASAnimMasterComponent::TryPlayCombinedAnimation "));
        return false;
    }

    FCombinedAnimsMaster* animConfig = GetCombinedAnimTag(combineAnimTag);

    UCASAnimSlaveComponent* slaveComp = otherCharachter->FindComponentByClass<UCASAnimSlaveComponent>();
    if (!slaveComp || !animConfig) {
        return false;
    }

    if (!slaveComp->CanStartCombinedAnimation(combineAnimTag, GetCharacterOwner()) || !EvaluateCombinedAnim(*animConfig, otherCharachter)) {
        return false;
    }

    UMotionWarpingComponent* warpComponent = characterOwner->FindComponentByClass<UMotionWarpingComponent>();
    return (animConfig->MasterAnimMontage && warpComponent);
}

void UCASAnimMasterComponent::MulticastPlayAnimMontage_Implementation(const FCurrentCombinedAnim& combinedAnim)
{
    Internal_PlayMontageWithWarp(combinedAnim);
    return;
}

bool UCASAnimMasterComponent::MulticastPlayAnimMontage_Validate(const FCurrentCombinedAnim& combinedAnim)
{
    return true;
}

void UCASAnimMasterComponent::MulticastSlavePlayAnimMontage_Implementation(ACharacter* slave, UAnimMontage* montage)
{
    if (slave) {
        if (characterOwner && characterOwner->GetMesh() && slave->GetMesh()) {
            currentAnimScale = slave->GetMesh()->GlobalAnimRateScale;
            slave->GetMesh()->GlobalAnimRateScale = characterOwner->GetMesh()->GlobalAnimRateScale;
        }
        slave->PlayAnimMontage(montage);
    }
}

bool UCASAnimMasterComponent::MulticastSlavePlayAnimMontage_Validate(ACharacter* slave, UAnimMontage* montage)
{
    return IsValid(slave);
}

FCombinedAnimsMaster* UCASAnimMasterComponent::GetCombinedAnimTag(const FGameplayTag& combineAnimTag)
{
    const auto anims = MasterAnimsConfig->GetRowMap();
    for (const auto& anim : anims) {
        FCombinedAnimsMaster* currConfig = (FCombinedAnimsMaster*)anim.Value;
        if (currConfig && currConfig->AnimTag == combineAnimTag) {
            return currConfig;
        }
    }
    return nullptr;
}

// Called when the game starts
void UCASAnimMasterComponent::BeginPlay()
{
    Super::BeginPlay();

    characterOwner = Cast<ACharacter>(GetOwner());
}

bool UCASAnimMasterComponent::EvaluateCombinedAnim(const FCombinedAnimsMaster& animConfig, const ACharacter* otherChar) const
{
    return animConfig.MasterAnimMontage != nullptr && characterOwner->GetDistanceTo(otherChar) <= animConfig.MaxDistanceToStartWarping && (animConfig.SlaveRequiredDirection == GetCharacterRelativedDirection(otherChar) || animConfig.SlaveRequiredDirection == ERelativeDirection::EAny);
}

void UCASAnimMasterComponent::OnCombinedAnimStarted(const FGameplayTag& animTag)
{
}

void UCASAnimMasterComponent::OnCombinedAnimEnded(const FGameplayTag& animTag)
{
}

ERelativeDirection UCASAnimMasterComponent::GetCharacterRelativedDirection(const ACharacter* otherChar) const
{
    if (!otherChar || !characterOwner) {
        return ERelativeDirection::EAny;
    }

    const FVector masterRelative = characterOwner->GetActorLocation()
        - otherChar->GetActorLocation();

    const FVector relativeNormalized = masterRelative.GetUnsafeNormal();

    const float forwardDot = FVector::DotProduct(otherChar->GetActorForwardVector(), relativeNormalized);
    const float rightDot = FVector::DotProduct(otherChar->GetActorRightVector(), relativeNormalized);
    if (forwardDot >= 0.707f || rightDot >= 0.707f || rightDot <= -0.707f) {
        return ERelativeDirection::EFrontal;
    } else {
        return ERelativeDirection::EOpposite;
    }
}

void UCASAnimMasterComponent::HandleMontageFinished(UAnimMontage* inMontage, bool bInterruptted)
{
    if (currentAnim.MasterAnimConfig.MasterAnimMontage == inMontage) {
        ServerCombinedAnimationEnded.Broadcast(currentAnim.AnimTag);
        DispatchAnimEnded(currentAnim.AnimTag);

        UAnimInstance* animinst = (characterOwner->GetMesh()->GetAnimInstance());

        if (animinst) {
            animinst->OnMontageBlendingOut.RemoveDynamic(this, &UCASAnimMasterComponent::HandleMontageFinished);
        }
        if (currentAnim.AnimSlave) {
            if (currentAnim.AnimSlave->GetMesh()) {
                currentAnim.AnimSlave->GetMesh()->GlobalAnimRateScale = currentAnimScale;
            }

            const UCASAnimSlaveComponent* slaveComp = currentAnim.AnimSlave->FindComponentByClass<UCASAnimSlaveComponent>();
            if (slaveComp) {
                slaveComp->OnCombinedAnimationEnded.Broadcast(currentAnim.AnimTag);
            }
        }
        bIsPlayingCombAnim = false;
    }
}

void UCASAnimMasterComponent::StartAnim()
{
    UAnimInstance* animinst = (characterOwner->GetMesh()->GetAnimInstance());
    if (animinst && currentAnim.AnimSlave && currentAnim.MasterAnimConfig.MasterAnimMontage) {
        animinst->OnMontageBlendingOut.AddDynamic(this, &UCASAnimMasterComponent::HandleMontageFinished);
        const ACharacter* otherCharacter = currentAnim.AnimSlave;
        const float distance = characterOwner->GetDistanceTo(otherCharacter);

        const FVector otheractorLoc = otherCharacter->GetActorLocation();
        FRotator warpRotation = UKismetMathLibrary::FindLookAtRotation(characterOwner->GetActorLocation(), otheractorLoc);
        warpRotation.Pitch = 0.f;
        warpRotation.Roll = 0.f;

        currentAnim.WarpTransform = FTransform(warpRotation, otheractorLoc);
        MulticastPlayAnimMontage(currentAnim);
        StartAnimOnSlave();
        ServerCombinedAnimationStarted.Broadcast(currentAnim.AnimTag);
        DispatchAnimStarted(currentAnim.AnimTag);
    }
}

void UCASAnimMasterComponent::StartAnimOnSlave()
{
    if (currentAnim.AnimSlave) {
        const UCASAnimSlaveComponent* slaveComp = currentAnim.AnimSlave->FindComponentByClass<UCASAnimSlaveComponent>();

        FCombinedAnimsSlave outAnim;
        if (slaveComp->TryGetSlaveAnim(currentAnim.AnimTag, outAnim) && outAnim.MasterAnimMontage) {
            FRotator rotation = currentAnim.AnimSlave->GetActorRotation();

            switch (currentAnim.MasterAnimConfig.SlaveForcedDirection) {
            case ERelativeDirection::EFrontal:
                rotation = UKismetMathLibrary::FindLookAtRotation(currentAnim.AnimSlave->GetActorLocation(), characterOwner->GetActorLocation());
                break;
            case ERelativeDirection::EOpposite:
                rotation = UKismetMathLibrary::FindLookAtRotation(characterOwner->GetActorLocation(), currentAnim.AnimSlave->GetActorLocation());
                break;
            case ERelativeDirection::EAny:
            default:
                break;
            }

            currentAnim.AnimSlave->SetActorRotation(rotation);

            MulticastSlavePlayAnimMontage(currentAnim.AnimSlave, outAnim.MasterAnimMontage);
            slaveComp->OnCombinedAnimationStarted.Broadcast(currentAnim.AnimTag);
        } else {
            bIsPlayingCombAnim = false;
        }
    }
}

void UCASAnimMasterComponent::DispatchAnimStarted_Implementation(const FGameplayTag& animTag)
{
    OnCombinedAnimationStarted.Broadcast(animTag);
    OnCombinedAnimStarted(animTag);
}

bool UCASAnimMasterComponent::DispatchAnimStarted_Validate(const FGameplayTag& animTag)
{
    return true;
}

void UCASAnimMasterComponent::DispatchAnimEnded_Implementation(const FGameplayTag& animTag)
{
    OnCombinedAnimationEnded.Broadcast(animTag);
    OnCombinedAnimEnded(animTag);
}

bool UCASAnimMasterComponent::DispatchAnimEnded_Validate(const FGameplayTag& animTag)
{
    return true;
}

void UCASAnimMasterComponent::Internal_PlayMontageWithWarp(const FCurrentCombinedAnim& combinedAnim)
{
    if (!characterOwner) {
        return;
    }

    UMotionWarpingComponent* motionComp = characterOwner->FindComponentByClass<UMotionWarpingComponent>();

    const FMotionWarpingTarget newTarget = FMotionWarpingTarget(WarpSyncPoint, combinedAnim.WarpTransform);
    motionComp->AddOrUpdateWarpTarget(newTarget);

    URootMotionModifier_SkewWarp::AddRootMotionModifierSkewWarp(motionComp, combinedAnim.MasterAnimConfig.MasterAnimMontage,
        0.0f,
        combinedAnim.MasterAnimConfig.WarpTime, WarpSyncPoint,
        EWarpPointAnimProvider::None, currentAnim.WarpTransform, NAME_None, true, true, true,
        EMotionWarpRotationType::Facing, EMotionWarpRotationMethod::Slerp, combinedAnim.MasterAnimConfig.WarpRotationTimeMultiplier);
    characterOwner->PlayAnimMontage(combinedAnim.MasterAnimConfig.MasterAnimMontage);
}

FVector UCASAnimMasterComponent::GetPointAtDirectionAndDistanceFromActor(const AActor* targetActor, const FVector& direction, float distance, bool bShowDebug /*= false*/)
{
    if (!targetActor) {
        return FVector();
    }
    const FVector actorLoc = targetActor->GetActorLocation();
    FVector normalizedDir = direction;

    normalizedDir.Normalize();
    FVector targetPos = actorLoc + (normalizedDir * distance);
    targetPos.Z = targetActor->GetActorLocation().Z;

    if (bShowDebug) {
        UKismetSystemLibrary::DrawDebugSphere(targetActor, targetPos, 50.f, 12, FLinearColor::Yellow, 10.f, 1.f);
    }

    return targetPos;
}
