// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "EvaluatedOption.generated.h"

/**
 * Simplified and pre-evaluated version of an Options statement.
 * This is how Selection Box widgets receive options on its 'Play' event.
 */
USTRUCT(BlueprintType)
struct QUILLSCRIPT_API FEvaluatedOption
{
	GENERATED_BODY()

	/** Option's conditions evaluation result. */
	UPROPERTY(BlueprintReadWrite, Category = "Data")
	bool bValid{ true };

	UPROPERTY(BlueprintReadWrite, Category = "Data")
	FText Text;

	UPROPERTY(BlueprintReadWrite, Category = "Data")
	TArray<FString> Tags;
};