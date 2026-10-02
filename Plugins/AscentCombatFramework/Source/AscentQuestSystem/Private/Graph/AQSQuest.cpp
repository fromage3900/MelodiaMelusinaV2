// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Graph/AQSQuest.h"
#include "AGSGraph.h"
#include "AGSGraphNode.h"
#include "Graph/AQSBaseNode.h"
#include "Graph/AQSEdge.h"
#include "Graph/AQSObjectiveNode.h"
#include "Graph/AQSQuestFailedNode.h"
#include "Graph/AQSQuestSuccededNode.h"
#include "Graph/AQSStartQuestNode.h"
#include <WorldPartition/DataLayer/DataLayerAsset.h>
#include <WorldPartition/DataLayer/DataLayerInstance.h>
#include <WorldPartition/DataLayer/DataLayerManager.h>
#include <GameplayTagContainer.h>

bool UAQSQuest::ActivateNode(class UAGSGraphNode* node)
{

	return Super::ActivateNode(node);
}

UAQSQuest::UAQSQuest()
{
	NodeType = UAQSBaseNode::StaticClass();
	EdgeType = UAQSEdge::StaticClass();
	bAllowCycles = true;
}

void UAQSQuest::CompleteQuest(bool bSucceded)
{
	OnQuestEnded.Broadcast(GetQuestTag(), bSucceded);
}

bool UAQSQuest::HasActiveObjectiveByTag(const FGameplayTag& objectiveTag) const
{
	FGuid outID;
	if (FromTagToID(objectiveTag, outID)) {
		return HasActiveObjective(outID);
	}
	return false;
}

bool UAQSQuest::HasActiveObjective(const FGuid& objectiveID) const
{
	for (UAGSGraphNode* node : GetActiveNodes()) {
		UAQSObjectiveNode* objective = Cast<UAQSObjectiveNode>(node);

		if (objective && objective->GetNodeId() == objectiveID) {
			return true;
		}
	}
	return false;
}

UAQSQuestSuccededNode* UAQSQuest::GetQuestSucceededNode() const
{
	for (UAGSGraphNode* Node : GetAllNodes()) {
		UAQSQuestSuccededNode* SucceededNode = Cast<UAQSQuestSuccededNode>(Node);
		if (SucceededNode) {
			return SucceededNode;
		}
	}
	return nullptr;
}

UAQSQuestFailedNode* UAQSQuest::GetQuestFailedNode() const
{
	for (UAGSGraphNode* Node : GetAllNodes()) {
		UAQSQuestFailedNode* FailedNode = Cast<UAQSQuestFailedNode>(Node);
		if (FailedNode) {
			return FailedNode;
		}
	}
	return nullptr;
}

UAQSObjectiveNode* UAQSQuest::GetActiveObjectiveNode(const FGuid& objectiveId) const
{
	for (UAGSGraphNode* node : GetActiveNodes()) {
		UAQSObjectiveNode* objective = Cast<UAQSObjectiveNode>(node);

		if (objective && objective->GetNodeId() == objectiveId) {
			return objective;
		}
	}
	return nullptr;
}

UAQSQuestObjective* UAQSQuest::GetActiveObjective(const FGuid& objectiveId) const
{
	for (const auto& obj : GetActiveNodes()) {
		UAQSObjectiveNode* objNode = Cast<UAQSObjectiveNode>(obj);
		if (objNode && objNode->GetNodeId() == objectiveId) {
			return objNode->GetQuestObjective();
		}
	}
	return nullptr;
}

UAQSObjectiveNode* UAQSQuest::GetObjectiveNode(const FGuid& objectiveId) const
{
	for (const auto& obj : GetAllNodes()) {
		UAQSObjectiveNode* objNode = Cast<UAQSObjectiveNode>(obj);
		if (objNode && objNode->GetNodeId() == objectiveId) {
			return objNode;
		}
	}
	return nullptr;
}

TArray<UAQSQuestObjective*> UAQSQuest::GetAllActiveObjectives() const
{
	TArray<UAQSQuestObjective*> objectives;
	for (const auto& obj : GetActiveNodes()) {
		const UAQSObjectiveNode* objNode = Cast<UAQSObjectiveNode>(obj);
		if (objNode) {
			objectives.Add(objNode->GetQuestObjective());
		}
		else {
			UE_LOG(LogTemp, Warning, TEXT("Wrong Node types in graph! -  UAQSQuest::GetAllActiveObjectives"));
		}
	}
	return objectives;
}

UAQSQuestObjective* UAQSQuest::GetObjectiveByTag(const FGameplayTag& objectiveTag) const
{
	for (const auto& obj : GetAllNodes()) {
		const UAQSObjectiveNode* objNode = Cast<UAQSObjectiveNode>(obj);
		if (objNode && objNode->GetObjectiveTag() == objectiveTag) {
			return objNode->GetQuestObjective();
		}
	}
	return nullptr;
}

UAQSQuestObjective* UAQSQuest::GetObjectiveById(const FGuid& objectiveId) const
{

	const UAQSObjectiveNode* objNode = Cast<UAQSObjectiveNode>(GetNodeById(objectiveId));
	if (objNode) {
		return objNode->GetQuestObjective();
	}

	return nullptr;
}

