// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "AQSQuestObjective.h"
#include "AQSQuestFunctionLibrary.h"
#include "AQSQuestManagerComponent.h"
#include <Kismet/KismetSystemLibrary.h>
#include <Engine/StreamableManager.h>
#include <GameFramework/Actor.h>

UAQSQuestObjective::UAQSQuestObjective()
{
	TargetRefType = ETargetReferenceType::ESoftRef;
	ObjectiveName = FText::FromString("Default Name");
	/*    ObjectiveDescription = "";*/
}

TArray<class AActor*> UAQSQuestObjective::GetObjectiveTargetsActors() const
{
	TArray<class AActor*> outActors;
	for (const UAQSQuestTargetComponent* targetComp : questTargets) {
		if (targetComp) {
			outActors.Add(targetComp->GetOwner());
		}
	}
	return outActors;
}

TArray<TSoftObjectPtr<AActor>> UAQSQuestObjective::GetObjectiveTargetsSoftRef() const
{
	return ReferencedActors;
}

APlayerController* UAQSQuestObjective::GetLocalPlayerController() const
{
	if (nodeOwner) {
		return nodeOwner->GetPlayerController();
	}
	return nullptr;
}

void UAQSQuestObjective::CompleteObjective()
{
	UAQSQuestManagerComponent* questMan = GetLocalQuestManager();
	if (questMan) {
		questMan->ServerCompleteObjective(GetObjectiveId());
	}
}

void UAQSQuestObjective::Internal_OnObjectiveStarted(UAQSObjectiveNode* inNodeOwner)
{
	nodeOwner = inNodeOwner;

	FillTargetsRef();

	if (GetLocalPlayerController()->HasAuthority()) {
		// In standalone / listen server, this pawn may also be locally controlled
		OnObjectiveStarted();
		if (GetLocalPlayerController()->IsLocalController()) {
			// Execute local feedback logic too
			ClientOnObjectiveStarted();
		}
	}
	else {
		ClientOnObjectiveStarted();
	}
}

void UAQSQuestObjective::Internal_OnObjectiveEnded(bool bInterrupted)
{
	if (bInterrupted) {
		if (GetLocalPlayerController()->HasAuthority()) {
			// In standalone / listen server, this pawn may also be locally controlled
			OnObjectiveInterrupted();
			if (GetLocalPlayerController()->IsLocalController()) {
				// Execute local feedback logic too
				ClientOnObjectiveInterrupted();
			}
		}
		else {
			ClientOnObjectiveInterrupted();
		}

	}
	else {
		if (GetLocalPlayerController()->HasAuthority()) {
			// In standalone / listen server, this pawn may also be locally controlled
			OnObjectiveCompleted();
			if (GetLocalPlayerController()->IsLocalController()) {
				// Execute local feedback logic too
				ClientOnObjectiveCompleted();
			}
		}
		else {
			ClientOnObjectiveCompleted();
		}
	}

}

void UAQSQuestObjective::FillTargetsRef()
{
	questTargets.Empty();
	const UAQSQuestManagerComponent* questMan = UAQSQuestFunctionLibrary::GetQuestManager(this);

	switch (TargetRefType) {
	case ETargetReferenceType::ETag:
		if (questMan) {
			questTargets = questMan->GetAllTargetsWithTags(ReferencedTargets);
		}
		else {
			UE_LOG(LogTemp, Error, TEXT("Add Quest Manager Component to your player controller! - AQSQuestObjective::Internal_OnObjectiveStarted"));
		}
		break;
	case ETargetReferenceType::ESoftRef:
		FStreamableManager StreamableManager;

		for (const TSoftObjectPtr<AActor>& actor : ReferencedActors) {
			if (actor) {
				//                 if (bForceLoadReferencedActors) {
				//                     actor->SetIsSpatiallyLoaded(false);
				//                 }       
				UAQSQuestTargetComponent* targetComp = actor->FindComponentByClass<UAQSQuestTargetComponent>();
				if (targetComp) {
					questTargets.Add(targetComp);
				}
				else {
					UE_LOG(LogTemp, Error, TEXT("Add Quest Target Component to your target actors! - AQSQuestObjective::Internal_OnObjectiveStarted"));
				}
			}
			else {
				UE_LOG(LogTemp, Error, TEXT("Can't Start the quest"));

			}
		}
	}
}

void UAQSQuestObjective::OnObjectiveStarted_Implementation()
{
}

void UAQSQuestObjective::ClientOnObjectiveStarted_Implementation()
{
}

void UAQSQuestObjective::OnObjectiveCompleted_Implementation()
{
}

void UAQSQuestObjective::ClientOnObjectiveCompleted_Implementation()
{
}

void UAQSQuestObjective::OnObjectiveUpdated_Implementation()
{
}

void UAQSQuestObjective::OnObjectiveInterrupted_Implementation()
{
}

void UAQSQuestObjective::ClientOnObjectiveInterrupted_Implementation()
{
}

void UAQSQuestObjective::SetCurrentRepetitions(int32 currentRep)
{
	if (currentRep < GetRepetitions()) {
		nodeOwner->SetCurrentRepetitions(currentRep);
	}
}

UAQSQuestManagerComponent* UAQSQuestObjective::GetLocalQuestManager() const
{
	return GetLocalPlayerController() ? GetLocalPlayerController()->FindComponentByClass<UAQSQuestManagerComponent>() : nullptr;
}
