// Copyright (C) Developed by Pask & insodimension, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Actions/ACFHitReactionChooserAction.h"
#include "Actions/ACFChooserAction.h"
#include "Actors/ACFCharacter.h"
#include "Components/ACFAbilitySystemComponent.h"
#include "Game/ACFFunctionLibrary.h"
#include "Kismet/KismetMathLibrary.h"
#include "GameFramework/CharacterMovementComponent.h"
// #include "Data/ACFBoneMapping.h" // Not available in this plugin

UACFHitReactionChooserAction::UACFHitReactionChooserAction()
{
    // Configure action settings
    ActionConfig.bStopBehavioralThree = true;
    ActionConfig.MontageReproductionType = EMontageReproductionType::EMotionWarped;

    // Set default zone for unmapped bones to Torso
    DefaultHitZone = FGameplayTag::RequestGameplayTag(FName("Hit.Zone.Torso"), false);

    // Default zone mappings for UE5 Mannequin/MetaHuman skeleton
    // Note: These are sensible defaults - designers should customize per character in Blueprint
    // ErrorIfNotFound=false allows tags to work even if not defined in GameplayTags.ini

    // Head zone - includes entire head, neck, and facial bones
    FHitZoneBoneMapping HeadZone;
    HeadZone.ZoneTag = FGameplayTag::RequestGameplayTag(FName("Hit.Zone.Head"), false);
    HeadZone.BoneNames = {
        TEXT("head"),
        TEXT("neck_01"),
        TEXT("neck_02")
    };
    BoneToZoneMappings.Add(HeadZone);

    // Chest zone - upper torso
    FHitZoneBoneMapping ChestZone;
    ChestZone.ZoneTag = FGameplayTag::RequestGameplayTag(FName("Hit.Zone.Chest"), false);
    ChestZone.BoneNames = {
        TEXT("spine_03"),
        TEXT("spine_04"),
        TEXT("spine_05"),
        TEXT("clavicle_l"),
        TEXT("clavicle_r")
    };
    BoneToZoneMappings.Add(ChestZone);

    // Torso zone - mid/lower torso including pelvis
    FHitZoneBoneMapping TorsoZone;
    TorsoZone.ZoneTag = FGameplayTag::RequestGameplayTag(FName("Hit.Zone.Torso"), false);
    TorsoZone.BoneNames = {
        TEXT("spine_01"),
        TEXT("spine_02"),
        TEXT("pelvis")
    };
    BoneToZoneMappings.Add(TorsoZone);

    // Left Arm zone - entire left arm (shoulder to fingertips via hierarchy)
    FHitZoneBoneMapping LeftArmZone;
    LeftArmZone.ZoneTag = FGameplayTag::RequestGameplayTag(FName("Hit.Zone.LeftArm"), false);
    LeftArmZone.BoneNames = {
        TEXT("upperarm_l"),
        TEXT("lowerarm_l"),
        TEXT("hand_l")
    };
    BoneToZoneMappings.Add(LeftArmZone);

    // Right Arm zone - entire right arm
    FHitZoneBoneMapping RightArmZone;
    RightArmZone.ZoneTag = FGameplayTag::RequestGameplayTag(FName("Hit.Zone.RightArm"), false);
    RightArmZone.BoneNames = {
        TEXT("upperarm_r"),
        TEXT("lowerarm_r"),
        TEXT("hand_r")
    };
    BoneToZoneMappings.Add(RightArmZone);

    // Left Leg zone - entire left leg (hip to toes via hierarchy)
    FHitZoneBoneMapping LeftLegZone;
    LeftLegZone.ZoneTag = FGameplayTag::RequestGameplayTag(FName("Hit.Zone.LeftLeg"), false);
    LeftLegZone.BoneNames = {
        TEXT("thigh_l"),
        TEXT("calf_l"),
        TEXT("foot_l")
    };
    BoneToZoneMappings.Add(LeftLegZone);

    // Right Leg zone - entire right leg
    FHitZoneBoneMapping RightLegZone;
    RightLegZone.ZoneTag = FGameplayTag::RequestGameplayTag(FName("Hit.Zone.RightLeg"), false);
    RightLegZone.BoneNames = {
        TEXT("thigh_r"),
        TEXT("calf_r"),
        TEXT("foot_r")
    };
    BoneToZoneMappings.Add(RightLegZone);
}

