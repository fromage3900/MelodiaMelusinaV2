#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "MelodiaBattleResultsWidget.generated.h"

class UTextBlock;

/** Presentation-only results screen populated from the authoritative battle session. */
UCLASS(Blueprintable)
class MELODIACORE_API UMelodiaBattleResultsWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category="Melodia|Battle Results")
	void RefreshFromBattleSession();

protected:
	virtual void NativeConstruct() override;

	UPROPERTY(meta=(BindWidgetOptional)) TObjectPtr<UTextBlock> TXT_Rank;
	UPROPERTY(meta=(BindWidgetOptional)) TObjectPtr<UTextBlock> TXT_Score;
	UPROPERTY(meta=(BindWidgetOptional)) TObjectPtr<UTextBlock> TXT_Perfect;
	UPROPERTY(meta=(BindWidgetOptional)) TObjectPtr<UTextBlock> TXT_Hit;
	UPROPERTY(meta=(BindWidgetOptional)) TObjectPtr<UTextBlock> TXT_Miss;
	UPROPERTY(meta=(BindWidgetOptional)) TObjectPtr<UTextBlock> TXT_Damage;
	UPROPERTY(meta=(BindWidgetOptional)) TObjectPtr<UTextBlock> TXT_MaxCombo;
};
