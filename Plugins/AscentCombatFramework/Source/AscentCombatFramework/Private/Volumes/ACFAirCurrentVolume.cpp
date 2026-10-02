// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Volumes/ACFAirCurrentVolume.h"
#include "Components/ACFAirCurrentBoostComponent.h"

#include "AbilitySystemComponent.h"
#include "Components/ArrowComponent.h"
#include "Components/BoxComponent.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Net/UnrealNetwork.h"

// ---------------------------------------------------------------------------

AACFAirCurrentVolume::AACFAirCurrentVolume()
{
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.bStartWithTickEnabled = false;
    bReplicates = true;

    CollisionVolume = CreateDefaultSubobject<UBoxComponent>(TEXT("CollisionVolume"));
    CollisionVolume->SetBoxExtent(FVector(200.f, 200.f, 400.f));
    CollisionVolume->SetCollisionProfileName(TEXT("OverlapAllDynamic"));
    CollisionVolume->SetGenerateOverlapEvents(true);
    SetRootComponent(CollisionVolume);

    DirectionArrow = CreateDefaultSubobject<UArrowComponent>(TEXT("DirectionArrow"));
    DirectionArrow->SetupAttachment(CollisionVolume);
    DirectionArrow->SetArrowColor(FLinearColor(0.2f, 0.6f, 1.f));
    DirectionArrow->bIsScreenSizeScaled = false;
}

// ---------------------------------------------------------------------------

void AACFAirCurrentVolume::UpdateDirectionArrow()
{
    if (!DirectionArrow)
    {
        return;
    }

    const FVector Dir = AirCurrentConfig.Direction.GetSafeNormal();
    if (!Dir.IsNearlyZero())
    {
        DirectionArrow->SetWorldRotation(Dir.Rotation());
    }
}

void AACFAirCurrentVolume::OnConstruction(const FTransform& Transform)
{
    Super::OnConstruction(Transform);
    UpdateDirectionArrow();
}

#if WITH_EDITOR
void AACFAirCurrentVolume::PostEditChangeProperty(FPropertyChangedEvent& PropertyChangedEvent)
{
    Super::PostEditChangeProperty(PropertyChangedEvent);
    UpdateDirectionArrow();
}
#endif

// ---------------------------------------------------------------------------

void AACFAirCurrentVolume::BeginPlay()
{
    Super::BeginPlay();

    UpdateDirectionArrow();

    CollisionVolume->OnComponentBeginOverlap.AddDynamic(this, &AACFAirCurrentVolume::HandleBeginOverlap);
    CollisionVolume->OnComponentEndOverlap.AddDynamic(this, &AACFAirCurrentVolume::HandleEndOverlap);

    bIsActive = bStartActive;

    if (bIsActive && AirCurrentConfig.bContinuous)
    {
        SetActorTickEnabled(true);
    }
}

// ---------------------------------------------------------------------------
// Replication
// ---------------------------------------------------------------------------

void AACFAirCurrentVolume::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AACFAirCurrentVolume, bIsActive);
}

void AACFAirCurrentVolume::OnRep_bIsActive()
{
}

// ---------------------------------------------------------------------------
// Activation
// ---------------------------------------------------------------------------

void AACFAirCurrentVolume::SetActive(bool bNewActive)
{
    if (bIsActive == bNewActive)
    {
        return;
    }

    bIsActive = bNewActive;

    if (HasAuthority())
    {
        if (!bIsActive)
        {
            ClearAllOverlaps();
            SetActorTickEnabled(false);
        }
        else if (AirCurrentConfig.bContinuous)
        {
            SetActorTickEnabled(true);
        }
    }
}

// ---------------------------------------------------------------------------
// Queries
// ---------------------------------------------------------------------------

FVector AACFAirCurrentVolume::GetCurrentDirection() const
{
    return AirCurrentConfig.Direction.GetSafeNormal();
}

float AACFAirCurrentVolume::GetCurrentStrength() const
{
    return AirCurrentConfig.Strength;
}

// ---------------------------------------------------------------------------
// Gameplay Cue helpers
// ---------------------------------------------------------------------------

