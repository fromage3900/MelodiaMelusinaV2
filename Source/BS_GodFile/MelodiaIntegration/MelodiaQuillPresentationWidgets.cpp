#include "MelodiaQuillPresentationWidgets.h"

#include "MelodiaUIFeedbackSubsystem.h"
#include "Components/Button.h"
#include "Components/Image.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Engine/World.h"
#include "Input/Reply.h"
#include "InputCoreTypes.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundBase.h"
#include "Text/SmartTypewriter.h"
#include "UObject/UObjectGlobals.h"

namespace MelodiaFeedbackIds
{
	const FName DialogueAdvance(TEXT("UI.Feedback.DialogueAdvance"));
	const FName ChoiceSelected(TEXT("UI.Feedback.ChoiceSelected"));
}

UMelodiaQuillDialogWidget::UMelodiaQuillDialogWidget()
{
	VoiceBlipSound = TSoftObjectPtr<USoundBase>(
		FSoftObjectPath(TEXT("/Game/Melodia/Audio/SFX/UI/SW_MelodiaDialogueBlip.SW_MelodiaDialogueBlip")));
	VoiceBlipFallbackSound = TSoftObjectPtr<USoundBase>(
		FSoftObjectPath(TEXT("/Game/Audio/tick_001.tick_001")));
}

void UMelodiaQuillDialogWidget::NativeConstruct()
{
	Super::NativeConstruct();

	SetIsFocusable(true);
	if (AdvanceButton)
	{
		AdvanceButton->OnClicked.RemoveDynamic(this, &ThisClass::HandleAdvanceClicked);
		AdvanceButton->OnClicked.AddDynamic(this, &ThisClass::HandleAdvanceClicked);
	}
	if (!IsInViewport())
	{
		AddToViewportAtLayer();
	}
}

void UMelodiaQuillDialogWidget::NativeDestruct()
{
	StopTypewriter();
	ReleaseDialogueContext();
	Super::NativeDestruct();
}

void UMelodiaQuillDialogWidget::Play_Implementation(
	const FString& Speaker,
	const FText& Text,
	const TArray<FString>& Tags)
{
	EnsureDialogueContext();
	bAdvanceConsumed = false;
	VoiceBlipsPlayed = 0;
	ActiveTags = Tags;

	if (SpeakerText)
	{
		SpeakerText->SetText(FText::FromString(Speaker));
		SpeakerText->SetVisibility(Speaker.IsEmpty() ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible);
	}

	if (BodyText)
	{
		BodyText->SetText(FText::GetEmpty());
	}

	StartTypewriter(Speaker, Text);

	if (!IsInViewport() && !GetParent())
	{
		AddToViewportAtLayer();
	}

	if (AdvanceButton)
	{
		AdvanceButton->SetKeyboardFocus();
	}
	else
	{
		SetKeyboardFocus();
	}
}

FReply UMelodiaQuillDialogWidget::NativeOnKeyDown(
	const FGeometry& InGeometry,
	const FKeyEvent& InKeyEvent)
{
	const FKey Key = InKeyEvent.GetKey();
	if (Key == EKeys::Enter || Key == EKeys::SpaceBar || Key == EKeys::E || Key == EKeys::Gamepad_FaceButton_Bottom)
	{
		TryAdvance();
		return FReply::Handled();
	}

	return Super::NativeOnKeyDown(InGeometry, InKeyEvent);
}

FReply UMelodiaQuillDialogWidget::NativeOnMouseButtonDown(
	const FGeometry& InGeometry,
	const FPointerEvent& InMouseEvent)
{
	if (InMouseEvent.GetEffectingButton() == EKeys::LeftMouseButton)
	{
		TryAdvance();
		return FReply::Handled();
	}

	return Super::NativeOnMouseButtonDown(InGeometry, InMouseEvent);
}

void UMelodiaQuillDialogWidget::HandleAdvanceClicked()
{
	TryAdvance();
}

