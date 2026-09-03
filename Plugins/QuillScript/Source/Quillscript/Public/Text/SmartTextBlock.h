// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/RichTextBlock.h"
#include "SmartTextBlock.generated.h"

/**
 * A text block that replaces variables within a text, for their values.
 */
UCLASS(BlueprintType)
class QUILLSCRIPT_API USmartTextBlock : public URichTextBlock
{
	GENERATED_BODY()

public:
	virtual void SynchronizeProperties() override;
	virtual void SetText(const FText& InText) override;


	/// Getters and Setters

	UFUNCTION(BlueprintGetter)
	FORCEINLINE TMap<FName, FString> GetVariablesMap() const { return this->VariablesMap; }

	UFUNCTION(BlueprintSetter)
	void SetVariablesMap(const TMap<FName, FString>& Value);

	UFUNCTION(BlueprintGetter)
	FORCEINLINE TArray<UStringTable*> GetStringTables() const { return this->StringTables; }

	UFUNCTION(BlueprintSetter)
	void SetStringTables(const TArray<UStringTable*>& Value);


private:
	/** String Map to use for variable replacement. */
	UPROPERTY(EditAnywhere, BlueprintGetter = GetVariablesMap, BlueprintSetter = SetVariablesMap, Category = "Settings")
	TMap<FName, FString> VariablesMap;

	/** String Tables to use for variable replacement. */
	UPROPERTY(EditAnywhere, BlueprintGetter = GetStringTables, BlueprintSetter = SetStringTables, Category = "Settings")
	TArray<UStringTable*> StringTables;
};