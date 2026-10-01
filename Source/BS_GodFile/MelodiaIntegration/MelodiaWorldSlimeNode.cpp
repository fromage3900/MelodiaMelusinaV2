#include "MelodiaWorldSlimeNode.h"

#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "MelodiaExternalJRPGBridgeSubsystem.h"
#include "MelodiaHybridEncounterComponent.h"
#include "MelodiaNarrativeTypes.h"

AMelodiaWorldSlimeNode::AMelodiaWorldSlimeNode()
{
	PrimaryActorTick.bCanEverTick = false;

	SlimeMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("SlimeMesh"));
	SetRootComponent(SlimeMesh);

	HitVolume = CreateDefaultSubobject<USphereComponent>(TEXT("HitVolume"));
	HitVolume->SetupAttachment(SlimeMesh);
	HitVolume->InitSphereRadius(120.0f);
	HitVolume->SetCollisionProfileName(TEXT("Trigger"));

	HybridEncounter = CreateDefaultSubobject<UMelodiaHybridEncounterComponent>(TEXT("HybridEncounter"));
}

void AMelodiaWorldSlimeNode::BeginPlay()
{
	Super::BeginPlay();
	CurrentHP = FMath::Max(1.0f, MaxHP);
}

bool AMelodiaWorldSlimeNode::IsPlayerInTargetRange(const APawn* PlayerPawn) const
{
	return !bIsDead && IsValid(PlayerPawn) && PlayerPawn->IsPlayerControlled()
		&& HitVolume && HitVolume->IsOverlappingActor(PlayerPawn);
}

float AMelodiaWorldSlimeNode::TakeDamage(const float DamageAmount, const FDamageEvent& DamageEvent,
	AController* EventInstigator, AActor* DamageCauser)
{
	const float Before = CurrentHP;
	ApplyWorldDamage(DamageAmount);
	return Before - CurrentHP;
}

void AMelodiaWorldSlimeNode::ApplyWorldDamage(const float FinalDamage)
{
	if (bIsDead || !FMath::IsFinite(FinalDamage) || FinalDamage <= 0.0f)
	{
		return;
	}
	CurrentHP = FMath::Max(0.0f, CurrentHP - FinalDamage);
	UE_LOG(LogTemp, Log, TEXT("MELODIA_HYBRID_HIT target=%s final=%.1f hp=%.1f/%.1f"),
		*GetName(), FinalDamage, CurrentHP, MaxHP);
	if (CurrentHP <= 0.0f)
	{
		Die();
	}
}

void AMelodiaWorldSlimeNode::Die()
{
	bIsDead = true;
	++KillCount;
	SetActorHiddenInGame(true);
	SetActorEnableCollision(false);
	if (HybridEncounter
		&& HybridEncounter->GetPresentationMode() == EMelodiaHybridPresentationMode::Sequence)
	{
		HybridEncounter->ExitSequence();
	}

	UGameInstance* GameInstance = GetWorld() ? GetWorld()->GetGameInstance() : nullptr;
	UMelodiaExternalJRPGBridgeSubsystem* Bridge = GameInstance
		? GameInstance->GetSubsystem<UMelodiaExternalJRPGBridgeSubsystem>() : nullptr;
	const bool bCompleted = Bridge && Bridge->CompleteWorldEncounter(HybridEncounter, EMelodiaBattleResult::Victory);
	if (!bCompleted)
	{
		UE_LOG(LogTemp, Warning, TEXT("MELODIA_HYBRID_OUTCOME_PENDING target=%s encounter=%s: narrative completion unavailable"),
			*GetName(), HybridEncounter ? *HybridEncounter->GetEncounterId().ToString() : TEXT("None"));
	}
}