void UMelodiaQuillDialogWidget::TryAdvance()
{
	if (Typewriter && !bTypewriterLineComplete)
	{
		if (bClickCompletesLine)
		{
			FinishTypewriter();
			return;
		}

		StopTypewriter();
		if (BodyText)
		{
			BodyText->SetText(TypewriterFullText);
		}
	}

	if (bAdvanceConsumed)
	{
		return;
	}

	bAdvanceConsumed = true;
	// The per-glyph voice cue replaces the long UI bubble on dialogue advance;
	// keep the bubble as the fallback when blips are disabled or unavailable.
	if (!bVoiceBlipsEnabled || !LoadedVoiceBlip)
	{
		UMelodiaUIFeedbackSubsystem::RequestFeedback(
			this,
			MelodiaFeedbackIds::DialogueAdvance,
			FVector2D(-1.0, -1.0));
	}
	OnAdvance.Broadcast();
}

void UMelodiaQuillDialogWidget::StartTypewriter(const FString& Speaker, const FText& Text)
{
	TypewriterFullText = Text;
	ActiveSpeaker = Speaker;
	LastVoiceBlipTime = 0.0;
	bLoggedVoiceBlip = false;
	bTypewriterLineComplete = true;

	EnsureVoiceBlipLoaded();

	UWorld* World = GetWorld();
	if (!bTypewriterEnabled || !World)
	{
		if (BodyText)
		{
			BodyText->SetText(Text);
		}
		return;
	}

	if (!Typewriter)
	{
		Typewriter = World->SpawnActor<ASmartTypewriter>();
	}

	if (!Typewriter)
	{
		if (BodyText)
		{
			BodyText->SetText(Text);
		}
		return;
	}

	FTextPrintedDelegate Printed;
	Printed.BindDynamic(this, &ThisClass::HandleTypewriterPrinted);
	FTextCompletedDelegate Completed;
	Completed.BindDynamic(this, &ThisClass::HandleTypewriterCompleted);

	bTypewriterLineComplete = false;
	Typewriter->Initialize(
		Text,
		Printed,
		Completed,
		FMath::Max(0.01f, TypewriterInterval),
		nullptr,
		false,
		false);
}

void UMelodiaQuillDialogWidget::StopTypewriter()
{
	if (IsValid(Typewriter.Get()))
	{
		Typewriter->ClearTimer();
		Typewriter->Destroy();
	}
	Typewriter = nullptr;
	bTypewriterLineComplete = true;
}

void UMelodiaQuillDialogWidget::FinishTypewriter()
{
	if (BodyText)
	{
		BodyText->SetText(TypewriterFullText);
	}
	if (Typewriter)
	{
		Typewriter->Finish();
	}
	bTypewriterLineComplete = true;
}

void UMelodiaQuillDialogWidget::HandleTypewriterPrinted(
	const FText& PrintedText,
	const FString& Character,
	const int32& Index)
{
	if (BodyText)
	{
		BodyText->SetText(PrintedText);
	}

	PlayVoiceBlip(ActiveSpeaker, Character, Index);

	if (Typewriter && !Character.IsEmpty())
	{
		const TCHAR Glyph = Character[0];
		if (Glyph == '.' || Glyph == '!' || Glyph == '?')
		{
			Typewriter->Pause(0.12f);
		}
		else if (Glyph == ',' || Glyph == ';' || Glyph == ':')
		{
			Typewriter->Pause(0.06f);
		}
		else if (Glyph == '\n')
		{
			Typewriter->Pause(0.15f);
		}
	}
}

void UMelodiaQuillDialogWidget::HandleTypewriterCompleted()
{
	bTypewriterLineComplete = true;
	if (BodyText)
	{
		BodyText->SetText(TypewriterFullText);
	}
}

void UMelodiaQuillDialogWidget::EnsureVoiceBlipLoaded()
{
	if (LoadedVoiceBlip)
	{
		return;
	}

	if (!VoiceBlipSound.IsNull())
	{
		LoadedVoiceBlip = VoiceBlipSound.LoadSynchronous();
	}

	if (!LoadedVoiceBlip && !VoiceBlipFallbackSound.IsNull())
	{
		LoadedVoiceBlip = VoiceBlipFallbackSound.LoadSynchronous();
	}

	if (!LoadedVoiceBlip)
	{
		LoadedVoiceBlip = LoadObject<USoundBase>(nullptr, TEXT("/Game/Audio/tick_001.tick_001"));
	}

	if (LoadedVoiceBlip)
	{
		UE_LOG(LogTemp, Log, TEXT("MELODIA_DIALOGUE_VOICE loaded=%s"), *GetNameSafe(LoadedVoiceBlip));
	}
}