void AACFAirCurrentVolume::AddAirCurrentCue(ACharacter* Character)
{
    if (!AirCurrentCueTag.IsValid() || !Character)
    {
        return;
    }

    UAbilitySystemComponent* ASC = Character->FindComponentByClass<UAbilitySystemComponent>();
    if (ASC)
    {
        ASC->AddGameplayCue(AirCurrentCueTag, FGameplayCueParameters());
    }
}

void AACFAirCurrentVolume::RemoveAirCurrentCue(ACharacter* Character)
{
    if (!AirCurrentCueTag.IsValid() || !Character)
    {
        return;
    }

    UAbilitySystemComponent* ASC = Character->FindComponentByClass<UAbilitySystemComponent>();
    if (ASC)
    {
        ASC->RemoveGameplayCue(AirCurrentCueTag);
    }
}

// ---------------------------------------------------------------------------
// Overlap handling
// ---------------------------------------------------------------------------

void AACFAirCurrentVolume::HandleBeginOverlap(UPrimitiveComponent* OverlappedComp,
    AActor* OtherActor, UPrimitiveComponent* OtherComp,
    int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
    if (!bIsActive)
    {
        return;
    }

    ACharacter* Character = Cast<ACharacter>(OtherActor);
    if (!Character)
    {
        return;
    }

    if (!Character->IsLocallyControlled() && !HasAuthority())
    {
        return;
    }

    if (FindOverlapEntry(Character) != INDEX_NONE)
    {
        return;
    }

    UACFAirCurrentBoostComponent* BoostComp = nullptr;
    if (HasAuthority())
    {
        BoostComp = EnsureBoostComponent(Character);
        if (BoostComp)
        {
            BoostComp->EnterAirCurrent(this, AirCurrentConfig);
        }
    }

    FACFAirCurrentOverlapEntry Entry;
    Entry.Character        = Character;
    Entry.BoostComponent   = BoostComp;
    Entry.PulseAccumulator = 0.f;
    OverlappingEntries.Add(Entry);

    if (!AirCurrentConfig.bContinuous && IsCharacterEligible(Character))
    {
        const float Depth = AirCurrentConfig.bScaleWithOverlapDepth ? ComputeDepthScale(Character) : 1.f;
        ApplyBoostToCharacter(Character, 1.f, Depth);
    }

    if (AirCurrentConfig.bContinuous)
    {
        SetActorTickEnabled(true);
    }

    if (HasAuthority())
    {
        AddAirCurrentCue(Character);
        OnCharacterEnteredCurrent(Character);
    }
}

void AACFAirCurrentVolume::HandleEndOverlap(UPrimitiveComponent* OverlappedComp,
    AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex)
{
    ACharacter* Character = Cast<ACharacter>(OtherActor);
    if (!Character)
    {
        return;
    }

    const int32 Idx = FindOverlapEntry(Character);
    if (Idx == INDEX_NONE)
    {
        return;
    }

    UACFAirCurrentBoostComponent* BoostComp = OverlappingEntries[Idx].BoostComponent.Get();
    OverlappingEntries.RemoveAtSwap(Idx);

    if (HasAuthority())
    {
        if (BoostComp)
        {
            BoostComp->ExitAirCurrent(this);
        }

        RemoveAirCurrentCue(Character);
        OnCharacterExitedCurrent(Character);
    }

    if (OverlappingEntries.Num() == 0 && AirCurrentConfig.bContinuous)
    {
        SetActorTickEnabled(false);
    }
}

// ---------------------------------------------------------------------------
// Tick
// ---------------------------------------------------------------------------

void AACFAirCurrentVolume::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);

    if (!bIsActive || !AirCurrentConfig.bContinuous)
    {
        return;
    }

    for (int32 i = OverlappingEntries.Num() - 1; i >= 0; --i)
    {
        FACFAirCurrentOverlapEntry& Entry = OverlappingEntries[i];
        ACharacter* Character = Entry.Character.Get();
        if (!Character)
        {
            OverlappingEntries.RemoveAtSwap(i);
            continue;
        }

        if (!IsCharacterEligible(Character))
        {
            continue;
        }

        if (AirCurrentConfig.PulseIntervalSec > 0.f)
        {
            Entry.PulseAccumulator += DeltaTime;
            if (Entry.PulseAccumulator < AirCurrentConfig.PulseIntervalSec)
            {
                continue;
            }
            Entry.PulseAccumulator -= AirCurrentConfig.PulseIntervalSec;
        }

        const float Depth = AirCurrentConfig.bScaleWithOverlapDepth ? ComputeDepthScale(Character) : 1.f;
        ApplyBoostToCharacter(Character, DeltaTime, Depth);
    }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

