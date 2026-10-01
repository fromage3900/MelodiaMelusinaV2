// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 


#include "ACFSummonAction.h"
#include <NavigationSystem.h>
#include <Engine/World.h>
#include "Game/ACFTypes.h"
#include "Game/ACFFunctionLibrary.h"
#include <Kismet/KismetMathLibrary.h>
#include "Actions/ACFActionAbility.h"
#include <GameFramework/Actor.h>
#include "Actors/ACFCharacter.h"
#include "Components/ACFDamageHandlerComponent.h"
#include "Components/ACFCompanionGroupAIComponent.h"
#include <TimerManager.h>
#include <Engine/EngineTypes.h>
#include "GameFramework/Pawn.h"
#include <GameFramework/Controller.h>


void UACFSummonAction::OnNotablePointReached_Implementation()
{
	Super::OnNotablePointReached_Implementation();
	//resetting to avoid having 
	if (currentCompIndex >= 250) {
		currentCompIndex = 0;
	}   

	FVector outLoc;
	if (GetCharacterOwner() &&
		UNavigationSystemV1::K2_GetRandomLocationInNavigableRadius(this, GetCharacterOwner()->GetActorLocation(), outLoc, SpawnRadius))
	{
		UWorld* world = GetWorld();
		if (!world)
			return;

		if (world && CompanionToSummonClass)
		{
			FActorSpawnParameters SpawnParams;
			SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
	
			FRotator rot = UKismetMathLibrary::FindLookAtRotation(outLoc, GetCharacterOwner()->GetActorLocation());
			rot.Pitch = 0.f;
            rot.Roll = 0.f;
			AACFCharacter* comp = world->SpawnActor<AACFCharacter>(CompanionToSummonClass, outLoc, rot, SpawnParams);
			
			if (comp) {
				comp->SpawnDefaultController();
				Companions.Add(comp);
				
				const AController* controller = CharacterOwner->GetController();
				if (controller) {
					UACFCompanionGroupAIComponent* groupComp = controller->FindComponentByClass<UACFCompanionGroupAIComponent>();
					if (groupComp) {
						groupComp->AddExistingCharacterToGroup(comp);
					}
					else {
						UE_LOG(LogTemp, Error, TEXT("No CompanionsComp on Controller!!"));
					}
				}
	
				UACFDamageHandlerComponent* damageHandler = comp->GetDamageHandlerComponent();
				damageHandler->OnOwnerDeath.AddDynamic(this, &UACFSummonAction::OnCompanionDeath);
				if (bAutoKillAfterSeconds) {
					FTimerDelegate TimerDel;
					FTimerHandle TimerHandle;
					TimerDel.BindUFunction(this, FName("KillCompanion"), comp);
					world->GetTimerManager().SetTimer(TimerHandle, TimerDel, AutoKillTime, false);
				}
			}
		}
	}
}

bool UACFSummonAction::CanExecuteAction_Implementation(class ACharacter* owner) const
{
	return Companions.Num() < MaxCompanionNumb;
}

void UACFSummonAction::KillCompanion(class AACFCharacter* comp)
{
	if (Companions.Contains(comp)) {
		 comp->KillCharacter();
		 Companions.Remove(comp);
	}
}

void UACFSummonAction::OnCompanionDeath()
{
	TArray<AACFCharacter*> pendingDelete;
	for (const auto& comp : Companions) {
		if (comp && comp->IsAlive()) {
			continue;
		}
		pendingDelete.Add(comp);
	}

	for (const auto& tobeRem : pendingDelete) {
		Companions.Remove(tobeRem);
	}
}

