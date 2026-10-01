// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Components/ACFGroupAIComponent.h"
#include "ACFAIController.h"
#include "Actors/ACFCharacter.h"
#include "Components/ACFTeamComponent.h"
#include "Components/ACFThreatManagerComponent.h"
#include "Game/ACFFunctionLibrary.h"
#include "Game/ACFPlayerController.h"
#include "Game/ACFTypes.h"
#include "Kismet/KismetMathLibrary.h"
#include "Net/UnrealNetwork.h"
#include <Engine/AssetManager.h>
#include <Engine/World.h>
#include <GameFramework/Pawn.h>
#include <Kismet/GameplayStatics.h>
#include <Kismet/KismetSystemLibrary.h>
#include <NavigationSystem.h>
#include <PrimitiveSceneProxy.h>
#include <GameFramework/Controller.h>
#include "ACFTeamManagerSubsystem.h"
#include <MeshElementCollector.h>
#include <SceneView.h>
#include <PrimitiveDrawingUtils.h>
#include <Logging.h>
#include "Components/CapsuleComponent.h"
#include "Components/ActorComponent.h"
#include "ACFAITypes.h"
#include "Data/ACFCharacterDataAsset.h"
#include "Components/ACFBaseGroupComponent.h"
#include "Data/ACFCharacterInitializerComponent.h"


// Sets default values for this component's properties
UACFGroupAIComponent::UACFGroupAIComponent()
{
	bInBattle = false;

	DefaultSpawnOffset = FVector2D(150.f, 150.f);
	AIToSpawn.Add(FAISpawnInfo());
}

void UACFGroupAIComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(UACFGroupAIComponent, groupLead);
	DOREPLIFETIME(UACFGroupAIComponent, bInBattle);

}
// Called when the game starts
void UACFGroupAIComponent::BeginPlay()
{
	Super::BeginPlay();
	SetReferences();
}

void UACFGroupAIComponent::SetReferences()
{
	groupLead = Cast<AActor>(GetOwner());
}

void UACFGroupAIComponent::OnComponentLoaded_Implementation()
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

void UACFGroupAIComponent::SendCommandToCompanions_Implementation(FGameplayTag command)
{
	Internal_SendCommandToAgents(command);
}

void UACFGroupAIComponent::Internal_SpawnGroup()
{
	if (AIToSpawn.Num() == 0) {
		UE_LOG(ACFAILog, Error, TEXT("%s NO AI to Spawn - AAIFGROUPPAWN::SpawnAGroup"), *this->GetName());
		return;
	}

	if (!GetOwner()->HasAuthority()) {
		return;
	}

	TArray<FSoftObjectPath> AssetsToLoad;
	for (const FAISpawnInfo& info : AIToSpawn) {
		if (info.AIClassBP.ToSoftObjectPath().IsValid()) {
			AssetsToLoad.Add(info.AIClassBP.ToSoftObjectPath());
			AssetsToLoad.Add(info.AIConfig.ToSoftObjectPath());
		}
	}

	StreamableHandle = UAssetManager::GetStreamableManager().RequestAsyncLoad(
		AssetsToLoad,
		FStreamableDelegate::CreateUObject(this, &UACFGroupAIComponent::OnAIAssetsLoaded),
		FStreamableManager::AsyncLoadHighPriority);
}

void UACFGroupAIComponent::OnAIAssetsLoaded()
{
	Super::OnAIAssetsLoaded();

	for (const FAISpawnInfo& aiSpawn : AIToSpawn) {
		// safety check for the AIClassBP to ensure it is valid before adding to the load list
		if (UClass* loadedClass = aiSpawn.AIClassBP.LoadSynchronous()) {
			AddAgentToGroup(aiSpawn);
		}
		else {
			UE_LOG(ACFAILog, Warning, TEXT("Failed to load class for spawn info!"));
		}
	}
}

void UACFGroupAIComponent::DespawnGroup_Implementation(const bool bUpdateAIToSpawn /*= true*/, FGameplayTag actionToTriggerOnDyingAgent, float lifespawn /*= 1.f*/)
{
	if (bAlreadySpawned) {
		if (bUpdateAIToSpawn) {
			AIToSpawn.Empty();
			for (const FAIAgentsInfo& agent : AICharactersInfo) {
				if (agent.AICharacter && agent.AICharacter->IsAlive()) {
					AIToSpawn.Add(BuildSpawnInfoFromAgent(agent));
				}
			}
		}
		for (FAIAgentsInfo& agent : AICharactersInfo) {
			if (agent.AICharacter && agent.AICharacter->IsAlive()) {
				agent.AICharacter->DestroyCharacter(lifespawn);
				agent.AICharacter->TriggerAction(actionToTriggerOnDyingAgent, EActionPriority::EHigh);
			}
		}
		AICharactersInfo.Empty();
		bAlreadySpawned = false;
		OnAgentsDespawned.Broadcast();
	}
}