void UMelodiaQuillDialogWidget::PlayVoiceBlip(
	const FString& Speaker,
	const FString& Character,
	const int32 Index)
{
	if (!bVoiceBlipsEnabled || !LoadedVoiceBlip || Character.IsEmpty())
	{
		return;
	}

	const TCHAR Glyph = Character[0];
	if (FChar::IsWhitespace(Glyph) || Glyph == '<' || Glyph == '>' || Glyph == '/' || Glyph == '\\')
	{
		return;
	}

	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}

	const double Now = World->GetTimeSeconds();
	if (LastVoiceBlipTime > 0.0 && Now - LastVoiceBlipTime < VoiceBlipMinInterval)
	{
		return;
	}
	LastVoiceBlipTime = Now;

	float Pitch = ResolveSpeakerPitch(Speaker);
	const uint32 Hash = HashCombine(GetTypeHash(Character), static_cast<uint32>(Index));
	const float Jitter = (static_cast<float>(Hash % 1001) / 500.0f) - 1.0f;
	Pitch *= FMath::Pow(2.0f, Jitter * VoiceBlipPitchJitterSemitones / 12.0f);

	if (Glyph == '.' || Glyph == ',' || Glyph == ';' || Glyph == ':')
	{
		Pitch *= 0.94f;
	}
	else if (Glyph == '!' || Glyph == '?')
	{
		Pitch *= 1.06f;
	}

	Pitch = FMath::Clamp(Pitch, 0.35f, 2.5f);
	UGameplayStatics::PlaySound2D(this, LoadedVoiceBlip, VoiceBlipVolume, Pitch);
	++VoiceBlipsPlayed;

	if (!bLoggedVoiceBlip)
	{
		bLoggedVoiceBlip = true;
		UE_LOG(LogTemp, Log,
			TEXT("MELODIA_DIALOGUE_VOICE blip asset=%s speaker=%s pitch=%.3f index=%d"),
			*GetNameSafe(LoadedVoiceBlip),
			*Speaker,
			Pitch,
			Index);
	}
}

float UMelodiaQuillDialogWidget::ResolveSpeakerPitch(const FString& Speaker) const
{
	if (Speaker.IsEmpty() || Speaker == TEXT("."))
	{
		return 0.92f;
	}
	if (Speaker.Equals(TEXT("Melusina"), ESearchCase::IgnoreCase))
	{
		return 1.0f;
	}
	if (Speaker.Contains(TEXT("Sir Melodious"), ESearchCase::IgnoreCase))
	{
		return 0.82f;
	}
	if (Speaker.Contains(TEXT("Sheep"), ESearchCase::IgnoreCase))
	{
		return 1.25f;
	}

	const uint32 Hash = GetTypeHash(Speaker);
	const int32 Semitones = static_cast<int32>(Hash % 9) - 4;
	return FMath::Pow(2.0f, static_cast<float>(Semitones) / 12.0f);
}

void UMelodiaQuillDialogWidget::EnsureDialogueContext()
{
	if (DialogueContextHandle.IsValid())
	{
		return;
	}

	if (UMelodiaInputContextSubsystem* Input = UMelodiaInputContextSubsystem::Get(this))
	{
		DialogueContextHandle = Input->PushContext(EMelodiaInputContext::Dialogue, this);
	}
}

void UMelodiaQuillDialogWidget::ReleaseDialogueContext()
{
	if (!DialogueContextHandle.IsValid())
	{
		return;
	}

	if (UMelodiaInputContextSubsystem* Input = UMelodiaInputContextSubsystem::Get(this))
	{
		Input->PopContext(DialogueContextHandle);
	}
	DialogueContextHandle = {};
}

