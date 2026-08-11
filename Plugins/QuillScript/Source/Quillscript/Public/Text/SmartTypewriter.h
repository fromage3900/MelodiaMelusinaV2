// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Info.h"
#include "SmartTypewriter.generated.h"

class UAudioComponent;

DECLARE_DYNAMIC_DELEGATE(FTextCompletedDelegate);
DECLARE_DYNAMIC_DELEGATE_ThreeParams(FTextPrintedDelegate, const FText&, Text, const FString&, Character, const int32&, Index);

/** Handles the typing effect for text. */
UCLASS(BlueprintType)
class QUILLSCRIPT_API ASmartTypewriter final : public AInfo
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Typewriter")
	void Initialize(const FText& InText,
		const FTextPrintedDelegate& InPrintedDelegate,
		const FTextCompletedDelegate& InCompletedDelegate,
		float InInterval, USoundBase* InSound,
		bool bInAudioOverlap,
		bool bInSanitize);

	UFUNCTION(BlueprintCallable, Category = "Quillscript|Typewriter|Timer Controls")
	void TypeText();

	UFUNCTION(BlueprintCallable, Category = "Quillscript|Typewriter|Timer Controls")
	void Finish();

	UFUNCTION(BlueprintCallable, Category = "Quillscript|Typewriter|Timer Controls")
	void ChangeSpeed(float NewInterval = 0.02f);

	UFUNCTION(BlueprintCallable, Category = "Quillscript|Typewriter|Timer Controls", meta = (AdvancedDisplay = "Duration"))
	void Pause(float Duration = -1.0f);

	UFUNCTION(BlueprintCallable, Category = "Quillscript|Typewriter|Timer Controls")
	void Unpause();

	UFUNCTION(BlueprintCallable, Category = "Quillscript|Typewriter|Timer Controls")
	void ClearTimer();

	UFUNCTION(BlueprintCallable, Category = "Quillscript|Typewriter|Timer Controls")
	void AddSubstringDelay(const FString& Substring, float Delay = 0.5f);

	UFUNCTION(BlueprintCallable, Category = "Quillscript|Typewriter|Timer Controls")
	void AddSubstringsDelays(const TMap<FString, float>& Substrings);

	UFUNCTION(BlueprintCallable, Category = "Quillscript|Typewriter|Timer Controls")
	void RemoveSubstringDelay(const FString& Substring);

	UFUNCTION(BlueprintCallable, Category = "Quillscript|Typewriter|Timer Controls", meta = (AdvancedDisplay = "OverlapSound"))
	void ChangeSound(USoundBase* NewSound = nullptr, bool OverlapSound = false);

	UFUNCTION(BlueprintCallable, Category = "Quillscript|Typewriter|Timer Controls")
	bool IsPaused() const;

	UFUNCTION(BlueprintCallable, Category = "Quillscript|Typewriter|Timer Controls")
	bool IsPrintCompleted() const;

	UFUNCTION(BlueprintGetter)
	FORCEINLINE int32 GetIndex() const { return Index; }

	UFUNCTION(BlueprintGetter)
	FORCEINLINE FTimerHandle& GetTimerHandle() { return TimerHandle; }

	UPROPERTY(BlueprintReadOnly, Category = "Quillscript|Typewriter|Events")
	FTextPrintedDelegate OnPrinted;

	UPROPERTY(BlueprintReadOnly, Category = "Quillscript|Typewriter|Events")
	FTextCompletedDelegate OnCompleted;

protected:
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

private:
	FText Text;
	FTextPrintedDelegate PrintedDelegate;
	FTextCompletedDelegate CompletedDelegate;
	float Interval{0.02f};
	bool bOverlapSound{true};
	bool bSanitize{true};
	bool bCompletionDispatched{false};

	UPROPERTY()
	TObjectPtr<USoundBase> Sound{nullptr};

	UPROPERTY(BlueprintGetter = GetIndex, Category = "Quillscript|Typewriter|Properties")
	int32 Index{1};

	TMap<FString, float> SubstringDelays;

	UPROPERTY(BlueprintGetter = GetTimerHandle, Category = "Quillscript|Typewriter|References")
	FTimerHandle TimerHandle;

	FTimerHandle PauseDurationTimerHandle;
	bool bAddTemporaryClosingTag{false};

	UPROPERTY()
	TObjectPtr<UAudioComponent> AudioComponent{nullptr};

	void GetPartialText();
	FString GetProcessedTextString() const;
	static FText ReplaceDelayTags(const FText& InText);
	static float ParseDelayTag(FString TagNameAndAttributes);
};