void UACFGroupAIComponent::InitAgents()
{
	Super::InitAgents();
}

void UACFGroupAIComponent::ServerAddCharacterToGroup_Implementation(AACFCharacter* character)
{
	AddExistingCharacterToGroup(character);
}

void UACFGroupAIComponent::ServerRemoveCharacterFromGroup_Implementation(AACFCharacter* character)
{
	RemoveAgentFromGroup(character);
}

void UACFGroupAIComponent::ServerAddAIToSpawn_Implementation(const FAISpawnInfo& spawnInfo)
{
	AddAIToSpawn(spawnInfo);
}




void UACFGroupAIComponent::InitAgent(FAIAgentsInfo& agent, int32 childIndex)
{
	if (!agent.bHasSpawnInfo) {
		if (AIToSpawn.IsValidIndex(childIndex)) {
			StoreSpawnInfoForAgent(agent, AIToSpawn[childIndex]);
		}
		else if (agent.AICharacter) {
			StoreSpawnInfoForAgent(agent, BuildSpawnInfoFromCharacter(agent.AICharacter));
		}
	}

	Super::InitAgent(agent, childIndex);

	if (agent.GetController()) {
		if (!groupLead) {
			SetReferences();
		}
		agent.GetController()->SetLeadActorBK(groupLead);
		agent.GetController()->SetDefaultState(DefaultAiState);
		agent.GetController()->SetCurrentAIState(DefaultAiState);
		const FAISpawnInfo spawnInfo = BuildSpawnInfoFromAgent(agent);
		if (spawnInfo.PatrolPath) {
			agent.GetController()->SetPatrolPath(spawnInfo.PatrolPath, true);
		}
		//	agent.AICharacter->GetEquipmentComponent()->InitializeStartingItems();
		agent.GetController()->SetGroupOwner(this, childIndex, bOverrideAgentPerception, bOverrideAgentTeam);
		UACFCharacterInitializerComponent* initComp = agent.AICharacter->FindComponentByClass<UACFCharacterInitializerComponent>();

		if (initComp && spawnInfo.AIConfig) {

			initComp->InitFromDataAsset(spawnInfo.AIConfig.LoadSynchronous(), spawnInfo.AILevel);
		}
	}
}

bool UACFGroupAIComponent::AddAIToSpawnFromClass(const TSubclassOf<AACFCharacter>& charClass)
{
	if (!GetOwner()->HasAuthority()) {
		UE_LOG(ACFAILog, Warning, TEXT("Trying to manipulate AI from client!- UACFGroupAIComponentn [%s]"), *this->GetName());

		return false;
	}

	if (GetMaxSimultaneousAgents() <= GetTotalAIToSpawnCount()) {
		UE_LOG(ACFAILog, Warning, TEXT("Your Group Already Reach The Maximum! - UACFGroupAIComponent::AddAIToSpawn [%s]"), *this->GetName());
		return false;
	}

	AIToSpawn.Add(FAISpawnInfo(charClass));

	OnAgentsChanged.Broadcast();
	return true;
}

bool UACFGroupAIComponent::AddAIToSpawn(const FAISpawnInfo& spawnInfo)
{
	if (!GetOwner()->HasAuthority()) {
		UE_LOG(ACFAILog, Warning, TEXT("Trying to manipulate AI from client!- UACFGroupAIComponentn [%s]"), *this->GetName());
		return false;
	}

	if (GetMaxSimultaneousAgents() < GetTotalAIToSpawnCount()) {
		UE_LOG(ACFAILog, Warning, TEXT("Your Group Already Reach The Maximum! - UACFGroupAIComponent::AddAIToSpawn [%s]"), *this->GetName());
		return false;
	}

	AIToSpawn.Add(spawnInfo);

	OnAgentsChanged.Broadcast();
	return true;
}

bool UACFGroupAIComponent::RemoveAIToSpawn(const TSubclassOf<AACFCharacter>& charClass)
{
	if (AIToSpawn.Contains(charClass)) {

		AIToSpawn.Remove(charClass);

		OnAgentsChanged.Broadcast();
		return true;
	}
	return false;
}