bool UACFHitReactionChooserAction::IsDeathHit_Implementation() const
{
    return false;
}

void UACFHitReactionChooserAction::BuildBoneToZoneCache()
{
    BoneToZoneCache.Empty();
    bCacheBuilt = false;

    ACharacter* Character = GetCharacterOwner();
    USkeletalMeshComponent* MeshComp = Character ? Character->GetMesh() : nullptr;

    if (!MeshComp || BoneToZoneMappings.Num() == 0)
    {
        return;
    }

    // For each configured zone bone, traverse down to cache all child bones
    for (const FHitZoneBoneMapping& ZoneMapping : BoneToZoneMappings)
    {
        const FGameplayTag& ZoneTag = ZoneMapping.ZoneTag;
        const TArray<FName>& ConfiguredBones = ZoneMapping.BoneNames;

        for (const FName& ConfiguredBone : ConfiguredBones)
        {
            const int32 BoneIndex = MeshComp->GetBoneIndex(ConfiguredBone);
            if (BoneIndex == INDEX_NONE)
            {
                continue;
            }

            // Cache this bone and all its children (traverse down hierarchy)
            TArray<int32> BonesToCache;
            BonesToCache.Add(BoneIndex);

            // Breadth-first traversal to get all child bones
            const FReferenceSkeleton& RefSkeleton = MeshComp->GetSkeletalMeshAsset()->GetRefSkeleton();
            const int32 NumBones = RefSkeleton.GetNum();

            for (int32 i = 0; i < BonesToCache.Num(); ++i)
            {
                const int32 CurrentBoneIndex = BonesToCache[i];
                const FName CurrentBoneName = MeshComp->GetBoneName(CurrentBoneIndex);

                // Add to cache if not already present (first zone wins)
                if (!BoneToZoneCache.Contains(CurrentBoneName))
                {
                    BoneToZoneCache.Add(CurrentBoneName, ZoneTag);
                }

                // Find all children by checking which bones have this as parent
                for (int32 ChildIndex = 0; ChildIndex < NumBones; ++ChildIndex)
                {
                    if (RefSkeleton.GetParentIndex(ChildIndex) == CurrentBoneIndex)
                    {
                        BonesToCache.Add(ChildIndex);
                    }
                }
            }
        }
    }

    bCacheBuilt = true;
}

FACFDamageEvent UACFHitReactionChooserAction::GetCurrentDamageEvent() const
{
    AACFCharacter* acfCharacter = Cast<AACFCharacter>(GetCharacterOwner());
    if (!acfCharacter)
    {
        UE_LOG(LogTemp, Warning, TEXT("ACFHitReactionChooserAction: Character owner is invalid!"));
        return FACFDamageEvent();
    }

    return acfCharacter->GetLastDamageInfo();
}

void UACFHitReactionChooserAction::OnActionEnded_Implementation()
{
    Super::OnActionEnded_Implementation();

    // If this was a death hit, disable movement after warp is done
    if (IsDeathHit())
    {
        if (UCharacterMovementComponent* moveComp = CharacterOwner->GetCharacterMovement())
        {
            moveComp->DisableMovement();
        }
    }
}

