// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Widgets/AUTTextBlock.h"

#include "AUTTypeWriteTextBlock.generated.h"


/** Delegate triggered when the typewriter effect is completed */
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnTypewriterComplete);

/**
 * A custom TextBlock that adds a typewriter effect to display text character by character.
 */
UCLASS()
class ASCENTUITOOLS_API UAUTTypeWriteTextBlock : public UAUTTextBlock {
	GENERATED_BODY()

public:
	UAUTTypeWriteTextBlock();

	/** Starts the typewriter effect with localized text */
	UFUNCTION(BlueprintCallable, Category = "Typewriter")
	void SetTextWithTypeWriterEffect(const FText& NewText, float charDelay = 0.03f);

	/** Skips the typewriter effect and immediately shows the full text */
	UFUNCTION(BlueprintCallable, Category = "Typewriter")
	void SkipTypewriterEffect();

	/** Delegate event triggered when the typewriter effect completes */
	UPROPERTY(BlueprintAssignable, Category = "Typewriter")
	FOnTypewriterComplete OnTypewriterComplete;

	UFUNCTION(BlueprintPure, Category = "Typewriter")
	bool GetIsTyping() const { return bIsTyping; }

private:
	FText FullText;
	FString FullTextString;
	FString CurrentText;
	float TypingSpeed;
	int32 CurrentIndex;
	float Timer;
	bool bIsTyping;

	FTimerHandle TypewriterTimer;
	void UpdateTypewriter();
};
