#include "MelodiaPartySubsystem.h"

#include "Components/SkeletalMeshComponent.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"

void UMelodiaPartySubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);

	// Default roster: 0 = Melusina (whatever pawn registers itself as 0),
	// 1 = Sir Melodious flight. Index 0 has no class on purpose - the game
	// mode spawns Melusina; the subsystem only lazy-spawns members > 0.
	if (PartyPawnClasses.Num() == 0)
	{
		PartyPawnClasses.SetNum(2);
		PartyPawnClasses[1] = TSoftClassPtr<APawn>(FSoftObjectPath(
			TEXT("/Game/Melodia/Characters/SirMelodious/BP_SirMelodious_Flight.BP_SirMelodious_Flight_C")));
	}
}

UMelodiaPartySubsystem* UMelodiaPartySubsystem::Get(const UObject* WorldContext)
{
	if (!WorldContext)
	{
		return nullptr;
	}
	const UWorld* World = WorldContext->GetWorld();
	if (!World || !World->GetGameInstance())
	{
		return nullptr;
	}
	return World->GetGameInstance()->GetSubsystem<UMelodiaPartySubsystem>();
}

void UMelodiaPartySubsystem::RegisterPawn(APawn* Pawn, const int32 Index)
{
	if (!Pawn || Index < 0)
	{
		return;
	}
	if (SpawnedPawns.Num() <= Index)
	{
		SpawnedPawns.SetNum(Index + 1);
	}
	SpawnedPawns[Index] = Pawn;
	if (Pawn->IsPlayerControlled())
	{
		ActiveIndex = Index;
	}
}

APawn* UMelodiaPartySubsystem::GetActivePawn() const
{
	return SpawnedPawns.IsValidIndex(ActiveIndex) ? SpawnedPawns[ActiveIndex].Get() : nullptr;
}

APawn* UMelodiaPartySubsystem::EnsurePawn(const int32 Index, const FTransform& SpawnAt)
{
	if (SpawnedPawns.IsValidIndex(Index) && IsValid(SpawnedPawns[Index]))
	{
		return SpawnedPawns[Index];
	}
	if (!PartyPawnClasses.IsValidIndex(Index))
	{
		return nullptr;
	}
	UClass* PawnClass = PartyPawnClasses[Index].LoadSynchronous();
	if (!PawnClass)
	{
		return nullptr;
	}
	UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr;
	if (!World)
	{
		return nullptr;
	}
	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
	APawn* NewPawn = World->SpawnActor<APawn>(PawnClass, SpawnAt, Params);
	RegisterPawn(NewPawn, Index);
	return NewPawn;
}

void UMelodiaPartySubsystem::ParkPawn(APawn* Pawn, const bool bParked)
{
	if (!Pawn)
	{
		return;
	}
	Pawn->SetActorHiddenInGame(bParked);
	Pawn->SetActorEnableCollision(!bParked);
	Pawn->SetActorTickEnabled(!bParked);
	TArray<USkeletalMeshComponent*> Meshes;
	Pawn->GetComponents<USkeletalMeshComponent>(Meshes);
	for (USkeletalMeshComponent* MeshComp : Meshes)
	{
		MeshComp->bPauseAnims = bParked;
	}
}

void UMelodiaPartySubsystem::SwitchToNext(APlayerController* PC)
{
	if (!PC || PartyPawnClasses.Num() < 2 || !bSirMelodiousExplorationUnlocked)
	{
		return;
	}
	const int32 NextIndex = (ActiveIndex + 1) % PartyPawnClasses.Num();
	SetActiveIndex(NextIndex, PC);
}

void UMelodiaPartySubsystem::SetSirMelodiousExplorationUnlocked(const bool bUnlocked)
{
	bSirMelodiousExplorationUnlocked = bUnlocked;
	if (!bSirMelodiousExplorationUnlocked && ActiveIndex != 0)
	{
		ActiveIndex = 0;
	}
}

void UMelodiaPartySubsystem::SetActiveIndex(const int32 NewIndex, APlayerController* PC)
{
	if (!PC || NewIndex == ActiveIndex)
	{
		return;
	}

	APawn* OldPawn = PC->GetPawn();
	FTransform HandoffAt = OldPawn ? OldPawn->GetActorTransform() : FTransform::Identity;
	HandoffAt.AddToTranslation(FVector(0.0f, 0.0f, 150.0f));
	HandoffAt.SetScale3D(FVector::OneVector);

	APawn* NewPawn = EnsurePawn(NewIndex, HandoffAt);
	if (!NewPawn)
	{
		return;
	}

	if (NewPawn != OldPawn)
	{
		NewPawn->SetActorTransform(HandoffAt, false, nullptr, ETeleportType::TeleportPhysics);
	}

	ParkPawn(NewPawn, false);

	// Hold the view on the old pawn through the possess, then blend to the new one.
	if (OldPawn)
	{
		PC->SetViewTarget(OldPawn);
	}
	PC->Possess(NewPawn);
	PC->SetViewTargetWithBlend(NewPawn, 0.6f, VTBlend_EaseInOut, 2.0f);

	if (OldPawn && OldPawn != NewPawn)
	{
		ParkPawn(OldPawn, true);
	}

	ActiveIndex = NewIndex;
}