bool AACFAirCurrentVolume::IsCharacterEligible(const ACharacter* Character) const
{
    if (!Character)
    {
        return false;
    }

    if (!AirCurrentConfig.bOnlyAffectsGliders)
    {
        const UCharacterMovementComponent* MovComp = Character->GetCharacterMovement();
        return MovComp && MovComp->IsFalling();
    }

    // bOnlyAffectsGliders == true: require an active glider.
    const UACFAirCurrentBoostComponent* BoostComp = Character->FindComponentByClass<UACFAirCurrentBoostComponent>();
    return BoostComp && BoostComp->HasActiveGlider();
}

void AACFAirCurrentVolume::ApplyBoostToCharacter(ACharacter* Character, float DeltaTime, float DepthScale)
{
    UCharacterMovementComponent* MovComp = Character->GetCharacterMovement();
    if (!MovComp)
    {
        return;
    }

    const FVector Dir = AirCurrentConfig.Direction.GetSafeNormal();
    if (Dir.IsNearlyZero())
    {
        return;
    }

    const float CurrentAlongDir = FVector::DotProduct(MovComp->Velocity, Dir);
    const float Headroom = AirCurrentConfig.MaxAddedSpeed - FMath::Max(CurrentAlongDir, 0.f);
    if (Headroom <= 0.f)
    {
        return;
    }

    const float RawDelta = AirCurrentConfig.Strength * DeltaTime * DepthScale;
    const float ClampedDelta = FMath::Min(RawDelta, Headroom);

    MovComp->Velocity += Dir * ClampedDelta;
}

float AACFAirCurrentVolume::ComputeDepthScale(const ACharacter* Character) const
{
    if (!CollisionVolume || !Character)
    {
        return 1.f;
    }

    const FVector CharLoc = Character->GetActorLocation();
    const FVector VolCentre = CollisionVolume->GetComponentLocation();
    const FVector Extent = CollisionVolume->GetScaledBoxExtent();

    const FVector LocalOffset = (CharLoc - VolCentre).GetAbs();
    float MaxNorm = 0.f;
    if (Extent.X > KINDA_SMALL_NUMBER) MaxNorm = FMath::Max(MaxNorm, LocalOffset.X / Extent.X);
    if (Extent.Y > KINDA_SMALL_NUMBER) MaxNorm = FMath::Max(MaxNorm, LocalOffset.Y / Extent.Y);
    if (Extent.Z > KINDA_SMALL_NUMBER) MaxNorm = FMath::Max(MaxNorm, LocalOffset.Z / Extent.Z);

    return FMath::Clamp(1.f - MaxNorm, 0.f, 1.f);
}

UACFAirCurrentBoostComponent* AACFAirCurrentVolume::EnsureBoostComponent(ACharacter* Character)
{
    UACFAirCurrentBoostComponent* Comp = Character->FindComponentByClass<UACFAirCurrentBoostComponent>();
    if (!Comp)
    {
        Comp = NewObject<UACFAirCurrentBoostComponent>(Character, TEXT("AirCurrentBoost"));
        Comp->RegisterComponent();
    }
    return Comp;
}

void AACFAirCurrentVolume::ClearAllOverlaps()
{
    for (FACFAirCurrentOverlapEntry& Entry : OverlappingEntries)
    {
        UACFAirCurrentBoostComponent* BoostComp = Entry.BoostComponent.Get();
        ACharacter* Character = Entry.Character.Get();
        if (BoostComp)
        {
            BoostComp->ExitAirCurrent(this);
        }
        if (Character)
        {
            RemoveAirCurrentCue(Character);
            OnCharacterExitedCurrent(Character);
        }
    }
    OverlappingEntries.Empty();
}

int32 AACFAirCurrentVolume::FindOverlapEntry(const ACharacter* Character) const
{
    for (int32 i = 0; i < OverlappingEntries.Num(); ++i)
    {
        if (OverlappingEntries[i].Character.Get() == Character)
        {
            return i;
        }
    }
    return INDEX_NONE;
}