// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Components/ACFAIManagerComponent.h"
#include "ACFAITypes.h"
#include "Logging.h"
#include <Net/UnrealNetwork.h>
#include "ACFAIManagerSubsystem.h"
#include "Engine/World.h"


// Sets default values for this component's properties
UACFAIManagerComponent::UACFAIManagerComponent()
{
	// Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
	// off to improve performance if you don't need them.
	PrimaryComponentTick.bCanEverTick = true;
	SetIsReplicatedByDefault(true);


	// ...
}

void UACFAIManagerComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(UACFAIManagerComponent, battleState);
}
// Called when the game starts
void UACFAIManagerComponent::BeginPlay()
{
	Super::BeginPlay();
	LegacyAIStateToTagMap = {
		{ EAIState::EWait, UGameplayTagsManager::Get().RequestGameplayTag(ACF::AIWait) },
		{ EAIState::EFollowLeader, UGameplayTagsManager::Get().RequestGameplayTag(ACF::AIFollowLead) },
		{ EAIState::EPatrol, UGameplayTagsManager::Get().RequestGameplayTag(ACF::AIPatrol) },
		{ EAIState::EReturnHome, UGameplayTagsManager::Get().RequestGameplayTag(ACF::AIReturnHome) },
		{ EAIState::EBattle, UGameplayTagsManager::Get().RequestGameplayTag(ACF::AICombat) }
	};

	if (GetOwner()->HasAuthority())
	{
		if (UACFAIManagerSubsystem* Subsystem = GetWorld()->GetSubsystem<UACFAIManagerSubsystem>())
		{
			Subsystem->OnAIAddedToBattle.AddDynamic(this, &UACFAIManagerComponent::HandleBattleStateChanged);
			Subsystem->OnAIRemovedFromBattle.AddDynamic(this, &UACFAIManagerComponent::HandleBattleStateChanged);

		}

	}
}



// Called every frame
void UACFAIManagerComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	UpdateTickets(DeltaTime);
}

void UACFAIManagerComponent::UpdateTickets(float DeltaTime)
{

	for (FACFAITicket& Ticket : ActiveTickets) {
		Ticket.TimeRemaining -= DeltaTime;
	}
	ActiveTickets.RemoveAll([](const FACFAITicket& Ticket) { return Ticket.TimeRemaining <= 0.f; });
}

bool UACFAIManagerComponent::HasTicket(AController* AIController) const
{
	return ActiveTickets.Contains(AIController);
}

bool UACFAIManagerComponent::RequestTicket(AActor* Target, AController* AIController, float Duration)
{
	if (!Target || !AIController)
		return false;

	int32 CurrentCount = 0;
	for (const FACFAITicket& Ticket : ActiveTickets) {
		if (Ticket.Target == Target && !(Ticket.TimeRemaining <= 0.f)) {
			++CurrentCount;
		}
	}

	if (CurrentCount >= MaxAttackersPerTarget) {
		return false;
	}

	ActiveTickets.Add(FACFAITicket(Target, AIController, Duration));
	return true;
}

void UACFAIManagerComponent::ReleaseTicket(AController* AIController)
{
	ActiveTickets.RemoveAll([&](const FACFAITicket& Ticket) { return Ticket.AIController == AIController; });
}

void UACFAIManagerComponent::AddAIToBattle(AAIController* contr)
{
	if (UACFAIManagerSubsystem* Subsystem = GetWorld()->GetSubsystem<UACFAIManagerSubsystem>())
	{
		Subsystem->AddAIToBattle(contr);
	}

}

void UACFAIManagerComponent::RemoveAIFromBattle(AAIController* contr)
{
	if (UACFAIManagerSubsystem* Subsystem = GetWorld()->GetSubsystem<UACFAIManagerSubsystem>())
	{
		Subsystem->RemoveAIFromBattle(contr);
	}

}

void UACFAIManagerComponent::HandleBattleStateChanged(AAIController* contr)
{
	UpdateBattleState();
}


void UACFAIManagerComponent::UpdateBattleState()
{
	int32 InBattleCount = 0;
	if (UACFAIManagerSubsystem* Subsystem = GetWorld()->GetSubsystem<UACFAIManagerSubsystem>())
	{
		InBattleCount = Subsystem->GetInBattleAICount();
	}

	const EBattleState state = InBattleCount > 0 ? EBattleState::EBattle : EBattleState::EExploration;
	if (battleState != state)
	{
		battleState = state;
		OnBattleStateChanged.Broadcast(battleState);
	}
}

void UACFAIManagerComponent::OnRep_BattleState()
{
	OnBattleStateChanged.Broadcast(battleState);
}

FGameplayTag UACFAIManagerComponent::GetAIStateTag(EAIState aiState)
{

	if (LegacyAIStateToTagMap.Contains(aiState)) {
		return *LegacyAIStateToTagMap.Find(aiState);
	}

	return FGameplayTag();
}
