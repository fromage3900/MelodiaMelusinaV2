// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include "UObject/NoExportTypes.h"
#include "ALSSaveTypes.h"
#include "ALSSavableInterface.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/World.h"
#include <Async/AsyncWork.h>
#include "ALSSaveTask.generated.h"

/**
 * 
 */
 class UALSSaveGame;


DECLARE_DYNAMIC_DELEGATE_OneParam(FOnSaveFinished, const bool, Success);


class FSaveWorldTask : public FNonAbandonableTask {

public:

	FString slotDesc;
	FString saveName;
	bool bSaveLocalPlayer;
	UWorld* world;
        explicit FSaveWorldTask(const FString& slotName, UWorld* inWorld, const bool saveLocalPlayer, FString inSlotDescription = "")
        {
		saveName = slotName;
		slotDesc = inSlotDescription;
		world = inWorld;
		bSaveLocalPlayer = saveLocalPlayer;
		if (world) {
			 UGameplayStatics::GetAllActorsWithInterface(world, UALSSavableInterface::StaticClass(), SavableActors);
		}
		SuccessfullySavedActors.Empty();
	}

	void DoWork();

private:
	FALSActorData SerializeActor(AActor* actor);

	void FinishSave(const bool bSuccess);

	void StoreLocalPlayer();

	void StoreGameState();

	void StorePlayerState();

	TArray<AActor*> SavableActors;
	TArray<AActor*> SuccessfullySavedActors;

protected:
	TObjectPtr<UALSSaveGame> newSave;

public:

	FORCEINLINE TStatId GetStatId() const {
		RETURN_QUICK_DECLARE_CYCLE_STAT(FSaveWorldTask, STATGROUP_ThreadPoolAsyncTasks);
	}

};


UCLASS()
class ASCENTSAVESYSTEM_API UALSSaveTask : public UObject
{
	GENERATED_BODY()
	
};
