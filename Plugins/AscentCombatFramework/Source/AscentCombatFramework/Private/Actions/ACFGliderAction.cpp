// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Actions/ACFGliderAction.h"
#include "Actors/ACFCharacter.h"
#include "Animation/ACFAnimInstance.h"
#include "Components/ACFAirCurrentBoostComponent.h"
#include "Components/ACFEquipmentComponent.h"
#include "Components/ACFInventoryComponent.h"
#include "ItemActors/ACFGliderActor.h"

#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"

UACFGliderAction::UACFGliderAction()
{
    ActionConfig.PerformableInMovementModes.Empty();
    ActionConfig.PerformableInMovementModes.Add(EMovementMode::MOVE_Falling);

    bBindActionToAnimation = false;
    InstancingPolicy = EGameplayAbilityInstancingPolicy::InstancedPerActor;
}

// ---------------------------------------------------------------------------

bool UACFGliderAction::CanActivateAbility(const FGameplayAbilitySpecHandle Handle,
    const FGameplayAbilityActorInfo* ActorInfo,
    const FGameplayTagContainer* SourceTags,
    const FGameplayTagContainer* TargetTags,
    OUT FGameplayTagContainer* OptionalRelevantTags) const
{
    if (!Super::CanActivateAbility(Handle, ActorInfo, SourceTags, TargetTags, OptionalRelevantTags))
    {
        return false;
    }

    if (!bNeedsItem)
    {
        return true;
    }

    const UACFInventoryComponent* Inventory = ActorInfo->AvatarActor->FindComponentByClass<UACFInventoryComponent>();
    if (!Inventory)
    {
        return false;
    }

    if (!GliderItemClass)
    {
        return false;
    }
    return Inventory->HasAnyItemOfType(GliderItemClass);
}

// ---------------------------------------------------------------------------

void UACFGliderAction::ActivateAbility(const FGameplayAbilitySpecHandle Handle,
    const FGameplayAbilityActorInfo* ActorInfo,
    const FGameplayAbilityActivationInfo ActivationInfo,
    const FGameplayEventData* TriggerEventData)
{
    Super::ActivateAbility(Handle, ActorInfo, ActivationInfo, TriggerEventData);

    ACharacter* Char = GetCharacterOwner();
    if (!Char)
    {
        return;
    }

    UCharacterMovementComponent* MovComp = Char->GetCharacterMovement();
    if (!MovComp)
    {
        EndAbility(Handle, ActorInfo, ActivationInfo, true, true);
        return;
    }

    CachedGliderItem = nullptr;

    if (bNeedsItem)
    {
        // CanActivateAbility already validated inventory presence.
        UACFInventoryComponent* Inventory = Char->FindComponentByClass<UACFInventoryComponent>();
        if (Inventory)
        {
            const TSubclassOf<UACFItem> SearchClass = GliderItemClass.Get()
                ? TSubclassOf<UACFItem>(GliderItemClass.Get())
                : TSubclassOf<UACFItem>(UACFGliderItem::StaticClass());
            FInventoryItem FoundItem;
            Inventory->FindFirstItemOfClassInInventory(SearchClass, FoundItem);
            CachedGliderItem = Cast<UACFGliderItem>(FoundItem.Item);
        }
    }

    // Use item's movement config when available, otherwise fall back to the ability's own settings.
    const FGliderMovementConfig& ActiveConfig = CachedGliderItem ? CachedGliderItem->MovementConfig : GliderMovementConfig;
    ApplyMovementConfig(MovComp, ActiveConfig);

    // Reset the fall-height reference so damage is measured from the glider activation point,
    // not from wherever the character originally started falling.
    if (AACFCharacter* ACFChar = Cast<AACFCharacter>(Char))
    {
        ACFChar->ResetFallHeight();
    }

    Char->LandedDelegate.AddDynamic(this, &UACFGliderAction::HandleLanded);
    Char->MovementModeChangedDelegate.AddDynamic(this, &UACFGliderAction::HandleMovementModeChanged);

    // The glider actor is spawned later, when the NotablePoint anim notify fires.

    // -- Air current integration ----------------------------------------------
    AirCurrentComp = Char->FindComponentByClass<UACFAirCurrentBoostComponent>();
    if (AirCurrentComp)
    {
        AirCurrentComp->NotifyGliderOpened();
        AirCurrentComp->OnAirCurrentStateChanged.AddDynamic(this, &UACFGliderAction::HandleAirCurrentStateChanged);
    }

    OnGliderOpened();
}

// ---------------------------------------------------------------------------

void UACFGliderAction::EndAbility(const FGameplayAbilitySpecHandle Handle,
    const FGameplayAbilityActorInfo* ActorInfo,
    const FGameplayAbilityActivationInfo ActivationInfo,
    bool bReplicateEndAbility,
    bool bWasCancelled)
{
    OnGliderClosed(bWasCancelled);

    // Reset fall-height reference so damage is measured only from the point where
    // the glider closes, not from the original jump/fall start.
    if (AACFCharacter* ACFChar = Cast<AACFCharacter>(GetCharacterOwner()))
    {
        ACFChar->ResetFallHeight();
    }

    // -- Air current cleanup --------------------------------------------------
    if (AirCurrentComp)
    {
        AirCurrentComp->OnAirCurrentStateChanged.RemoveDynamic(this, &UACFGliderAction::HandleAirCurrentStateChanged);
        AirCurrentComp->NotifyGliderClosed();
        AirCurrentComp = nullptr;
    }

    ACharacter* Char = GetCharacterOwner();
    if (Char)
    {
        Char->LandedDelegate.RemoveDynamic(this, &UACFGliderAction::HandleLanded);
        Char->MovementModeChangedDelegate.RemoveDynamic(this, &UACFGliderAction::HandleMovementModeChanged);

        UCharacterMovementComponent* MovComp = Char->GetCharacterMovement();
        if (MovComp)
        {
            RestoreMovementConfig(MovComp);
        }
        RestoreHandIK(Char);
    }

    if (Char && Char->HasAuthority())
    {
        DestroyGliderActor();
    }

    Super::EndAbility(Handle, ActorInfo, ActivationInfo, bReplicateEndAbility, bWasCancelled);
}