bool UACFGroupAIComponent::RemoveAIToSpawnUnit(const FBaseUnit& unit)
{
	const int32 unitIndex = AIToSpawn.IndexOfByKey(unit);

	if (AIToSpawn.IsValidIndex(unitIndex)) {
		AIToSpawn.RemoveAt(unitIndex);
		OnAgentsChanged.Broadcast();
		return true;
	}
	return false;
}

void UACFGroupAIComponent::ReplaceAIToSpawn(const TArray<FAISpawnInfo>& newAIs)
{
	AIToSpawn.Empty();
	AIToSpawn = newAIs;
}


void UACFGroupAIComponent::Internal_SendCommandToAgents(FGameplayTag command)
{
	for (FAIAgentsInfo& achar : AICharactersInfo) {
		if (achar.GetController()) {
			achar.GetController()->TriggerCommand(command);
		}
		else {

			ensure(false);
		}
	}
}

void UACFGroupAIComponent::SetEnemyGroup(UACFGroupAIComponent* inEnemyGroup)
{
	if (inEnemyGroup && UACFFunctionLibrary::AreEnemyTeams(GetWorld(), GetCombatTeam(), inEnemyGroup->GetCombatTeam())) {
		enemyGroup = inEnemyGroup;
	}
}

FVector UACFGroupAIComponent::GetGroupCentroid() const
{
	TArray<AActor*> actors;
	for (const auto& agent : AICharactersInfo) {
		if (agent.AICharacter) {
			actors.Add(agent.AICharacter);
		}
	}
	return UGameplayStatics::GetActorArrayAverageLocation(actors);
}

class AACFCharacter* UACFGroupAIComponent::RequestNewTarget(const AACFAIController* requestSender)
{
	// First Try to help lead
	const AACFCharacter* lead = Cast<AACFCharacter>(requestSender->GetLeadActorBK());
	if (lead) {
		const AACFCharacter* newTarget = Cast<AACFCharacter>(lead->GetTarget());
		if (newTarget && newTarget->IsMyEnemy(requestSender->GetBaseAICharacter())) {
			return Cast<AACFCharacter>(lead->GetTarget());
		}
	}

	// Then Try to help other in  the group
	if (AICharactersInfo.IsValidIndex(0) && IsValid(AICharactersInfo[0].AICharacter) && IsValid(AICharactersInfo[0].GetController())) {
		for (FAIAgentsInfo achar : AICharactersInfo) {
			if (achar.GetController() && achar.GetController() != requestSender) {
				AACFCharacter* newTarget = Cast<AACFCharacter>(achar.GetController()->GetTargetActorBK());
				if (newTarget && newTarget->IsAlive() && achar.GetController()->IsInBattle()) {
					return newTarget;
				}
			}
		}
	}

	// Then Try to help other in  the group
	if (enemyGroup) {
		return enemyGroup->GetAgentNearestTo(requestSender->GetPawn()->GetActorLocation());
	}

	return nullptr;
}


uint8 UACFGroupAIComponent::AddAgentToGroup(const FAISpawnInfo& spawnInfo)
{
	UWorld* const world = GetWorld();

	ensure(GetOwner()->HasAuthority());

	if (!world)
		return -1;

	if (!groupLead) {
		SetReferences();
		if (!groupLead) {
			return -1;
		}
	}

	if (AICharactersInfo.Num() >= GetMaxSimultaneousAgents()) {
		return -1;
	}

	FAIAgentsInfo newCharacterInfo;
	StoreSpawnInfoForAgent(newCharacterInfo, spawnInfo);

	const int32 localGroupIndex = AICharactersInfo.Num();
	const FVector myLocation = groupLead->GetActorLocation();
	FVector additivePos = FVector::ZeroVector;
	FActorSpawnParameters spawnParam;
	spawnParam.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
	FTransform spawnTransform;
	if (spawnInfo.SpawnTransform.GetLocation() != FVector::ZeroVector) {
		additivePos = spawnInfo.SpawnTransform.GetLocation();
	}
	else {
		additivePos.X = UKismetMathLibrary::RandomFloatInRange(-DefaultSpawnOffset.X, DefaultSpawnOffset.X);
		additivePos.Y = UKismetMathLibrary::RandomFloatInRange(-DefaultSpawnOffset.Y, DefaultSpawnOffset.Y);
	}
	const FVector spawnLocation = myLocation + additivePos;
	FVector outPoint;

	if (UNavigationSystemV1::K2_ProjectPointToNavigation(this, spawnLocation, outPoint, nullptr, nullptr, FVector(500.f))) {
		spawnTransform.SetLocation(outPoint);

	}
	else {
		spawnTransform.SetLocation(spawnLocation);
	}
	spawnTransform.SetRotation(spawnInfo.SpawnTransform.GetRotation());
	newCharacterInfo.AICharacter = world->SpawnActorDeferred<AACFCharacter>(
		spawnInfo.AIClassBP.LoadSynchronous(), spawnTransform, nullptr, nullptr,
		ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn);

	if (newCharacterInfo.AICharacter) {

		// Disable auto-init if spawner provides its own config
		if (spawnInfo.AIConfig.IsValid()) {
			newCharacterInfo.AICharacter->SetAutoInit(false);
		}
		UGameplayStatics::FinishSpawningActor(newCharacterInfo.AICharacter, spawnTransform);

		// End Spawn
		if (!newCharacterInfo.AICharacter->GetController()) {
			newCharacterInfo.AICharacter->SpawnDefaultController();
		}
		InitAgent(newCharacterInfo, localGroupIndex);

		AICharactersInfo.Add(newCharacterInfo);
		return localGroupIndex;
	}
	return -1;
}

