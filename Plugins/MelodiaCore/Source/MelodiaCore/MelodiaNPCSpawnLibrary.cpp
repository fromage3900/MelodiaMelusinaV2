#include "MelodiaNPCSpawnLibrary.h"
#include "Engine/AssetManager.h"
#include "Engine/World.h"

bool UMelodiaNPCSpawnLibrary::SpawnNPCBatch(UObject* WorldContextObject, const TArray<FMelodiaNPCSpawnRequest>& Requests, TArray<AMelodiaNPCBase*>& OutSpawnedActors)
{
	OutSpawnedActors.Reset();
	UWorld* World = WorldContextObject ? WorldContextObject->GetWorld() : nullptr;
	if (!World) { return false; }
	bool bAllSucceeded = true;
	for (const FMelodiaNPCSpawnRequest& Request : Requests)
	{
		const FSoftObjectPath Path = UAssetManager::Get().GetPrimaryAssetPath(Request.DefinitionId);
		UMelodiaNPCDefinitionAsset* Definition = Cast<UMelodiaNPCDefinitionAsset>(Path.TryLoad());
		if (!Definition)
		{
			UE_LOG(LogTemp, Warning, TEXT("NPC batch skipped unresolved definition '%s'."), *Request.DefinitionId.ToString());
			bAllSucceeded = false;
			continue;
		}
		UClass* SpawnClass = Request.ActorClass ? Request.ActorClass.Get() : AMelodiaNPCBase::StaticClass();
		AMelodiaNPCBase* NPC = World->SpawnActor<AMelodiaNPCBase>(SpawnClass, Request.Transform, FActorSpawnParameters());
		if (!NPC || !NPC->SetNPCDefinition(Definition))
		{
			if (NPC) { NPC->Destroy(); }
			bAllSucceeded = false;
			continue;
		}
		OutSpawnedActors.Add(NPC);
	}
	return bAllSucceeded;
}