// ---------------------------------------------------------------------------

void UACFGliderAction::SpawnGliderActor(ACharacter* Char, UACFGliderItem* GliderItem)
{
    if (!GliderItem || !Char || !Char->GetWorld())
    {
        return;
    }

    const TSubclassOf<AACFItemActor> ActorClass = GliderItem->GetItemActorClass();
    if (!ActorClass)
    {
        return;
    }

    AACFGliderActor* Actor = Char->GetWorld()->SpawnActorDeferred<AACFGliderActor>(
        ActorClass, Char->GetActorTransform(), Char);

    if (Actor)
    {
        Actor->InitItemActor(Char, GliderItem);
        UGameplayStatics::FinishSpawningActor(Actor, Char->GetActorTransform());
        SpawnedGliderActor = Actor;

        if (UACFAnimInstance* AnimInst = Cast<UACFAnimInstance>(Char->GetMesh()->GetAnimInstance()))
        {
            AnimInst->SetEnableHandIK(true);
        }
    }
}

void UACFGliderAction::DestroyGliderActor()
{
    if (SpawnedGliderActor)
    {
        RestoreHandIK(GetCharacterOwner());
        SpawnedGliderActor->Destroy();
        SpawnedGliderActor = nullptr;
    }
}

void UACFGliderAction::RestoreHandIK(ACharacter* Char)
{
    if (!Char)
    {
        return;
    }

    UACFEquipmentComponent* EquipComp = Char->FindComponentByClass<UACFEquipmentComponent>();
    if (EquipComp)
    {
        EquipComp->ClearLeftHandIKOverride();
    }

    if (USkeletalMeshComponent* MeshComp = Char->GetMesh())
    {
        if (UACFAnimInstance* AnimInst = Cast<UACFAnimInstance>(MeshComp->GetAnimInstance()))
        {
            AnimInst->SetEnableHandIK(EquipComp && EquipComp->ShouldUseLeftHandIK());
        }
    }
}

// ---------------------------------------------------------------------------

void UACFGliderAction::ApplyMovementConfig(UCharacterMovementComponent* MovComp, const FGliderMovementConfig& Config)
{
    OriginalMovement.GravityScale               = MovComp->GravityScale;
    OriginalMovement.AirControl                 = MovComp->AirControl;
    OriginalMovement.FallingLateralFriction     = MovComp->FallingLateralFriction;
    OriginalMovement.BrakingDecelerationFalling = MovComp->BrakingDecelerationFalling;
    OriginalMovement.MaxWalkSpeed               = MovComp->MaxWalkSpeed;

    MovComp->GravityScale               = Config.GravityScale;
    MovComp->AirControl                 = Config.AirControl;
    MovComp->FallingLateralFriction     = Config.FallingLateralFriction;
    MovComp->BrakingDecelerationFalling = Config.BrakingDecelerationFalling;

    if (Config.MaxFlySpeed > 0.f)
    {
        MovComp->MaxWalkSpeed = Config.MaxFlySpeed;
    }
}

void UACFGliderAction::RestoreMovementConfig(UCharacterMovementComponent* MovComp)
{
    MovComp->GravityScale               = OriginalMovement.GravityScale;
    MovComp->AirControl                 = OriginalMovement.AirControl;
    MovComp->FallingLateralFriction     = OriginalMovement.FallingLateralFriction;
    MovComp->BrakingDecelerationFalling = OriginalMovement.BrakingDecelerationFalling;
    MovComp->MaxWalkSpeed               = OriginalMovement.MaxWalkSpeed;
}

// ---------------------------------------------------------------------------

void UACFGliderAction::HandleLanded(const FHitResult& Hit)
{
    ReleaseAction();
}

// ---------------------------------------------------------------------------

void UACFGliderAction::OnNotablePointReached_Implementation()
{
    ACharacter* Char = GetCharacterOwner();
    if (Char && Char->HasAuthority())
    {
        SpawnGliderActor(Char, CachedGliderItem);
    }
}

// ---------------------------------------------------------------------------
// Air current integration
// ---------------------------------------------------------------------------

bool UACFGliderAction::IsInAirCurrent() const
{
    return AirCurrentComp && AirCurrentComp->IsInAirCurrent();
}

void UACFGliderAction::HandleMovementModeChanged(ACharacter* Character, EMovementMode PrevMovementMode, uint8 PrevCustomMode)
{
    if (Character && Character->GetCharacterMovement()->MovementMode != MOVE_Falling)
    {
        ReleaseAction();
    }
}

void UACFGliderAction::HandleAirCurrentStateChanged(bool bNowInAirCurrent)
{
    if (bNowInAirCurrent)
    {
        OnAirCurrentEntered();
    }
    else
    {
        OnAirCurrentExited();
    }
}