FAISpawnInfo UACFGroupAIComponent::BuildSpawnInfoFromAgent(const FAIAgentsInfo& agent) const
{
	FAISpawnInfo spawnInfo;
	spawnInfo.AIClassBP = agent.AIClassBP;
	spawnInfo.AIConfig = agent.AIConfig;
	spawnInfo.AILevel = agent.AILevel;
	spawnInfo.SpawnTransform = agent.SpawnTransform;
	spawnInfo.PatrolPath = agent.PatrolPath;

	if (agent.AICharacter && spawnInfo.AIClassBP.IsNull()) {
		spawnInfo.AIClassBP = agent.AICharacter->GetClass();
	}

	return spawnInfo;
}

void UACFGroupAIComponent::StoreSpawnInfoForAgent(FAIAgentsInfo& agent, const FAISpawnInfo& spawnInfo) const
{
	agent.AIClassBP = spawnInfo.AIClassBP;
	agent.AIConfig = spawnInfo.AIConfig;
	agent.AILevel = spawnInfo.AILevel;
	agent.SpawnTransform = spawnInfo.SpawnTransform;
	agent.PatrolPath = spawnInfo.PatrolPath;
	agent.bHasSpawnInfo = true;
}

FAISpawnInfo UACFGroupAIComponent::BuildSpawnInfoFromCharacter(AACFCharacter* character) const
{
	FAISpawnInfo spawnInfo;
	if (!character) {
		return spawnInfo;
	}

	spawnInfo.AIClassBP = character->GetClass();
	spawnInfo.SpawnTransform = groupLead
		? character->GetActorTransform().GetRelativeTransform(groupLead->GetActorTransform())
		: character->GetActorTransform();

	UACFCharacterInitializerComponent* initComp = character->FindComponentByClass<UACFCharacterInitializerComponent>();
	if (initComp) {
		if (UACFCharacterDataAsset* characterData = initComp->GetCharacterDataAsset()) {
			spawnInfo.AIConfig = characterData;
		}
		else if (UACFCharacterDataAsset* autoInitData = initComp->GetAutoInitDataAsset()) {
			spawnInfo.AIConfig = autoInitData;
		}
		spawnInfo.AILevel = initComp->GetAutoInitLevel();
	}

	return spawnInfo;
}

int32 UACFGroupAIComponent::GetTotalAIToSpawnCount() const
{

	return AIToSpawn.Num();
}

