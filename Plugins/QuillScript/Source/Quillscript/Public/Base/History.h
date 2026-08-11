// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "SaveState.h"

#include "CoreMinimal.h"
#include "History.generated.h"

class UQuillscriptAsset;

/**
 * 'Script' history data.
 */
USTRUCT(BlueprintType)
struct QUILLSCRIPT_API FHistory
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Data")
	FName ScriptId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Data")
	int32 TimesPlayed{ 0 };

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Data")
	bool bRunning{ true };

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Data")
	TArray<FSaveState> SaveState;


	FSaveState GetLatestSaveState()
	{
		if (!this->SaveState.IsEmpty())
			return this->SaveState.Last();

		return FSaveState();
	}
};