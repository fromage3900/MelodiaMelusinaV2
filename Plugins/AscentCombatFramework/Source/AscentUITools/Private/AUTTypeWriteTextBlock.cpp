// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.


#include "AUTTypeWriteTextBlock.h"
#include <TimerManager.h>
#include <Engine/World.h>

UAUTTypeWriteTextBlock::UAUTTypeWriteTextBlock()
{
	bIsTyping = false;
}

void UAUTTypeWriteTextBlock::SetTextWithTypeWriterEffect(const FText& NewText, float charDelay /*= 0.05f*/)
{
	if (!GetWorld()) {
		return;
	}

	FullText = NewText; // Keep FText for localization
	FullTextString = NewText.ToString(); // Extract FString for character-by-character processing
	CurrentText = "";
	CurrentIndex = 0;
	TypingSpeed = charDelay;
	bIsTyping = true;

	SetText(FText::FromString(CurrentText));
	UpdateStyle();
	// Start the typewriter timer
	GetWorld()->GetTimerManager().SetTimer(TypewriterTimer, this, &UAUTTypeWriteTextBlock::UpdateTypewriter, TypingSpeed, true);
}

void UAUTTypeWriteTextBlock::SkipTypewriterEffect()
{
	if (GetWorld()) {
		GetWorld()->GetTimerManager().ClearTimer(TypewriterTimer);
	}

	SetText(FullText); // Use original FText to ensure localization
	bIsTyping = false;
	OnTypewriterComplete.Broadcast();
}

void UAUTTypeWriteTextBlock::UpdateTypewriter()
{
	if (CurrentIndex < FullTextString.Len()) {
		CurrentText.AppendChar(FullTextString[CurrentIndex]);
		++CurrentIndex;

		SetText(FText::FromString(CurrentText));
	}

	if (CurrentIndex >= FullTextString.Len()) {
		bIsTyping = false;
		GetWorld()->GetTimerManager().ClearTimer(TypewriterTimer);
		SetText(FullText); // Ensure final text uses FText for localization
		OnTypewriterComplete.Broadcast();
	}
}
