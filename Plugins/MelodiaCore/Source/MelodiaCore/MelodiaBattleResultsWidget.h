#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "MelodiaBattleResultsWidget.generated.h"

class UTextBlock;
class UButton;

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FMelodiaBattleResultsDismissed);

/** Presentation-only results screen populated from the authoritative battle session. */
UCLASS(Blueprintable)
class MELODIACORE_API UMelodiaBattleResultsWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category="Melodia|Battle Results")
	void RefreshFromBattleSession();

	UFUNCTION(BlueprintCallable, Category="Melodia|Battle Results")
	void Dismiss();

	UPROPERTY(BlueprintAssignable, Category="Melodia|Battle Results")
	FMelodiaBattleResultsDismissed OnResultsDismissed;

protected:
	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;
	virtual FReply NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent) override;
	virtual FReply NativeOnMouseButtonDown(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent) override;

	UPROPERTY(meta=(BindWidgetOptional)) TObjectPtr<UTextBlock> TXT_Rank;
	UPROPERTY(meta=(BindWidgetOptional)) TObjectPtr<UTextBlock> TXT_Score;
	UPROPERTY(meta=(BindWidgetOptional)) TObjectPtr<UTextBlock> TXT_Perfect;
	UPROPERTY(meta=(BindWidgetOptional)) TObjectPtr<UTextBlock> TXT_Hit;
	UPROPERTY(meta=(BindWidgetOptional)) TObjectPtr<UTextBlock> TXT_Miss;
	UPROPERTY(meta=(BindWidgetOptional)) TObjectPtr<UTextBlock> TXT_Damage;
	UPROPERTY(meta=(BindWidgetOptional)) TObjectPtr<UTextBlock> TXT_MaxCombo;
	UPROPERTY(meta=(BindWidgetOptional)) TObjectPtr<UButton> Btn_Continue;
	UPROPERTY(meta=(BindWidgetOptional)) TObjectPtr<UButton> Btn_Dismiss;

private:
	UFUNCTION()
	void HandleDismissClicked();

	bool bDismissed = false;
};
