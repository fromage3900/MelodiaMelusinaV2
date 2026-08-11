#include "MelodiaExplorationActors.h"

#include "Components/BoxComponent.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/Pawn.h"
#include "MelodiaPacingSubsystem.h"

namespace
{
    void ConfigureExplorerTrigger(UBoxComponent* Box)
    {
        Box->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
        Box->SetCollisionResponseToAllChannels(ECR_Ignore);
        Box->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
        Box->SetBoxExtent(FVector(120.0, 120.0, 120.0));
    }

    bool LooksLikeMelusina(const AActor* Actor)
    {
        return Actor && (Actor->ActorHasTag(TEXT("Melusina")) ||
            Actor->GetClass()->GetName().Contains(TEXT("Melusina"), ESearchCase::IgnoreCase));
    }
}

AMelodiaExplorationInteractionVolume::AMelodiaExplorationInteractionVolume()
{
    PrimaryActorTick.bCanEverTick = false;
    auto* Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
    SetRootComponent(Root);
    InteractionVolume = CreateDefaultSubobject<UBoxComponent>(TEXT("InteractionVolume"));
    InteractionVolume->SetupAttachment(Root);
    ConfigureExplorerTrigger(InteractionVolume);
    PromptText = FText::FromString(TEXT("Inspect"));
}

void AMelodiaExplorationInteractionVolume::BeginPlay()
{
    Super::BeginPlay();
    InteractionVolume->OnComponentBeginOverlap.AddDynamic(this, &ThisClass::HandleBeginOverlap);
    InteractionVolume->OnComponentEndOverlap.AddDynamic(this, &ThisClass::HandleEndOverlap);
}

bool AMelodiaExplorationInteractionVolume::IsEligibleExplorer(const AActor* Actor) const
{
    return Cast<APawn>(Actor) && (!bRequireMelusina || LooksLikeMelusina(Actor));
}

void AMelodiaExplorationInteractionVolume::HandleBeginOverlap(UPrimitiveComponent*, AActor* OtherActor,
    UPrimitiveComponent*, int32, bool, const FHitResult&)
{
    if (bInteractionActive && !bConsumed && IsEligibleExplorer(OtherActor))
    {
        OnMelusinaEntered.Broadcast(OtherActor);
    }
}

void AMelodiaExplorationInteractionVolume::HandleEndOverlap(UPrimitiveComponent*, AActor* OtherActor,
    UPrimitiveComponent*, int32)
{
    if (IsEligibleExplorer(OtherActor))
    {
        OnMelusinaExited.Broadcast(OtherActor);
    }
}

bool AMelodiaExplorationInteractionVolume::TryInteract(AActor* InteractingActor)
{
    if (!bInteractionActive || bConsumed || !IsEligibleExplorer(InteractingActor))
    {
        return false;
    }
    OnInteractionRequested.Broadcast(InteractingActor);
    bConsumed = bOneShot;
    return true;
}

AMelodiaPuzzleRelayVolume::AMelodiaPuzzleRelayVolume()
{
    PrimaryActorTick.bCanEverTick = false;
    auto* Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
    SetRootComponent(Root);
    TriggerVolume = CreateDefaultSubobject<UBoxComponent>(TEXT("TriggerVolume"));
    TriggerVolume->SetupAttachment(Root);
    ConfigureExplorerTrigger(TriggerVolume);
}

void AMelodiaPuzzleRelayVolume::BeginPlay()
{
    Super::BeginPlay();
    TriggerVolume->OnComponentBeginOverlap.AddDynamic(this, &ThisClass::HandleBeginOverlap);
}

bool AMelodiaPuzzleRelayVolume::IsEligibleExplorer(const AActor* Actor) const
{
    return Cast<APawn>(Actor) && (!bRequireMelusina || LooksLikeMelusina(Actor));
}

void AMelodiaPuzzleRelayVolume::HandleBeginOverlap(UPrimitiveComponent*, AActor* OtherActor,
    UPrimitiveComponent*, int32, bool, const FHitResult&)
{
    ActivateRelay(OtherActor);
}

bool AMelodiaPuzzleRelayVolume::ActivateRelay(AActor* ActivatingActor)
{
    if ((bOneShot && bActivated) || !IsEligibleExplorer(ActivatingActor))
    {
        return false;
    }
    bActivated = true;
    OnPuzzleActivated.Broadcast(ActivatingActor);
    return true;
}

void AMelodiaPuzzleRelayVolume::ResetRelay()
{
    bActivated = false;
}

AMelodiaMovingPlatform::AMelodiaMovingPlatform()
{
    PrimaryActorTick.bCanEverTick = true;
    auto* Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
    SetRootComponent(Root);
    PlatformMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PlatformMesh"));
    PlatformMesh->SetupAttachment(Root);
    PlatformMesh->SetCollisionProfileName(TEXT("BlockAllDynamic"));
}

void AMelodiaMovingPlatform::BeginPlay()
{
    Super::BeginPlay();
    StartLocation = GetActorLocation();
    bMoving = bAutoStart;
    // Resolve the travel duration once at spawn, never per-Tick (same pattern as
    // MelodiaSirMelodiousIntroActor::ResolvedDepartureDurationSeconds). Pacing
    // subsystem is optional polish: on a false return the authored TravelDuration
    // is used unchanged.
    ResolvedTravelDuration = TravelDuration;
    if (UMelodiaPacingSubsystem* Pacing = UMelodiaPacingSubsystem::Get(this))
    {
        Pacing->ResolveDuration(TEXT("PlatformTravelDuration"), ResolvedTravelDuration);
    }
}

void AMelodiaMovingPlatform::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!bMoving)
    {
        return;
    }

    ElapsedTime += DeltaSeconds;
    const float Duration = FMath::Max(ResolvedTravelDuration, KINDA_SMALL_NUMBER);
    float Alpha = ElapsedTime / Duration;
    if (bPingPong)
    {
        Alpha = 0.5f - 0.5f * FMath::Cos(Alpha * UE_TWO_PI);
    }
    else
    {
        Alpha = FMath::Clamp(Alpha, 0.0f, 1.0f);
        if (Alpha >= 1.0f)
        {
            bMoving = false;
        }
    }
    SetActorLocation(FMath::Lerp(StartLocation, StartLocation + GetActorTransform().TransformVectorNoScale(LocalEndOffset), Alpha), true);
}

void AMelodiaMovingPlatform::StartMotion()
{
    ElapsedTime = 0.0f;
    bMoving = true;
}

void AMelodiaMovingPlatform::StopMotion()
{
    bMoving = false;
}

void AMelodiaMovingPlatform::ResetPlatform()
{
    bMoving = false;
    ElapsedTime = 0.0f;
    SetActorLocation(StartLocation, true);
}
