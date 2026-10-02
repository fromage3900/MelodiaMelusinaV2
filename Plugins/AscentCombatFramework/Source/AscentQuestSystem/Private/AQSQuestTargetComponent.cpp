// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "AQSQuestTargetComponent.h"
#include "AQSQuestFunctionLibrary.h"
#include "AQSQuestManagerComponent.h"
#include "Graph/AQSObjectiveNode.h"
#include "Net/UnrealNetwork.h"

#include "UObject/CoreNet.h"

// Sets default values for this component's properties
UAQSQuestTargetComponent::UAQSQuestTargetComponent()
{
    // Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
    // off to improve performance if you don't need them.
    PrimaryComponentTick.bCanEverTick = false;
    SetIsReplicatedByDefault(true);

    // ...
}

void UAQSQuestTargetComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(UAQSQuestTargetComponent, bIsCurrentlyTargetOfObjective);
    DOREPLIFETIME(UAQSQuestTargetComponent, currentlyTargetingObjective);
    DOREPLIFETIME(UAQSQuestTargetComponent, currentlyTargetingQuest);
}

void UAQSQuestTargetComponent::CompleteObjective(const FGuid& objectiveToComplete)
{
    UAQSQuestManagerComponent* questManager = UAQSQuestFunctionLibrary::GetQuestManager(this);
    if (questManager) {
        questManager->ServerCompleteObjective(objectiveToComplete);
    } else {
        UE_LOG(LogTemp, Error, TEXT("Add Quest Manager Component to your player controller! - UAQSQuestTargetComponent::CompleteObjective"));
        return;
    }
}



void UAQSQuestTargetComponent::CompleteBranchedObjective(const FGuid& objectiveToComplete, const TArray<FName>& transitionFilters)
{
    UAQSQuestManagerComponent* questManager = UAQSQuestFunctionLibrary::GetQuestManager(this);
    if (questManager) {
        questManager->ServerCompleteBranchedObjective(objectiveToComplete, transitionFilters);
    } else {
        UE_LOG(LogTemp, Error, TEXT("Add Quest Manager Component to your player controller! - UAQSQuestTargetComponent::CompleteBranchedObjective"));
        return;
    }
}

void UAQSQuestTargetComponent::OnObjectiveStarted_Implementation(const FGuid& objectiveId, const FGameplayTag& questTag)
{
}

void UAQSQuestTargetComponent::OnObjectiveCompleted_Implementation(const FGuid& objectiveId, const FGameplayTag& questTag)
{
}

void UAQSQuestTargetComponent::OnObjectiveUpdated_Implementation(const FGuid& objectiveId, const FGameplayTag& questTag)
{
}

void UAQSQuestTargetComponent::OnObjectiveInterrupted_Implementation(const FGuid& objectiveId, const FGameplayTag& questTag)
{
}

void UAQSQuestTargetComponent::OnTrackedChanged_Implementation(bool bNewTracked)
{
}

void UAQSQuestTargetComponent::DispatchObjectiveUpdated(const FGuid& objectiveId, const FGameplayTag& questTag, EQuestUpdateType objectiveUpdate, bool inTracked)
{
    
    switch (objectiveUpdate) {
    case EQuestUpdateType::EStarted:
        bIsCurrentlyTargetOfObjective = true;
        currentlyTargetingQuest = questTag;
        currentlyTargetingObjective = objectiveId;
      
        OnReferencingObjectiveStarted.Broadcast(objectiveId, questTag);
        OnObjectiveStarted(objectiveId, questTag);
     
        break;
    case EQuestUpdateType::EUpdated:
        SetTracked(inTracked);
        OnReferencingObjectiveUpdated.Broadcast(objectiveId, questTag);
        OnObjectiveUpdated(objectiveId, questTag);      
        break;
    case EQuestUpdateType::ECompleted:
        bIsCurrentlyTargetOfObjective = false;
        currentlyTargetingQuest = FGameplayTag();
        currentlyTargetingObjective = FGuid(); 
        SetTracked(false);
        OnReferencingObjectiveCompleted.Broadcast(objectiveId, questTag);
        OnObjectiveCompleted(objectiveId, questTag);
        break;
    case EQuestUpdateType::EInterrupted:
        bIsCurrentlyTargetOfObjective = false;
        currentlyTargetingQuest = FGameplayTag();
        currentlyTargetingObjective = FGuid(); 
        SetTracked(false);
        OnReferencingObjectiveInterrupted.Broadcast(objectiveId, questTag);
        OnObjectiveInterrupted(objectiveId, questTag);
        break;
    }


     
    
}

void UAQSQuestTargetComponent::ClientDispatchObjectiveUpdated(const FGuid& objectiveId, const FGameplayTag& questTag, EQuestUpdateType objectiveUpdate, bool inTracked)
{

     SetTracked(inTracked);
}

void UAQSQuestTargetComponent::SetTracked(bool inTracked)
{
    if (inTracked != bTracked) {
        bTracked = inTracked;
        OnTrackedChanged(bTracked);
        OnTrackedStatusChanged.Broadcast(bTracked);
    }
}

// Called when the game starts
void UAQSQuestTargetComponent::BeginPlay()
{
    Super::BeginPlay();
    UAQSQuestManagerComponent* questMan = UAQSQuestFunctionLibrary::GetQuestManager(this);
    if (questMan && TargetTag != FGameplayTag()) {
        questMan->RegisterTarget(this);
    } 
}