bool UAQSQuest::StartQuest(class APlayerController* inController, TObjectPtr<UAQSQuestManagerComponent> inQuestManager, bool bActivateChildNodes /*= true*/)
{
	
	if(bIsStarted) {
		UE_LOG(LogTemp, Warning, TEXT("Quest already started! - UAQSQuest::StartQuest"));
		return false;
	}

	controller = inController;
	questManager = inQuestManager;
	DeactivateAllNodes();
	CompletedObjectives.Empty();
	bInActivateChildrenNode = bActivateChildNodes;

	if (inController && LayerToLoad) {
		UDataLayerManager::GetDataLayerManager(inController)->OnDataLayerInstanceRuntimeStateChanged.AddDynamic(this, &UAQSQuest::OnDataLayerStateChanged);
		UDataLayerManager::GetDataLayerManager(inController)->SetDataLayerRuntimeState(LayerToLoad, EDataLayerRuntimeState::Loaded);
		UDataLayerManager::GetDataLayerManager(inController)->SetDataLayerRuntimeState(LayerToLoad, EDataLayerRuntimeState::Activated);

	}
	else {
		return StartGraph();
	}

	bIsStarted = true;
	return true;
}

void UAQSQuest::OnDataLayerStateChanged(const UDataLayerInstance* LayerInst, EDataLayerRuntimeState State)
{
	if (State == EDataLayerRuntimeState::Loaded && LayerInst == UDataLayerManager::GetDataLayerManager(this)->GetDataLayerInstanceFromAsset(LayerToLoad)) {
		StartGraph();
	}
}

bool UAQSQuest::StartGraph()
{
	if (bInActivateChildrenNode) {
		for (const UAGSGraphNode* root : RootNodes) {
			const UAQSStartQuestNode* startNode = Cast<UAQSStartQuestNode>(root);
			if (startNode) {
				for (const auto& node : startNode->ChildrenNodes) {
					UAQSObjectiveNode* objective = Cast<UAQSObjectiveNode>(node);
					if (objective) {
						ActivateNode(objective);
					}
				}

				OnQuestStarted.Broadcast(QuestTag);
				return true;
			}
			else {
				UE_LOG(LogTemp, Error, TEXT("No Root nodes on quest -  UAQSQuest::StartQuest"));
			}
		}
	}
	else {
		return true;
	}
	return false;
}

void UAQSQuest::SetQuestTracked(bool inTracked)
{
	bIsTracked = inTracked;
	for (UAGSGraphNode* node : GetActiveNodes()) {
		UAQSObjectiveNode* objective = Cast<UAQSObjectiveNode>(node);
		if (objective) {
			objective->SetIsTracked(bIsTracked);
		}
	}
}

bool UAQSQuest::CompleteBranchedObjectiveByTag(const FGameplayTag& objectiveTag, const TArray<FName>& transitionFilters)
{
	FGuid outID;
	if (FromTagToID(objectiveTag, outID)) {
		return CompleteBranchedObjective(outID, transitionFilters);
	}

	return false;
}

bool UAQSQuest::CompleteBranchedObjective(const FGuid& objectiveID, const TArray<FName>& optionalTransitionFilters /*= TArray<FName>()*/)
{
	UAQSObjectiveNode* objective = Cast<UAQSObjectiveNode>(GetNodeById(objectiveID));

	if (objective && objective->IsNodeActivated()) {
		if (objective->TryToComplete()) {
			DeactivateNode(objective);
			CompletedObjectives.Add(objectiveID);
			for (auto childNode : objective->ChildrenNodes) {
				UAQSEdge* aqsEdge = Cast<UAQSEdge>(objective->GetEdge(childNode));

				if (!aqsEdge) {
					UE_LOG(LogTemp, Error, TEXT("Invalid Edge! -  UAQSQuest::CompleteObjective"));
				}

				if (optionalTransitionFilters.Num() == 0 || optionalTransitionFilters.Contains(aqsEdge->GetTransitionName())) {

					UAQSBaseNode* aqsChild = Cast<UAQSBaseNode>(childNode);
					if (aqsChild && aqsChild->CanBeActivated()) {
						ActivateNode(aqsChild);
					}
				}
			}
			return true;
		}

	}
	return false;
}

bool UAQSQuest::FromTagToID(const FGameplayTag& objectiveTag, FGuid& outID) const
{
	for (UAGSGraphNode* node : GetAllNodes()) {
		UAQSObjectiveNode* objective = Cast<UAQSObjectiveNode>(node);
		if (objective && objective->GetObjectiveTag() == objectiveTag) {
			outID = objective->GetNodeId();
			return true;
		}
	}
	return false;
}

bool UAQSQuest::CompleteObjectiveByTag(const FGameplayTag& objectiveTag)
{
	FGuid outID;
	if (FromTagToID(objectiveTag, outID)) {
		return CompleteObjective(outID);
	}

	return false;
}

bool UAQSQuest::CompleteObjective(const FGuid& objectiveID)
{

	UAQSObjectiveNode* objective = Cast<UAQSObjectiveNode>(GetNodeById(objectiveID));

 	if (objective && objective->IsNodeActivated()) {
		if (objective->TryToComplete()) {
			DeactivateNode(objective);
			CompletedObjectives.Add(objectiveID);
			for (auto childNode : objective->ChildrenNodes) {
				UAQSEdge* aqsEdge = Cast<UAQSEdge>(objective->GetEdge(childNode));
				if (!aqsEdge) {
					UE_LOG(LogTemp, Error, TEXT("Invalid Edge! -  UAQSQuest::CompleteObjective"));
				}
				UAQSBaseNode* aqsChild = Cast<UAQSBaseNode>(childNode);
				if (aqsChild && aqsChild->CanBeActivated()) {
					ActivateNode(aqsChild);
				}
			}
			return true;
		}
	}


	return false;
}

void UAQSQuest::ResetQuest()
{
	for (UAGSGraphNode* node : GetActiveNodes()) {
		UAQSObjectiveNode* objectiveNode = Cast<UAQSObjectiveNode>(node);

		if (objectiveNode) {
			objectiveNode->InterruptObjective();
			DeactivateNode(node);
		}
	}
}
