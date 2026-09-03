// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "SoundState.generated.h"

/**
 * History's sound structure.
 */
USTRUCT(BlueprintType)
struct QUILLSCRIPT_API FSoundState
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Data")
	FName Channel;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Data")
	FString AssetPath;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Data")
	float Volume{ 1 };
};