FTransform UACFHitReactionChooserAction::GetWarpTransform_Implementation()
{
    ACharacter* Character = GetCharacterOwner();
    if (!Character || !animMontage)
    {
        return FTransform(Character ? Character->GetActorRotation() : FRotator::ZeroRotator,
                         Character ? Character->GetActorLocation() : FVector::ZeroVector,
                         FVector(1.f));
    }

    FVector location = Character->GetActorLocation();
    FRotator rot = Character->GetActorRotation();

    // Get current damage event
    const FACFDamageEvent CurrentDamageEvent = GetCurrentDamageEvent();

    float warpDistance = BaseWarpDistance;
    float forceValue = 0.f;

    if (bUseDamageImpulse)
    {
        // Use damage impulse if available
        if (CurrentDamageEvent.DamageClass)
        {
            const UDamageType* damageObj = CurrentDamageEvent.DamageClass.GetDefaultObject();
            if (damageObj)
            {
                forceValue = damageObj->DamageImpulse;
            }
        }
    }
    else
    {
        // Use damage amount
        forceValue = CurrentDamageEvent.FinalDamage;
    }

    // Add force-based distance
    warpDistance += forceValue * ForceDistanceMultiplier;

    // Clamp to max distance
    warpDistance = FMath::Min(warpDistance, MaxWarpDistance);

    // Calculate warp direction based on damage (move away from attacker)
    // GetActorsRelativeDirectionVector returns (receiver - dealer), which already points away from dealer
    const FVector damageMomentum = UACFFunctionLibrary::GetActorsRelativeDirectionFromDamageEvent(CurrentDamageEvent);
    FVector direction = (damageMomentum * warpDistance);

    // Apply warp movement
    location = Character->GetActorLocation() + direction;

    // Rotate to face attacker if enabled
    if (bShouldFaceAttacker && CurrentDamageEvent.DamageDealer)
    {
        rot = UKismetMathLibrary::FindLookAtRotation(
            Character->GetActorLocation(),
            CurrentDamageEvent.DamageDealer->GetActorLocation()
        );
        rot.Pitch = 0.f;
        rot.Roll = 0.f;
    }

    return FTransform(rot, location, FVector(1.f));
}

void UACFHitReactionChooserAction::SetChooserParams_Implementation()
{
    Super::SetChooserParams_Implementation();

    // Get current damage event
    const FACFDamageEvent CurrentDamageEvent = GetCurrentDamageEvent();

    // Check if character is dead (for death animation selection in chooser)
    AACFCharacter* acfCharacter = Cast<AACFCharacter>(GetCharacterOwner());
    bIsDead = acfCharacter ? acfCharacter->GetIsDead() : false;

    // Build cache on first use
    if (!bCacheBuilt)
    {
        BuildBoneToZoneCache();
    }

    // Fast O(1) lookup using cached bone-to-zone mapping
    HitZone.Reset();
    const FName HitBoneName = CurrentDamageEvent.hitResult.BoneName;

    if (HitBoneName != NAME_None)
    {
        const FGameplayTag* ZoneTag = BoneToZoneCache.Find(HitBoneName);
        if (ZoneTag && ZoneTag->IsValid())
        {
            HitZone.AddTag(*ZoneTag);
        }
        else if (DefaultHitZone.IsValid())
        {
            // No mapping found - use default zone if configured
            HitZone.AddTag(DefaultHitZone);
        }
    }

    // Set damage type tags (now directly available in damage event)
    DamageTypeTags = CurrentDamageEvent.DamageTags;

    // Calculate 8-way damage direction for chooser
    if (CurrentDamageEvent.DamageDealer && CurrentDamageEvent.DamageReceiver)
    {
        // Direction from victim to attacker
        const FVector directionToAttacker = (CurrentDamageEvent.DamageDealer->GetActorLocation() -
                                             CurrentDamageEvent.DamageReceiver->GetActorLocation()).GetSafeNormal();

        DamageDirection = UACFFunctionLibrary::GetDirection8FromInput(CurrentDamageEvent.DamageReceiver, directionToAttacker);
    }
    else
    {
        DamageDirection = EACFDirection::Front;
    }
}
