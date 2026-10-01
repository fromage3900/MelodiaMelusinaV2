// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.


#include "Components/ACFBaseGroupComponent.h"
#include "Net/UnrealNetwork.h"
#include "Components/ACFTeamComponent.h"
#include <Engine/AssetManager.h>
#include <Engine/World.h>
#include <GameFramework/Pawn.h>
#include <Kismet/GameplayStatics.h>
#include "ACFAITypes.h"
#include "Data/ACFCharacterInitializerComponent.h"
#include "Actors/ACFCharacter.h"
#include "Logging.h"


UACFBaseGroupComponent::UACFBaseGroupComponent()
{
	SetIsReplicatedByDefault(true);
	PrimaryComponentTick.bCanEverTick = false;

}

void UACFBaseGroupComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(UACFBaseGroupComponent, AICharactersInfo);
}

void UACFBaseGroupComponent::OnComponentLoaded_Implementation()
{
	for (int32 index = 0; index < AICharactersInfo.Num(); index++) {
		FAIAgentsInfo& agent = AICharactersInfo[index];
		TArray<AActor*> foundActors;
		UGameplayStatics::GetAllActorsOfClassWithTag(this, agent.characterClass, agent.Guid, foundActors);
		if (foundActors.Num() == 0) {
			UE_LOG(ACFAILog, Error, TEXT("Impossible to find actor"));
			continue;
		}
		agent.AICharacter = Cast<AACFCharacter>(foundActors[0]);
		InitAgent(agent, index);
	}
}

void UACFBaseGroupComponent::OnComponentSaved_Implementation()
{

}

void UACFBaseGroupComponent::OnChildDeath(const AACFCharacter* character)
{
	OnAgentDeath.Broadcast(character);
}


bool UACFBaseGroupComponent::GetAgentByIndex(int32 index, FAIAgentsInfo& outAgent) const
{
	if (AICharactersInfo.IsValidIndex(index)) {
		outAgent = AICharactersInfo[index];
		return true;
	}
	return false;
}

void UACFBaseGroupComponent::SpawnGroup_Implementation()
{
	if (bAlreadySpawned && !bCanSpawnMultitpleTimes) {
		return;
	}


	if (AICharactersInfo.Num() > 0) {
		// Already spawned!
		return;
	}

	Internal_SpawnGroup();
	bAlreadySpawned = true;
}

void UACFBaseGroupComponent::OnAIAssetsLoaded()
{
	bAlreadySpawned = true;
	OnAgentsSpawned.Broadcast();
}

void UACFBaseGroupComponent::HandleAgentDeath(class AACFCharacter* agent)
{
	OnChildDeath(agent);
}


void UACFBaseGroupComponent::Internal_SpawnGroup()
{

}

void UACFBaseGroupComponent::InitAgents()
{
	for (int32 index = 0; index < AICharactersInfo.Num(); index++) {
		if (AICharactersInfo.IsValidIndex(index)) {
			InitAgent(AICharactersInfo[index], index);
		}
	}
}

void UACFBaseGroupComponent::InitAgent(FAIAgentsInfo& agent, int32 childIndex)
{
	if (!agent.AICharacter) {
		ensure(false);
		return;
	}

	if (!agent.AICharacter->GetController()) {
		agent.AICharacter->SpawnDefaultController();
	}

	agent.characterClass = (agent.AICharacter->GetClass());



	if (!agent.GetController()) {
	//	UE_LOG(ACFAILog, Error, TEXT("invalid AI Controller! - UACFBaseGroupComponent::InitAgent"), *this->GetName());

		return;
	}
	const FName newGuid = agent.AICharacter->GetFName();
	agent.Guid = newGuid;
	if (!agent.AICharacter->Tags.Contains(newGuid)) {
		agent.AICharacter->Tags.Add(newGuid);
	}

	
	if (!agent.AICharacter->OnDeath.IsAlreadyBound(this, &UACFBaseGroupComponent::HandleAgentDeath)) {
		agent.AICharacter->OnDeath.AddDynamic(this, &UACFBaseGroupComponent::HandleAgentDeath);
	}
}

FGameplayTag UACFBaseGroupComponent::GetCombatTeam() const
{
	const UACFTeamComponent* teamComp = GetOwner()->FindComponentByClass<UACFTeamComponent>();
	if (teamComp) {
		return teamComp->GetTeam();
	}
	return FGameplayTag();
}
