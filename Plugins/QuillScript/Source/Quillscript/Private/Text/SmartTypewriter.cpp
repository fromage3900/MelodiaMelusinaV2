// Copyright Bruno Caxito. All Rights Reserved.

#include "Text/SmartTypewriter.h"

#include "Components/AudioComponent.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundBase.h"
#include "Text/SmartTextBlockDecorator.h"
#include "TimerManager.h"
#include "Utils/Lexer.h"
#include "Utils/Tools.h"

void ASmartTypewriter::Initialize(const FText& InText,
	const FTextPrintedDelegate& InPrintedDelegate,
	const FTextCompletedDelegate& InCompletedDelegate,
	const float InInterval,
	USoundBase* InSound,
	const bool bInAudioOverlap,
	const bool bInSanitize)
{
	if (!GetWorld())
	{
		return;
	}

	ClearTimer();
	Index = 1;
	bAddTemporaryClosingTag = false;
	bCompletionDispatched = false;
	Text = ReplaceDelayTags(InText);
	PrintedDelegate = InPrintedDelegate;
	CompletedDelegate = InCompletedDelegate;
	Interval = InInterval;
	Sound = InSound;
	bOverlapSound = bInAudioOverlap;
	bSanitize = bInSanitize;
	TypeText();
}

void ASmartTypewriter::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	ClearTimer();
	if (IsValid(AudioComponent))
	{
		AudioComponent->Stop();
	}
	PrintedDelegate.Unbind();
	CompletedDelegate.Unbind();
	Super::EndPlay(EndPlayReason);
}

FString ASmartTypewriter::GetProcessedTextString() const
{
	FString Result = Text.ToString();
	if (bSanitize)
	{
		Result.TrimStartAndEndInline();
	}
	return Result;
}

void ASmartTypewriter::TypeText()
{
	UWorld* World = GetWorld();
	if (!World || bCompletionDispatched)
	{
		return;
	}

	const int32 TextLength = GetProcessedTextString().Len();
	if (Index > TextLength)
	{
		GetPartialText();
		return;
	}

	if (Interval <= 0.0f)
	{
		Index = TextLength;
		GetPartialText();
		return;
	}

	World->GetTimerManager().SetTimer(
		TimerHandle,
		this,
		&ASmartTypewriter::GetPartialText,
		Interval,
		true,
		0.0f);
}

void ASmartTypewriter::Finish()
{
	Index = GetProcessedTextString().Len();
	bAddTemporaryClosingTag = false;
	Unpause();
}

void ASmartTypewriter::ChangeSpeed(const float NewInterval)
{
	ClearTimer();
	Interval = NewInterval;
	TypeText();
}

void ASmartTypewriter::Pause(const float Duration)
{
	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}

	FTimerManager& TimerManager = World->GetTimerManager();
	if (!TimerManager.TimerExists(TimerHandle))
	{
		return;
	}

	TimerManager.PauseTimer(TimerHandle);
	TimerManager.ClearTimer(PauseDurationTimerHandle);
	if (Duration > 0.0f)
	{
		TimerManager.SetTimer(
			PauseDurationTimerHandle,
			this,
			&ASmartTypewriter::Unpause,
			Duration,
			false);
	}
}

void ASmartTypewriter::Unpause()
{
	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}

	FTimerManager& TimerManager = World->GetTimerManager();
	TimerManager.ClearTimer(PauseDurationTimerHandle);
	if (TimerManager.TimerExists(TimerHandle) && TimerManager.IsTimerPaused(TimerHandle))
	{
		TimerManager.UnPauseTimer(TimerHandle);
	}
}

void ASmartTypewriter::ClearTimer()
{
	if (UWorld* World = GetWorld())
	{
		FTimerManager& TimerManager = World->GetTimerManager();
		TimerManager.ClearTimer(TimerHandle);
		TimerManager.ClearTimer(PauseDurationTimerHandle);
	}
	TimerHandle.Invalidate();
	PauseDurationTimerHandle.Invalidate();
}

void ASmartTypewriter::AddSubstringDelay(const FString& Substring, const float Delay)
{
	SubstringDelays.Add(Substring, Delay);
}

void ASmartTypewriter::AddSubstringsDelays(const TMap<FString, float>& Substrings)
{
	SubstringDelays.Append(Substrings);
}

void ASmartTypewriter::RemoveSubstringDelay(const FString& Substring)
{
	SubstringDelays.Remove(Substring);
}

void ASmartTypewriter::ChangeSound(USoundBase* NewSound, const bool OverlapSound)
{
	Sound = NewSound;
	bOverlapSound = OverlapSound;
	if (IsValid(AudioComponent))
	{
		AudioComponent->Stop();
		AudioComponent->SetSound(Sound);
	}
}

