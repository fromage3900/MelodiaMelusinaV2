// Hybrid-combat spike: world-resolved slime node (sandbox only).
// See header for the stub contract.

#include "MelodiaWorldSlimeNode.h"

#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/Character.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "TimerManager.h"

AMelodiaWorldSlimeNode::AMelodiaWorldSlimeNode()
{
	PrimaryActorTick.bCanEverTick = false;

	SlimeMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("SlimeMesh"));
	SetRootComponent(SlimeMesh);

	HitVolume = CreateDefaultSubobject<USphereComponent>(TEXT("HitVolume"));
	HitVolume->SetupAttachment(SlimeMesh);
	HitVolume->InitSphereRadius(120.0f);
	// Trigger profile: overlap pawn capsules (which BLOCK WorldDynamic by
	// default, so a QueryOnly + response-to-Pawn setup never fires).
	HitVolume->SetCollisionProfileName(TEXT("Trigger"));
}

void AMelodiaWorldSlimeNode::BeginPlay()
{
	Super::BeginPlay();
	CurrentHP = MaxHP;
	HitVolume->OnComponentBeginOverlap.AddUniqueDynamic(this, &AMelodiaWorldSlimeNode::OnHitOverlap);
}

void AMelodiaWorldSlimeNode::OnHitOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
	if (bIsDead || !IsValid(OtherActor) || !OtherActor->IsA<ACharacter>())
	{
		return;
	}
	// Player-controlled pawns only: ignore wild pawns and trigger volumes.
	const APawn* OtherPawn = Cast<APawn>(OtherActor);
	if (!IsValid(OtherPawn) || !OtherPawn->IsPlayerControlled())
	{
		return;
	}
	ResolveContactHit();
}

void AMelodiaWorldSlimeNode::ResolveContactHit()
{
	if (bIsDead)
	{
		return;
	}
	// STUB: stock scalar goes here when STOCK_BRIDGE lands.
	ApplyWorldDamage(SpikeBaseDamage * SpikeScalarStub);
}

void AMelodiaWorldSlimeNode::ApplyWorldDamage(float FinalDamage)
{
	if (bIsDead)
	{
		return;
	}
	CurrentHP = FMath::Max(0.0f, CurrentHP - FMath::Max(0.0f, FinalDamage));
	UE_LOG(LogTemp, Log, TEXT("MelodiaHybridSpike: world hit %.1f on %s (HP %.1f/%.1f)."),
		FinalDamage, *GetActorLabel(), CurrentHP, MaxHP);
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
	SetActorTickEnabled(false);
	UE_LOG(LogTemp, Log, TEXT("MelodiaHybridSpike: %s defeated in-world (typed result Victory, kills=%d)."),
		*GetActorLabel(), KillCount);
	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().SetTimer(RespawnTimer, this,
			&AMelodiaWorldSlimeNode::Respawn, RespawnSeconds, false);
	}
}

void AMelodiaWorldSlimeNode::Respawn()
{
	CurrentHP = MaxHP;
	bIsDead = false;
	SetActorHiddenInGame(false);
	SetActorEnableCollision(true);
	SetActorTickEnabled(true);
	UE_LOG(LogTemp, Log, TEXT("MelodiaHybridSpike: %s respawned (HP %.1f)."), *GetActorLabel(), CurrentHP);
}
