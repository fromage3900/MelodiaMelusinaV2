#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "MelodiaCalibrationWidget.generated.h"

class UFont;
class USoundBase;

/**
 * Latency calibration: plays its own metronome (the music clock only runs in battle), times the
 * player's taps against each click, and stores the median lag as the player's calibration offset
 * through UMelodiaGameUserSettings. Self-painted, so it has no layout to drift.
 */
UCLASS()
class BS_GODFILE_API UMelodiaCalibrationWidget final : public UUserWidget
{
	GENERATED_BODY()

public:
	UMelodiaCalibrationWidget(const FObjectInitializer& ObjectInitializer);

	/** Creates the screen for the first local player, adds it to the viewport and focuses it. */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Rhythm|Calibration", meta = (WorldContext = "WorldContextObject"))
	static UMelodiaCalibrationWidget* Open(UObject* WorldContextObject);

	/** Median measured lag of the last run (ms, positive = late); valid once the run finished. */
	UFUNCTION(BlueprintPure, Category = "Melodia|Rhythm|Calibration")
	float GetMeasuredOffsetMs() const { return MeasuredOffsetMs; }

	/** Records a tap now. Keyboard/gamepad call this; exposed for scripted tests. */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Rhythm|Calibration")
	void RegisterTap();

	UFUNCTION(BlueprintCallable, Category = "Melodia|Rhythm|Calibration")
	void ApplyAndClose();

protected:
	virtual void NativeConstruct() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;
	virtual FReply NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent) override;
	virtual int32 NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
		FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;

	UPROPERTY(EditAnywhere, Category = "Melodia|Rhythm|Calibration")
	float BPM = 100.0f;

	UPROPERTY(EditAnywhere, Category = "Melodia|Rhythm|Calibration", meta = (ClampMin = "4"))
	int32 ClickCount = 12;

	/** Clicks before measurement starts, so the player can lock onto the pulse. */
	UPROPERTY(EditAnywhere, Category = "Melodia|Rhythm|Calibration", meta = (ClampMin = "0"))
	int32 WarmupClicks = 4;

	UPROPERTY(EditAnywhere, Category = "Melodia|Rhythm|Calibration")
	TObjectPtr<USoundBase> ClickSound;

	UPROPERTY(EditAnywhere, Category = "Melodia|Rhythm|Calibration")
	TObjectPtr<USoundBase> AccentSound;

	UPROPERTY(EditAnywhere, Category = "Melodia|Rhythm|Calibration")
	TObjectPtr<UFont> Font;

private:
	enum class EState : uint8 { Running, Result };

	void Restart();
	void Finish();

	EState State = EState::Running;
	double StartTime = 0.0;
	double LastClickTime = -1.0;
	int32 ClicksPlayed = 0;
	TArray<double> ClickTimes;
	TArray<float> TapLagsMs;
	float MeasuredOffsetMs = 0.0f;
};
