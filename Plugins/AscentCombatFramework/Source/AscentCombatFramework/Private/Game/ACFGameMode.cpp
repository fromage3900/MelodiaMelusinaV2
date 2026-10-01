// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#include "Game/ACFGameMode.h"
#include "ACMCollisionsMasterComponent.h"
#include "Components/ACFRagdollMasterComponent.h"
#include "Game/ACFPlayerController.h"
#include "GameFramework/PlayerController.h"
#include "Engine/World.h"
#include <Kismet/GameplayStatics.h>


AACFGameMode::AACFGameMode()
{
	CollisionManager = CreateDefaultSubobject<UACMCollisionsMasterComponent>(TEXT("Collision Master Comp"));
	RagdollManager = CreateDefaultSubobject<UACFRagdollMasterComponent>(TEXT("Ragdoll Master Comp"));
	bUseSeamlessTravel = bEnableACFSeamlessTravel;
}

void AACFGameMode::InitGame(const FString& MapName, const FString& Options, FString& ErrorMessage)
{
	Super::InitGame(MapName, Options, ErrorMessage);
	bUseSeamlessTravel = bEnableACFSeamlessTravel;
}

void AACFGameMode::GetSeamlessTravelActorList(bool bToTransition, TArray<AActor*>& ActorList)
{
	Super::GetSeamlessTravelActorList(bToTransition, ActorList);

	if (!bEnableACFSeamlessTravel) {
		return;
	}

	for (auto It = GetWorld()->GetPlayerControllerIterator(); It; ++It) {
		APlayerController* PlayerController = It->Get();
		if (!PlayerController) {
			continue;
		}

		ActorList.AddUnique(PlayerController);

		if (APawn* PlayerPawn = PlayerController->GetPawn()) {
			ActorList.AddUnique(PlayerPawn);
		}
	}
}

// void AACFGameMode::SpawnPlayersCompanions()
// {
// 	TArray<class AACFPlayerController*> pcs = GetAllPlayerControllers();
// 
// 	for (AACFPlayerController* pc : pcs) {
// 		pc->GetCompanionsComponent()->SpawnGroup();
// 	}
// }

TArray<class AACFPlayerController*> AACFGameMode::GetAllPlayerControllers() 
{
	TArray<class AACFPlayerController*> playerContrs;
	const int32 numPlayer = GetNumPlayers();

	for (int32 i = 0; i < numPlayer; i++) {
		 APlayerController* pc = UGameplayStatics::GetPlayerController(this,i );
		if (pc) {
			 AACFPlayerController* acfpc = Cast< AACFPlayerController>(pc);
			if (acfpc) {
				playerContrs.Add(acfpc);
			}
		}
	}

	return playerContrs;
}
