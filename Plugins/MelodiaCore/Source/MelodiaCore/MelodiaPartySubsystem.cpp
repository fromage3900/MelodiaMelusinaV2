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
	// Owner canon 2026-10-19/20: the pawn left behind on a party switch must
	// not vanish. Parked is inert-but-present: no collision, no actor tick,
	// idle animation keeps playing, and the pawn is never hidden.
	Pawn->SetActorHiddenInGame(false);
	Pawn->SetActorEnableCollision(!bParked);
	Pawn->SetActorTickEnabled(!bParked);
	TArray<USkeletalMeshComponent*> Meshes;
	Pawn->GetComponents<USkeletalMeshComponent>(Meshes);
	for (USkeletalMeshComponent* MeshComp : Meshes)
	{
		MeshComp->bPauseAnims = false;
	}
}

void UMelodiaPartySubsystem::SwitchToNext(APlayerController* PC)
{
	if (!PC || PartyPawnClasses.Num() < 2 || !bSirMelodiousExplorationUnlocked)
	{
		// Ctrl reaches here through C++ bindings only: the Sir flight pawn's own
		// IA_Flight_PartySwitch (switch-back) and the bootstrap subsystem's
		// pawn-level hook (UMelodiaJRPGPartyBootstrapSubsystem ~ LeftControl on
		// every non-flight, non-smoke pawn). The stock Melusina pawn and controller
		// Blueprints never bound this before 2026-10-19 — the earlier "wired end
		// to end" note here was aspirational, not true. The only reason a press
		// can do nothing is one of these three conditions, and all three used to
		// fail silently, which was indistinguishable from an unwired key. Name the
		// actual cause instead. Deliberately does not unlock itself: exploration
		// flight is gated on the stock JRPG party actually containing Sir, and
		// that is a gameplay decision, not a wiring fallback.
		UE_LOG(LogTemp, Warning,
			TEXT("Melodia party switch declined: no_controller=%d roster_size=%d sir_unlocked=%d "
				 "(sir_unlocked turns true only once stock partyMembers confirms Sir was recruited)"),
			PC ? 0 : 1, PartyPawnClasses.Num(), bSirMelodiousExplorationUnlocked ? 1 : 0);
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
	// The pawn being left is the roster member at ActiveIndex. Index 0 is spawned by the game mode
	// (stock BP_JRPGCharacterBase child) and never self-registers, so without this Sir -> Melusina
	// finds no pawn and no class for slot 0 and the switch back silently does nothing.
	if (OldPawn && !(SpawnedPawns.IsValidIndex(ActiveIndex) && IsValid(SpawnedPawns[ActiveIndex])))
	{
		RegisterPawn(OldPawn, ActiveIndex);
	}
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