void UMelodiaQuillChoiceEntryWidget::InitializeOption(
	UMelodiaQuillSelectionWidget* InOwner,
	const int32 InOptionIndex,
	const FEvaluatedOption& InOption)
{
	OwnerSelection = InOwner;
	OptionIndex = InOptionIndex;
	bOptionEnabled = InOption.bValid;
	OptionTags = InOption.Tags;
	OptionText = InOption.Text;

	ApplyOptionState();
}

void UMelodiaQuillChoiceEntryWidget::NativeConstruct()
{
	Super::NativeConstruct();

	if (ChoiceButton)
	{
		ChoiceButton->OnClicked.RemoveDynamic(this, &ThisClass::HandleClicked);
		ChoiceButton->OnClicked.AddDynamic(this, &ThisClass::HandleClicked);
	}
	if (ChoiceText)
	{
		ChoiceText->SetText(OptionText);
	}
	ApplyOptionState();
}

void UMelodiaQuillChoiceEntryWidget::FocusOption()
{
	if (ChoiceButton && ChoiceButton->GetIsEnabled())
	{
		ChoiceButton->SetKeyboardFocus();
	}
	else
	{
		SetKeyboardFocus();
	}
}

void UMelodiaQuillChoiceEntryWidget::HandleClicked()
{
	if (bOptionEnabled && OwnerSelection)
	{
		OwnerSelection->SelectOption(OptionIndex);
	}
}

void UMelodiaQuillChoiceEntryWidget::ApplyOptionState()
{
	if (ChoiceButton)
	{
		ChoiceButton->SetIsEnabled(bOptionEnabled);
	}
	if (ChoiceText)
	{
		ChoiceText->SetText(OptionText);
	}
}

void UMelodiaQuillSelectionWidget::NativeConstruct()
{
	Super::NativeConstruct();
	SetIsFocusable(true);
}

void UMelodiaQuillSelectionWidget::Play_Implementation(const TArray<FEvaluatedOption>& Options)
{
	EnsureDialogueContext();
	bSelectionConsumed = false;
	FocusedOptionIndex = INDEX_NONE;
	ActiveOptions = Options;
	CreatedEntries.Reset();

	if (!OptionsBox)
	{
		UE_LOG(LogTemp, Error, TEXT("Melodia Quill selection cannot present choices: OptionsBox is not bound."));
	}
	else
	{
		OptionsBox->ClearChildren();
		if (!ChoiceEntryClass)
		{
			UE_LOG(LogTemp, Error, TEXT("Melodia Quill selection cannot present choices: ChoiceEntryClass is not assigned."));
		}
		else
		{
			for (int32 Index = 0; Index < ActiveOptions.Num(); ++Index)
			{
				UMelodiaQuillChoiceEntryWidget* Entry = CreateWidget<UMelodiaQuillChoiceEntryWidget>(this, ChoiceEntryClass);
				if (Entry)
				{
					Entry->InitializeOption(this, Index, ActiveOptions[Index]);
					OptionsBox->AddChildToVerticalBox(Entry);
					CreatedEntries.Add(Index, Entry);
				}
				else
				{
					UE_LOG(LogTemp, Error, TEXT("Melodia Quill failed to create choice entry %d."), Index);
				}
			}
		}
	}

	if (!IsInViewport() && !GetParent())
	{
		AddToViewportAtLayer();
	}

	for (int32 Index = 0; Index < ActiveOptions.Num(); ++Index)
	{
		if (FocusOptionAt(Index))
		{
			break;
		}
	}
}

FReply UMelodiaQuillSelectionWidget::NativeOnKeyDown(
	const FGeometry& InGeometry,
	const FKeyEvent& InKeyEvent)
{
	const FKey Key = InKeyEvent.GetKey();
	if (Key == EKeys::Up || Key == EKeys::W || Key == EKeys::Gamepad_DPad_Up || Key == EKeys::Gamepad_LeftStick_Up)
	{
		return MoveChoiceFocus(-1) ? FReply::Handled() : FReply::Unhandled();
	}
	if (Key == EKeys::Down || Key == EKeys::S || Key == EKeys::Gamepad_DPad_Down || Key == EKeys::Gamepad_LeftStick_Down)
	{
		return MoveChoiceFocus(1) ? FReply::Handled() : FReply::Unhandled();
	}
	if (Key == EKeys::Enter || Key == EKeys::SpaceBar || Key == EKeys::E || Key == EKeys::Gamepad_FaceButton_Bottom)
	{
		if (ActiveOptions.IsValidIndex(FocusedOptionIndex) && ActiveOptions[FocusedOptionIndex].bValid)
		{
			SelectOption(FocusedOptionIndex);
			return FReply::Handled();
		}
	}

	return Super::NativeOnKeyDown(InGeometry, InKeyEvent);
}