bool UACFGroupAIComponent::AddExistingCharacterToGroup(AACFCharacter* character)
{
	if (!GetOwner()->HasAuthority()) {
		UE_LOG(ACFAILog, Warning, TEXT("Trying to manipulate AI from client!- UACFGroupAIComponentn [%s]"), *this->GetName());

		return false;
	}

	const UWorld* world = GetWorld();

	if (!world) {
		return false;
	}

	if (!groupLead) {
		SetReferences();
	}

	if (AICharactersInfo.Contains(character)) {
		InitAgents();
		return true;
	}

	FAIAgentsInfo newCharacterInfo;
	newCharacterInfo.AICharacter = character;
	StoreSpawnInfoForAgent(newCharacterInfo, BuildSpawnInfoFromCharacter(character));

	if (newCharacterInfo.AICharacter) {
		if (!newCharacterInfo.AICharacter->GetController()) {
			newCharacterInfo.AICharacter->SpawnDefaultController();
		}

		uint8 childIndex = AICharactersInfo.Num();
		newCharacterInfo.GetController() = Cast<AACFAIController>(newCharacterInfo.AICharacter->GetController());
		if (newCharacterInfo.GetController()) {
			InitAgent(newCharacterInfo, childIndex);
		}
		else {
			UE_LOG(ACFAILog, Error, TEXT("%s NO AI to Spawn - AAIFGROUPPAWN::SpawnAGroup"), *this->GetName());
		}

		AICharactersInfo.Add(newCharacterInfo);
		return true;
	}
	return false;
}

void UACFGroupAIComponent::ReInitAgent(AACFCharacter* character)
{
	if (AICharactersInfo.Contains(character)) {
		FAIAgentsInfo* newCharacterInfo = AICharactersInfo.FindByKey(character);
		const int32 index = AICharactersInfo.IndexOfByKey(character);
		InitAgent(*newCharacterInfo, index);
	}
}

AACFCharacter* UACFGroupAIComponent::GetAgentNearestTo(const FVector& location) const
{
	AACFCharacter* bestAgent = nullptr;
	float minDistance = 999999.f;
	for (FAIAgentsInfo achar : AICharactersInfo) {
		if (achar.AICharacter && achar.AICharacter->IsAlive()) {
			const float distance = FVector::Distance(location, achar.AICharacter->GetActorLocation());
			if (distance <= minDistance) {
				minDistance = distance;
				bestAgent = achar.AICharacter;
			}
		}
	}
	return bestAgent;
}



bool UACFGroupAIComponent::RemoveAgentFromGroup(AACFCharacter* character)
{
	if (!character) {
		return false;
	}

	AACFAIController* contr = Cast<AACFAIController>(character->GetController());
	if (!contr) {
		return false;
	}

	const FAIAgentsInfo agentInfo(character);


	if (AICharactersInfo.Contains(agentInfo)) {
		AICharactersInfo.RemoveSingle(agentInfo);
		contr->ResetToDefaultState();
		contr->SetLeadActorBK(nullptr);
		contr->SetGroupOwner(nullptr, 0, false, false);
		return true;
	}

	return false;
}

void UACFGroupAIComponent::SetInBattle(bool inBattle, AActor* newTarget)
{
	bInBattle = inBattle;
	if (bInBattle && GetOwner()->HasAuthority()) {
		const APawn* aiTarget = Cast<APawn>(newTarget);
		if (aiTarget) {

			// Check if target is part of a group
			AController* targetCont = aiTarget->GetController();
			if (targetCont) {
				const bool bImplements = targetCont->GetClass()->ImplementsInterface(UACFGroupAgentInterface::StaticClass());
				if (bImplements && IACFGroupAgentInterface::Execute_IsPartOfGroup(targetCont)) {
					UACFGroupAIComponent* groupComp = IACFGroupAgentInterface::Execute_GetOwningGroup(targetCont);
					SetEnemyGroup(groupComp);
				}
				else {
					enemyGroup = nullptr;
				}
			}
		}

		int32 index = 0;
		for (const FAIAgentsInfo& achar : AICharactersInfo) {
			if (!achar.GetController() || achar.GetController()->IsInBattle() || !achar.AICharacter->IsAlive()) {
				continue;
			}

			// Trying to assign to every agent in the group that is not in battle an enemy in the enemy group
			AActor* nextTarget = newTarget;
			FAIAgentsInfo adversary;
			if (enemyGroup && enemyGroup->GetGroupSize() > 0) {
				if (achar.GetController() && !achar.GetController()->HasTarget()) {
					if (enemyGroup->GetGroupSize() > index) {
						enemyGroup->GetAgentByIndex(index, adversary);
						index++;
					}
					else {
						index = 0;
						enemyGroup->GetAgentByIndex(index, adversary);
						index++;
					}
					nextTarget = adversary.AICharacter;
				}
			}
			UACFThreatManagerComponent* threatComp = achar.GetController()->GetThreatManager();
			if (nextTarget) {
				const float newThreat = threatComp->GetDefaultThreatForActor(nextTarget);
				if (newThreat > 0.f) {
					// if the enemy we found is valid, we add aggro for that enemy
					threatComp->AddThreat(nextTarget, newThreat + 10.f);
				}
				else {
					// otherwise we go in the new target
					threatComp->AddThreat(newTarget, threatComp->GetDefaultThreatForActor(newTarget));
				}
			}
		}
	}
}

