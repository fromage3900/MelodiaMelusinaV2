// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2023. All Rights Reserved.

#pragma once

#include "Components/RichTextBlock.h"
#include "CoreMinimal.h"

#include "AUTRichTextBlock.generated.h"

/**
 *
 */
UCLASS()
class ASCENTUITOOLS_API UAUTRichTextBlock : public URichTextBlock {
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category = AUT)
	void SetStyleIndex(int32 inStyleIndex);

	UFUNCTION(BlueprintCallable, Category = AUT)
	void UpdateStyle();

	UFUNCTION(BlueprintPure, Category = AUT)
	int32 GetStyleIndex() const { return StyleIndex; }

	UFUNCTION(BlueprintCallable, Category = AUT)
	void SetFontSize(int32 inFontSize);

protected:
	UPROPERTY(EditAnywhere, Category = AUT)
	int32 StyleIndex = 0;

	UPROPERTY(EditAnywhere, Category = AUT)
	int32 TextSize = 16;

	UPROPERTY(EditAnywhere, Category = AUT)
	bool bUseStyle = true;

	virtual void SynchronizeProperties() override;
};
