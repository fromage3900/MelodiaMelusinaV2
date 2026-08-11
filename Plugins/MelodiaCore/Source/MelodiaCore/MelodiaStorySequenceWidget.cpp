#include "MelodiaStorySequenceWidget.h"

#include "Components/Button.h"
#include "Components/Image.h"
#include "Components/TextBlock.h"
#include "Engine/Texture2D.h"
#include "Kismet/GameplayStatics.h"
#include "MelodiaStorySequenceData.h"
#include "Sound/SoundBase.h"
#include "TimerManager.h"

void UMelodiaStorySequenceWidget::NativeConstruct()
{
	Super::NativeConstruct();
	if (AdvanceButton)
	{
		AdvanceButton->OnClicked.AddUniqueDynamic(this, &ThisClass::Advance);
	}
	if (SkipButton)
	{
		SkipButton->OnClicked.AddUniqueDynamic(this, &ThisClass::Skip);
	}
}

void UMelodiaStorySequenceWidget::NativeDestruct()
{
	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().ClearTimer(AutoAdvanceTimer);
	}

	Super::NativeDestruct();
}

bool UMelodiaStorySequenceWidget::SetSequence(UMelodiaStorySequenceData* InSequence)
{
	if (!IsValid(InSequence) || InSequence->Slides.IsEmpty())
	{
		return false;
	}

	Sequence = InSequence;
	CurrentSlideIndex = 0;
	ApplyCurrentSlide();
	return true;
}

void UMelodiaStorySequenceWidget::Advance()
{
	if (!Sequence)
	{
		return;
	}

	if (CurrentSlideIndex + 1 >= Sequence->Slides.Num())
	{
		FinishSequence();
		return;
	}

	++CurrentSlideIndex;
	ApplyCurrentSlide();
}

void UMelodiaStorySequenceWidget::Skip()
{
	if (Sequence && Sequence->bAllowSkip)
	{
		FinishSequence();
	}
}

void UMelodiaStorySequenceWidget::ApplyCurrentSlide()
{
	if (!Sequence || !Sequence->Slides.IsValidIndex(CurrentSlideIndex))
	{
		FinishSequence();
		return;
	}

	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().ClearTimer(AutoAdvanceTimer);
	}

	const FMelodiaStorySlide& Slide = Sequence->Slides[CurrentSlideIndex];
	if (SlideArtwork)
	{
		if (UTexture2D* Artwork = Slide.Artwork.LoadSynchronous())
		{
			SlideArtwork->SetBrushFromTexture(Artwork, true);
			SlideArtwork->SetVisibility(ESlateVisibility::Visible);
		}
		else
		{
			SlideArtwork->SetVisibility(ESlateVisibility::Collapsed);
		}
	}
	if (KickerText) { KickerText->SetText(Slide.Kicker); }
	if (TitleText) { TitleText->SetText(Slide.Title); }
	if (BodyText) { BodyText->SetText(Slide.Body); }
	if (SkipButton) { SkipButton->SetVisibility(Sequence->bAllowSkip ? ESlateVisibility::Visible : ESlateVisibility::Collapsed); }

	if (USoundBase* Stinger = Slide.Stinger.LoadSynchronous())
	{
		UGameplayStatics::PlaySound2D(this, Stinger);
	}

	if (Slide.AutoAdvanceAfterSeconds > 0.0f)
	{
		if (UWorld* World = GetWorld())
		{
			World->GetTimerManager().SetTimer(AutoAdvanceTimer, this, &ThisClass::Advance, Slide.AutoAdvanceAfterSeconds, false);
		}
	}
}

void UMelodiaStorySequenceWidget::FinishSequence()
{
	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().ClearTimer(AutoAdvanceTimer);
	}
	UMelodiaStorySequenceData* FinishedSequence = Sequence;
	Sequence = nullptr;
	OnSequenceFinished.Broadcast(FinishedSequence);
}
