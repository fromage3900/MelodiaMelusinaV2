#include "MelodiaWorldSlimeNode.h"

#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "MelodiaExternalJRPGBridgeSubsystem.h"
#include "MelodiaHybridEncounterComponent.h"
#include "MelodiaNarrativeTypes.h"
#include "MelodiaNarrativeSubsystem.h"

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
	if (const UMelodiaNarrativeSubsystem* Narrative = UMelodiaNarrativeSubsystem::GetMelodiaNarrativeSubsystem(this))
	{
		if (Narrative->IsWorldEncounterCompleted(HybridEncounter->GetEncounterId()))
		{
			SetCanBeDamaged(false);
			SetActorEnableCollision(false);
			if (Narrative->GetWorldEncounterOutcome(HybridEncounter->GetEncounterId()) == EMelodiaBattleResult::Victory)
			{
				CurrentHP = 0.0f;
				bIsDead = true;
				SetActorHiddenInGame(true);
			}
			return; // Restoring a durable outcome must never broadcast another death.
		}
	}
	if (StockAttackerDefinition && StockDefenderDefinition)
	{
		if (UMelodiaExternalJRPGBridgeSubsystem* Bridge =
			UMelodiaExternalJRPGBridgeSubsystem::GetGameInstanceSubsystem(GetGameInstance()))
		{
			Bridge->BindWorldDamageResolver(HybridEncounter,
				StockAttackerDefinition->GetDefaultObject(), StockDefenderDefinition->GetDefaultObject(),
				StockSkillDefinition ? StockSkillDefinition->GetDefaultObject() : nullptr, StockPureDamage);
		}
	}
}

bool AMelodiaWorldSlimeNode::IsPlayerInTargetRange(const APawn* PlayerPawn) const
{
	return !bIsDead && CanBeDamaged() && IsValid(PlayerPawn) && PlayerPawn->IsPlayerControlled()
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
	if (bIsDead || !CanBeDamaged() || !FMath::IsFinite(FinalDamage) || FinalDamage <= 0.0f)
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
	SetCanBeDamaged(false);
	SetActorHiddenInGame(true);
	SetActorEnableCollision(false);
	if (HybridEncounter
		&& HybridEncounter->GetPresentationMode() == EMelodiaHybridPresentationMode::Sequence)
	{
		HybridEncounter->CancelSequence();
	}

	UGameInstance* GameInstance = GetWorld() ? GetWorld()->GetGameInstance() : nullptr;
	UMelodiaExternalJRPGBridgeSubsystem* Bridge = GameInstance
		? GameInstance->GetSubsystem<UMelodiaExternalJRPGBridgeSubsystem>() : nullptr;
	const bool bCompleted = Bridge && Bridge->CompleteWorldEncounter(HybridEncounter, EMelodiaBattleResult::Victory);
	if (!bCompleted)
	{
		UE_LOG(LogTemp, Warning, TEXT("MELODIA_HYBRID_OUTCOME_NOT_RETAINED target=%s encounter=%s: completion failed and no retry is queued"),
			*GetName(), HybridEncounter ? *HybridEncounter->GetEncounterId().ToString() : TEXT("None"));
	}
}
