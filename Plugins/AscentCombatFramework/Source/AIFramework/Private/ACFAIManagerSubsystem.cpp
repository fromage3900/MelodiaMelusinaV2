// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFAIManagerSubsystem.h"
#include "AIController.h"
#include "BrainComponent.h"
#include "GameFramework/Pawn.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/AudioComponent.h"

// ==================== REGISTRATION ====================

void UACFAIManagerSubsystem::RegisterAI(AAIController* Controller)
{
	if (Controller && !RegisteredAIs.Contains(Controller))
	{
		RegisteredAIs.Add(Controller);
	}
}

void UACFAIManagerSubsystem::UnregisterAI(AAIController* Controller)
{
	if (Controller)
	{
		RegisteredAIs.Remove(Controller);
		InBattleAIs.Remove(Controller);
		PausedAIs.Remove(Controller);
	}
}

TArray<AAIController*> UACFAIManagerSubsystem::GetAllRegisteredAIs() const
{
	TArray<AAIController*> Result;
	for (AAIController* AI : RegisteredAIs)
	{
		if (AI)
		{
			Result.Add(AI);
		}
	}
	return Result;
}

// ==================== BATTLE MANAGEMENT ====================

void UACFAIManagerSubsystem::AddAIToBattle(AAIController* Controller)
{
	if (Controller && !InBattleAIs.Contains(Controller))
	{
		InBattleAIs.AddUnique(Controller);
		OnAIAddedToBattle.Broadcast(Controller);
	}
}

void UACFAIManagerSubsystem::RemoveAIFromBattle(AAIController* Controller)
{
	if (Controller && InBattleAIs.Contains(Controller))
	{
		InBattleAIs.Remove(Controller);
		OnAIRemovedFromBattle.Broadcast(Controller);
	}
}

void UACFAIManagerSubsystem::ClearAllAIsFromBattle()
{
	const TArray<AAIController*> copy = InBattleAIs;
	InBattleAIs.Empty();
	for (AAIController* AI : copy)
	{
		if (AI)
		{
			OnAIRemovedFromBattle.Broadcast(AI);
		}
	}

}

TArray<AAIController*> UACFAIManagerSubsystem::GetInBattleAIs() const
{
	TArray<AAIController*> Result;
	for (AAIController* AI : InBattleAIs)
	{
		if (AI)
		{
			Result.Add(AI);
		}
	}
	return Result;
}

bool UACFAIManagerSubsystem::IsAIInBattle(AAIController* Controller) const
{
	return Controller && InBattleAIs.Contains(Controller);
}

// ==================== PAUSE/RESUME ====================

void UACFAIManagerSubsystem::PauseNonBattleAIs(const FString& Reason)
{
	PausedAIs.Empty();

	for (AAIController* AI : RegisteredAIs)
	{
		if (!AI || InBattleAIs.Contains(AI))
		{
			continue;
		}

		// Pause brain
		if (UBrainComponent* Brain = AI->GetBrainComponent())
		{
			Brain->PauseLogic(Reason);
		}

		// Hide and disable collision on pawn
		if (APawn* Pawn = AI->GetPawn())
		{
			Pawn->SetActorHiddenInGame(true);
			Pawn->SetActorEnableCollision(false);
			Pawn->SetActorTickEnabled(false);

			// SetActorTickEnabled only stops the actor tick; the skeletal mesh keeps
			// ticking, so the walk-cycle animation (and its footstep anim-notify sounds)
			// would keep firing on a hidden AI. Pause the mesh anims to silence it.
			Pawn->ForEachComponent<USkeletalMeshComponent>(false, [](USkeletalMeshComponent* Mesh)
			{
				Mesh->bPauseAnims = true;
				Mesh->SetComponentTickEnabled(false);
			});

			// Cut any currently-playing audio (sustained loops) immediately.
			Pawn->ForEachComponent<UAudioComponent>(false, [](UAudioComponent* AudioComp)
			{
				AudioComp->Stop();
			});
		}

		PausedAIs.Add(AI);
	}
}

void UACFAIManagerSubsystem::ResumeAllAIs(const FString& Reason)
{
	for (AAIController* AI : PausedAIs)
	{
		if (!AI)
		{
			continue;
		}

		// Resume brain
		if (UBrainComponent* Brain = AI->GetBrainComponent())
		{
			Brain->ResumeLogic(Reason);
		}

		// Show and enable collision on pawn
		if (APawn* Pawn = AI->GetPawn())
		{
			Pawn->SetActorHiddenInGame(false);
			Pawn->SetActorEnableCollision(true);
			Pawn->SetActorTickEnabled(true);

			// Restore mesh animation paused in PauseNonBattleAIs.
			Pawn->ForEachComponent<USkeletalMeshComponent>(false, [](USkeletalMeshComponent* Mesh)
			{
				Mesh->bPauseAnims = false;
				Mesh->SetComponentTickEnabled(true);
			});
		}
	}

	PausedAIs.Empty();
}
