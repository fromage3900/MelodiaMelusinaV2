#include "MelodiaQuillPresentationWidgets.h"

#include "MelodiaUIFeedbackSubsystem.h"
#include "Components/Button.h"
#include "Components/Image.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Input/Reply.h"
#include "InputCoreTypes.h"

namespace MelodiaFeedbackIds
{
	const FName DialogueAdvance(TEXT("UI.Feedback.DialogueAdvance"));
	const FName ChoiceSelected(TEXT("UI.Feedback.ChoiceSelected"));
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
	ActiveTags = Tags;

	if (SpeakerText)
	{
		SpeakerText->SetText(FText::FromString(Speaker));
		SpeakerText->SetVisibility(Speaker.IsEmpty() ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible);
	}

	if (BodyText)
	{
		BodyText->SetText(Text);
	}

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
	if (Key == EKeys::Enter || Key == EKeys::SpaceBar)
	{
		TryAdvance();
		return FReply::Handled();
	}

	return Super::NativeOnKeyDown(InGeometry, InKeyEvent);
}

void UMelodiaQuillDialogWidget::HandleAdvanceClicked()
{
	TryAdvance();
}

void UMelodiaQuillDialogWidget::TryAdvance()
{
	if (bAdvanceConsumed)
	{
		return;
	}

	bAdvanceConsumed = true;
	UMelodiaUIFeedbackSubsystem::RequestFeedback(
		this,
		MelodiaFeedbackIds::DialogueAdvance,
		FVector2D(-1.0, -1.0));
	OnAdvance.Broadcast();
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
	if (Key == EKeys::Up || Key == EKeys::W || Key == EKeys::Gamepad_DPad_Up)
	{
		return MoveChoiceFocus(-1) ? FReply::Handled() : FReply::Unhandled();
	}
	if (Key == EKeys::Down || Key == EKeys::S || Key == EKeys::Gamepad_DPad_Down)
	{
		return MoveChoiceFocus(1) ? FReply::Handled() : FReply::Unhandled();
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