void UACFGroupAIComponent::OnChildDeath(const AACFCharacter* character)
{
	Super::OnChildDeath(character);
	const int32 index = AICharactersInfo.IndexOfByKey(character);
	if (AICharactersInfo.IsValidIndex(index)) {
		AICharactersInfo.RemoveAt(index);
	}
	if (AICharactersInfo.Num() == 0) {
		OnAllAgentDeath.Broadcast();
	}
}


#if WITH_EDITOR
#include "Components/CapsuleComponent.h"

void UACFGroupAIComponent::PostEditChangeProperty(FPropertyChangedEvent& PropertyChangedEvent)
{
	Super::PostEditChangeProperty(PropertyChangedEvent);

	const FName PropertyName = PropertyChangedEvent.GetPropertyName();
	if (PropertyName == GET_MEMBER_NAME_CHECKED(UACFGroupAIComponent, AIToSpawn))
	{
		RebuildSpawnPreviewCapsules();
	}

	MarkRenderStateDirty();
}

void UACFGroupAIComponent::PostEditComponentMove(bool bFinished)
{
	Super::PostEditComponentMove(bFinished);
	MarkRenderStateDirty();
}

void UACFGroupAIComponent::RebuildSpawnPreviewCapsules()
{
	// Clear existing capsules
	for (UCapsuleComponent* Capsule : SpawnPreviewCapsules)
	{
		if (Capsule)
		{
			Capsule->TransformUpdated.RemoveAll(this);
			Capsule->DestroyComponent();
		}
	}
	SpawnPreviewCapsules.Empty();

	AActor* Owner = GetOwner();
	if (!Owner)
	{
		return;
	}

	// Create a capsule for each spawn info
	for (int32 i = 0; i < AIToSpawn.Num(); ++i)
	{
		UCapsuleComponent* Capsule = NewObject<UCapsuleComponent>(Owner, NAME_None, RF_Transactional);
		Capsule->SetupAttachment(this);
		Capsule->SetRelativeTransform(AIToSpawn[i].SpawnTransform);
		Capsule->SetCapsuleSize(34.f, 88.f);
		Capsule->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Capsule->SetHiddenInGame(true);
		Capsule->bVisibleInReflectionCaptures = false;
		Capsule->SetCastShadow(false);

		// Visual settings for editor
		Capsule->ShapeColor = FColor::Green;
		Capsule->bDrawOnlyIfSelected = false;
		Capsule->SetVisibility(true);

		Capsule->RegisterComponent();

		// Bind transform update
		int32 SpawnIndex = i;
		Capsule->TransformUpdated.AddWeakLambda(this, [this, SpawnIndex](USceneComponent* UpdatedComponent, auto, ETeleportType)
			{
				if (AIToSpawn.IsValidIndex(SpawnIndex))
				{
					AIToSpawn[SpawnIndex].SpawnTransform = UpdatedComponent->GetRelativeTransform();
					if (AActor* Owner = GetOwner())
					{
						Owner->Modify();
					}
				}
			});

		SpawnPreviewCapsules.Add(Capsule);
	}
}



void UACFGroupAIComponent::SyncSpawnInfoFromCapsules()
{
	for (int32 i = 0; i < SpawnPreviewCapsules.Num() && i < AIToSpawn.Num(); ++i)
	{
		if (SpawnPreviewCapsules[i])
		{
			AIToSpawn[i].SpawnTransform = SpawnPreviewCapsules[i]->GetRelativeTransform();
		}
	}
}
#endif

void UACFGroupAIComponent::OnRegister()
{
	Super::OnRegister();

#if WITH_EDITOR
	if (GetWorld() && GetWorld()->WorldType == EWorldType::Editor)
	{
		RebuildSpawnPreviewCapsules();
	}
#endif
}

void UACFGroupAIComponent::OnUnregister()
{
#if WITH_EDITOR
	for (UCapsuleComponent* Capsule : SpawnPreviewCapsules)
	{
		if (Capsule)
		{
			Capsule->TransformUpdated.RemoveAll(this);
			Capsule->DestroyComponent();
		}
	}
	SpawnPreviewCapsules.Empty();
#endif

	Super::OnUnregister();
}