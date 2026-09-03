// Mobile HUD ΓÇö portrait 4-lane rhythm highway with touch input
// iPhone 14/15 logical 390x844 (portrait primary). Landscape is optional later.
// SSOT: Docs/MELODIA_IOS_MOBILE_GAME_UI.md ┬╖ WBP_Battle_Mobile

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "MelodiaCoreRulesLibrary.h"
#include "MelodiaMobileHUD.generated.h"

class UButton;
class UCanvasPanel;
class UTextBlock;
class UProgressBar;
class UMelodiaBattleInputComponent;

UCLASS()
class MELODIACORE_API UMelodiaMobileHUD : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

	UFUNCTION(BlueprintCallable, Category = "Melodia|Mobile")
	void InitializeMobileHUD();

	UFUNCTION(BlueprintCallable, Category = "Melodia|Mobile")
	void SetLaneHighlight(int32 LaneIndex, bool bHighlight);

	UFUNCTION(BlueprintCallable, Category = "Melodia|Mobile")
	void ShowGradePopup(EMelodiaRhythmGrade Grade, float Damage);

	UFUNCTION(BlueprintCallable, Category = "Melodia|Mobile")
	void UpdateCombo(int32 ComboCount);

	UFUNCTION(BlueprintCallable, Category = "Melodia|Mobile")
	void UpdateResources(float HPPercent, float SPPercent, float UltPercent);

	/** Forward a lane tap (0ΓÇô3) to MelodiaBattleInputComponent::HandleLaneTap. */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Mobile")
	void ForwardLaneTap(int32 LaneIndex);

protected:
	UPROPERTY(meta = (BindWidgetOptional))
	TObjectPtr<UCanvasPanel> HighwayCanvas;

	UPROPERTY(meta = (BindWidgetOptional))
	TObjectPtr<UTextBlock> ComboText;

	UPROPERTY(meta = (BindWidgetOptional))
	TObjectPtr<UProgressBar> HPBar;

	UPROPERTY(meta = (BindWidgetOptional))
	TObjectPtr<UProgressBar> SPBar;

	UPROPERTY(meta = (BindWidgetOptional))
	TObjectPtr<UProgressBar> UltBar;

	UPROPERTY(meta = (BindWidgetOptional))
	TObjectPtr<UTextBlock> EnemyNameText;

	UPROPERTY(meta = (BindWidgetOptional))
	TObjectPtr<UProgressBar> EnemyHPBar;

	UPROPERTY(meta = (BindWidgetOptional))
	TObjectPtr<UProgressBar> EnemyToughnessBar;

	/** 4 portrait lane touch zones (AΓÇôD / D F J K). Assign in WBP_Battle_Mobile. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Mobile")
	TArray<TObjectPtr<UButton>> LaneButtons;

	UPROPERTY(meta = (BindWidgetOptional))
	TObjectPtr<UCanvasPanel> GradePopupCanvas;

	UPROPERTY(meta = (BindWidgetOptional))
	TObjectPtr<UTextBlock> GradeText;

	/** Portrait highway width in design px (390 frame ΓåÆ ~4├ù44pt lanes + gaps). */
	UPROPERTY(EditAnywhere, Category = "Melodia|Mobile")
	float PortraitHighwayWidth = 358.0f;

	/** Thumb-zone vertical anchor (0ΓÇô1 from top). Default ~0.58 ΓåÆ bottom ~42%. */
	UPROPERTY(EditAnywhere, Category = "Melodia|Mobile")
	float ThumbZoneTopRatio = 0.58f;

private:
	void SetupTouchZones();
	FVector2D CalculateLanePosition(int32 LaneIndex) const;
	UMelodiaBattleInputComponent* FindBattleInput() const;

	UFUNCTION()
	void OnLane0Clicked();
	UFUNCTION()
	void OnLane1Clicked();
	UFUNCTION()
	void OnLane2Clicked();
	UFUNCTION()
	void OnLane3Clicked();

	UFUNCTION()
	void OnLane0Pressed();
	UFUNCTION()
	void OnLane1Pressed();
	UFUNCTION()
	void OnLane2Pressed();
	UFUNCTION()
	void OnLane3Pressed();

	UFUNCTION()
	void OnLane0Released();
	UFUNCTION()
	void OnLane1Released();
	UFUNCTION()
	void OnLane2Released();
	UFUNCTION()
	void OnLane3Released();
};