bool UMelodiaQuillSelectionWidget::FocusOptionAt(const int32 OptionIndex)
{
	if (!ActiveOptions.IsValidIndex(OptionIndex) || !ActiveOptions[OptionIndex].bValid)
	{
		return false;
	}

	if (const TObjectPtr<UMelodiaQuillChoiceEntryWidget>* Entry = CreatedEntries.Find(OptionIndex))
	{
		if (IsValid(Entry->Get()))
		{
			FocusedOptionIndex = OptionIndex;
			Entry->Get()->FocusOption();
			return true;
		}
	}
	return false;
}

bool UMelodiaQuillSelectionWidget::MoveChoiceFocus(const int32 Direction)
{
	if (Direction == 0 || ActiveOptions.IsEmpty())
	{
		return false;
	}

	int32 Candidate = FocusedOptionIndex;
	if (!ActiveOptions.IsValidIndex(Candidate))
	{
		Candidate = Direction > 0 ? -1 : 0;
	}

	for (int32 Attempt = 0; Attempt < ActiveOptions.Num(); ++Attempt)
	{
		Candidate = (Candidate + Direction + ActiveOptions.Num()) % ActiveOptions.Num();
		if (FocusOptionAt(Candidate))
		{
			return true;
		}
	}
	return false;
}

void UMelodiaQuillSelectionWidget::NativeDestruct()
{
	ReleaseDialogueContext();
	Super::NativeDestruct();
}

void UMelodiaQuillSelectionWidget::EnsureDialogueContext()
{
	if (DialogueContextHandle.IsValid())
	{
		return;
	}

	if (UMelodiaInputContextSubsystem* Input = UMelodiaInputContextSubsystem::Get(this))
	{
		DialogueContextHandle = Input->PushContext(EMelodiaInputContext::Dialogue, this);
	}
}

void UMelodiaQuillSelectionWidget::ReleaseDialogueContext()
{
	if (!DialogueContextHandle.IsValid())
	{
		return;
	}

	if (UMelodiaInputContextSubsystem* Input = UMelodiaInputContextSubsystem::Get(this))
	{
		Input->PopContext(DialogueContextHandle);
	}
	DialogueContextHandle = {};
}

void UMelodiaQuillSelectionWidget::SelectOption(const int32 OptionIndex)
{
	if (bSelectionConsumed || !ActiveOptions.IsValidIndex(OptionIndex) || !ActiveOptions[OptionIndex].bValid)
	{
		return;
	}

	const TArray<FStatement> OriginalSelections = GetSelections();
	if (!OriginalSelections.IsValidIndex(OptionIndex))
	{
		return;
	}

	bSelectionConsumed = true;
	UMelodiaUIFeedbackSubsystem::RequestFeedback(
		this,
		MelodiaFeedbackIds::ChoiceSelected,
		FVector2D(-1.0, -1.0));
	RemoveFromParent();
	OnSelected.Broadcast(OriginalSelections[OptionIndex]);
}

void UMelodiaQuillBackgroundWidget::Play_Implementation(
	const UTexture* NewImage,
	const FString& Transition,
	const float Duration)
{
	UTexture* PreviousImage = PresentedImage;
	PresentedImage = const_cast<UTexture*>(NewImage);
	ActiveTransition = Transition;
	ActiveTransitionDuration = FMath::Max(0.0f, Duration);

	if (BackgroundImage)
	{
		BackgroundImage->SetBrushResourceObject(PresentedImage);
	}

	if (!IsInViewport() && !GetParent())
	{
		AddToViewportAtLayer();
	}

	OnImageChanged.Broadcast(PresentedImage, PreviousImage);
}