bool ASmartTypewriter::IsPaused() const
{
	const UWorld* World = GetWorld();
	if (!World)
	{
		return false;
	}
	const FTimerManager& TimerManager = World->GetTimerManager();
	return TimerManager.TimerExists(TimerHandle) && TimerManager.IsTimerPaused(TimerHandle);
}

bool ASmartTypewriter::IsPrintCompleted() const
{
	return Index > GetProcessedTextString().Len();
}

void ASmartTypewriter::GetPartialText()
{
	UWorld* World = GetWorld();
	if (!World || bCompletionDispatched)
	{
		return;
	}

	const FString TextAsString = GetProcessedTextString();
	const int32 TextLength = TextAsString.Len();
	Index = FMath::Max(Index, 1);

	if (Index <= TextLength)
	{
		const FString StartingSubstring = TextAsString.Left(Index);
		const FString EndingSubstring = TextAsString.RightChop(Index);

		if (StartingSubstring.EndsWith(TEXT("<")))
		{
			if (EndingSubstring.StartsWith(TEXT("/>")))
			{
				Index = FMath::Min(Index + 2, TextLength);
				bAddTemporaryClosingTag = false;
			}
			else
			{
				FString TagNameAndAttributes(TEXT("<"));
				for (; Index < TextLength; ++Index)
				{
					const FString CurrentChar = TextAsString.Mid(Index, 1);
					const FString PreviousChar = Index > 0 ? TextAsString.Mid(Index - 1, 1) : FString();
					TagNameAndAttributes += CurrentChar;
					if (CurrentChar == TEXT(">") && PreviousChar != FLexer::EscapeCharacter)
					{
						if (TagNameAndAttributes.StartsWith(TEXT("<") + USmartTextBlockDecorator::DelayTagName))
						{
							Pause(ParseDelayTag(TagNameAndAttributes));
						}
						++Index;
						bAddTemporaryClosingTag = true;
						break;
					}
				}
			}
		}

		Index = FMath::Min(Index, TextLength);
		FString PrintString = TextAsString.Left(Index);
		if (Index < TextLength)
		{
			for (const TPair<FString, float>& SubstringDelay : SubstringDelays)
			{
				if (PrintString.EndsWith(SubstringDelay.Key))
				{
					Pause(SubstringDelay.Value);
					break;
				}
			}
		}

		if (bAddTemporaryClosingTag)
		{
			PrintString += TEXT("</>");
		}

		const int32 PrintedIndex = Index;
		PrintedDelegate.ExecuteIfBound(FText::FromString(PrintString), PrintString.Right(1), PrintedIndex);
		if (!IsValid(this) || IsActorBeingDestroyed())
		{
			return;
		}
		++Index;

		if (IsValid(Sound))
		{
			if (bOverlapSound || !IsValid(AudioComponent))
			{
				AudioComponent = UGameplayStatics::CreateSound2D(this, Sound);
			}
			if (IsValid(AudioComponent))
			{
				AudioComponent->SetSound(Sound);
				AudioComponent->Play();
			}
		}
		return;
	}

	ClearTimer();
	bCompletionDispatched = true;
	CompletedDelegate.ExecuteIfBound();
}

FText ASmartTypewriter::ReplaceDelayTags(const FText& InText)
{
	const FString TokenOpen(TEXT("__TKN_DELAY_OPEN__"));
	const FString TokenClose(TEXT("__TKN_DELAY_CLOSE__"));
	FString TextAsString = InText.ToString();
	TextAsString.ReplaceInline(*(FLexer::EscapeCharacter + USmartTextBlockDecorator::DelayShortTagOpen), *TokenOpen);
	TextAsString.ReplaceInline(*(FLexer::EscapeCharacter + USmartTextBlockDecorator::DelayShortTagClose), *TokenClose);
	TextAsString.ReplaceInline(*USmartTextBlockDecorator::DelayShortTagOpen, *(TEXT("<") + USmartTextBlockDecorator::DelayTagName + TEXT(" value=\"")));
	TextAsString.ReplaceInline(*USmartTextBlockDecorator::DelayShortTagClose, TEXT("\"></>"));
	TextAsString.ReplaceInline(*TokenOpen, *USmartTextBlockDecorator::DelayShortTagOpen);
	TextAsString.ReplaceInline(*TokenClose, *USmartTextBlockDecorator::DelayShortTagClose);
	return TXT(TextAsString);
}

float ASmartTypewriter::ParseDelayTag(FString TagNameAndAttributes)
{
	TagNameAndAttributes.RemoveFromStart(TEXT("<") + USmartTextBlockDecorator::DelayTagName);
	TagNameAndAttributes.RemoveFromEnd(TEXT(">"));
	TagNameAndAttributes.ReplaceInline(TEXT("value="), TEXT(""));
	TagNameAndAttributes.ReplaceInline(TEXT("\""), TEXT(""));
	TagNameAndAttributes.TrimStartAndEndInline();
	return USmartTextBlockDecorator::ConvertDelayToSeconds(*TagNameAndAttributes);
}
