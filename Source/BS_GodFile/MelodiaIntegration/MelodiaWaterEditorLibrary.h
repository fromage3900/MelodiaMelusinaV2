// Copyright Melodia Water Systems. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "MelodiaWaterEditorLibrary.generated.h"

/**
 * Editor-only authoring helpers for project-owned water contracts.
 *
 * This is intentionally a narrow asset-authoring surface. It does not mutate
 * engine plugin content and is safe to invoke from the text-injection pipeline.
 */
UCLASS()
class BS_GODFILE_API UMelodiaWaterEditorLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
#if WITH_EDITOR
	UFUNCTION(BlueprintCallable, Category = "Melodia|Water|Editor")
	static bool CreateOrUpdateWaterContactDataChannel(const FString& AssetPath, FString& OutReport);
#endif
};
