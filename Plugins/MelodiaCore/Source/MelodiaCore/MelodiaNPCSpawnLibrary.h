#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "MelodiaNPCBase.h"
#include "MelodiaNPCSpawnLibrary.generated.h"

USTRUCT(BlueprintType)
struct MELODIACORE_API FMelodiaNPCSpawnRequest
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|NPC")
	FPrimaryAssetId DefinitionId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|NPC")
	FTransform Transform = FTransform::Identity;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|NPC")
	TSubclassOf<AMelodiaNPCBase> ActorClass;
};

UCLASS()
class MELODIACORE_API UMelodiaNPCSpawnLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()
public:
	UFUNCTION(BlueprintCallable, Category="Melodia|NPC", meta=(WorldContext="WorldContextObject"))
	static bool SpawnNPCBatch(UObject* WorldContextObject, const TArray<FMelodiaNPCSpawnRequest>& Requests, TArray<AMelodiaNPCBase*>& OutSpawnedActors);
};