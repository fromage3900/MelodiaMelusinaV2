#include "MelodiaCalibrationWidget.h"

#include "Blueprint/WidgetBlueprintLibrary.h"
#include "Engine/Font.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "MelodiaGameUserSettings.h"
#include "Sound/SoundBase.h"
#include "Styling/CoreStyle.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
	const FLinearColor Night(0.043f, 0.035f, 0.125f, 0.94f);
	const FLinearColor Pearl(0.96f, 0.93f, 0.90f, 1.0f);
	const FLinearColor Rose(0.91f, 0.71f, 0.63f, 1.0f);
	const FLinearColor Lavender(0.73f, 0.65f, 0.94f, 1.0f);
	const FLinearColor Cyan(0.62f, 0.91f, 0.97f, 1.0f);
	constexpr double LeadInSeconds = 1.0;
	constexpr int32 MinimumTaps = 4;
}

UMelodiaCalibrationWidget::UMelodiaCalibrationWidget(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
	static ConstructorHelpers::FObjectFinder<USoundBase> Tick(TEXT("/Game/Audio/tick_001.tick_001"));
	static ConstructorHelpers::FObjectFinder<USoundBase> Accent(TEXT("/Game/Audio/click_001.click_001"));
	static ConstructorHelpers::FObjectFinder<UFont> UIFont(TEXT("/Game/Melodia/UI/Fonts/F_Melodia_UI.F_Melodia_UI"));
	ClickSound = Tick.Object;
	AccentSound = Accent.Object;
	Font = UIFont.Object;
	SetIsFocusable(true);
}

UMelodiaCalibrationWidget* UMelodiaCalibrationWidget::Open(UObject* WorldContextObject)
{
	APlayerController* PC = UGameplayStatics::GetPlayerController(WorldContextObject, 0);
	if (!PC)
	{
		return nullptr;
	}
	UMelodiaCalibrationWidget* Widget = CreateWidget<UMelodiaCalibrationWidget>(PC, StaticClass());
	if (Widget)
	{
		Widget->AddToViewport(200);
		FInputModeGameAndUI Mode;
		Mode.SetWidgetToFocus(Widget->TakeWidget());
		PC->SetInputMode(Mode);
		Widget->SetKeyboardFocus();
	}
	return Widget;
}

void UMelodiaCalibrationWidget::NativeConstruct()
{
	Super::NativeConstruct();
	Restart();
}

void UMelodiaCalibrationWidget::Restart()
{
	State = EState::Running;
	StartTime = FPlatformTime::Seconds() + LeadInSeconds;
	LastClickTime = -1.0;
	ClicksPlayed = 0;
	ClickTimes.Reset();
	TapLagsMs.Reset();
	MeasuredOffsetMs = 0.0f;
}

void UMelodiaCalibrationWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);
	if (State != EState::Running)
	{
		return;
	}
	const double Now = FPlatformTime::Seconds();
	const double Interval = 60.0 / FMath::Max(BPM, 1.0f);
	if (ClicksPlayed < ClickCount && Now >= StartTime + ClicksPlayed * Interval)
	{
		USoundBase* Sound = (ClicksPlayed % 4 == 0 && AccentSound) ? AccentSound.Get() : ClickSound.Get();
		if (Sound)
		{
			UGameplayStatics::PlaySound2D(this, Sound);
		}
		// The reference is when the click was issued: the lag we measure is exactly the audio + input latency.
		ClickTimes.Add(Now);
		LastClickTime = Now;
		++ClicksPlayed;
	}
	else if (ClicksPlayed >= ClickCount && Now > LastClickTime + Interval * 0.6)
	{
		Finish();
	}
}

void UMelodiaCalibrationWidget::RegisterTap()
{
	if (State != EState::Running || ClickTimes.Num() == 0)
	{
		return;
	}
	const double Now = FPlatformTime::Seconds();
	const double Interval = 60.0 / FMath::Max(BPM, 1.0f);
	int32 Nearest = 0;
	for (int32 Index = 1; Index < ClickTimes.Num(); ++Index)
	{
		if (FMath::Abs(ClickTimes[Index] - Now) < FMath::Abs(ClickTimes[Nearest] - Now))
		{
			Nearest = Index;
		}
	}
	const double LagSeconds = Now - ClickTimes[Nearest];
	if (Nearest >= WarmupClicks && FMath::Abs(LagSeconds) < Interval * 0.5)
	{
		TapLagsMs.Add(static_cast<float>(LagSeconds * 1000.0));
	}
}

void UMelodiaCalibrationWidget::Finish()
{
	State = EState::Result;
	if (TapLagsMs.Num() >= MinimumTaps)
	{
		TArray<float> Sorted = TapLagsMs;
		Sorted.Sort();
		MeasuredOffsetMs = Sorted[Sorted.Num() / 2];
	}
	UE_LOG(LogTemp, Log, TEXT("MELODIA_CALIBRATION taps=%d median=%.1fms"), TapLagsMs.Num(), MeasuredOffsetMs);
}

void UMelodiaCalibrationWidget::ApplyAndClose()
{
	if (TapLagsMs.Num() >= MinimumTaps)
	{
		if (UMelodiaGameUserSettings* Settings = UMelodiaGameUserSettings::Get())
		{
			Settings->CalibrationOffsetMs = MeasuredOffsetMs;
			Settings->ApplyMelodiaPreferences(this);
			UE_LOG(LogTemp, Log, TEXT("MELODIA_CALIBRATION applied offset=%.1fms"), MeasuredOffsetMs);
		}
	}
	if (APlayerController* PC = GetOwningPlayer())
	{
		PC->SetInputMode(FInputModeGameOnly());
	}
	RemoveFromParent();
}

FReply UMelodiaCalibrationWidget::NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent)
{
	const FKey Key = InKeyEvent.GetKey();
	if (Key == EKeys::Escape || Key == EKeys::Gamepad_FaceButton_Right)
	{
		if (APlayerController* PC = GetOwningPlayer())
		{
			PC->SetInputMode(FInputModeGameOnly());
		}
		RemoveFromParent();
		return FReply::Handled();
	}
	const bool bConfirm = Key == EKeys::SpaceBar || Key == EKeys::Enter || Key == EKeys::Gamepad_FaceButton_Bottom;
	if (State == EState::Running && bConfirm)
	{
		RegisterTap();
		return FReply::Handled();
	}
	if (State == EState::Result)
	{
		if (Key == EKeys::R || Key == EKeys::Gamepad_FaceButton_Top)
		{
			Restart();
			return FReply::Handled();
		}
		if (bConfirm)
		{
			ApplyAndClose();
			return FReply::Handled();
		}
	}
	return Super::NativeOnKeyDown(InGeometry, InKeyEvent);
}

int32 UMelodiaCalibrationWidget::NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
	FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const
{
	const int32 SuperLayer = Super::NativePaint(Args, AllottedGeometry, MyCullingRect, OutDrawElements, LayerId, InWidgetStyle, bParentEnabled);
	FPaintContext Context(AllottedGeometry, MyCullingRect, OutDrawElements, SuperLayer, InWidgetStyle, bParentEnabled);
	const FVector2D Size = AllottedGeometry.GetLocalSize();
	if (Size.X < 2.0f || !Font)
	{
		return SuperLayer;
	}

	// DrawBox with no brush asset draws nothing; use the engine white brush for the backdrop.
	FSlateDrawElement::MakeBox(OutDrawElements, ++Context.MaxLayer, AllottedGeometry.ToPaintGeometry(),
		FCoreStyle::Get().GetBrush(TEXT("WhiteBrush")), ESlateDrawEffect::None, Night);
	const FVector2D Center(Size.X * 0.5f, Size.Y * 0.44f);

	// The pulse: a ring that flares on each click and decays over an eighth note.
	const double Since = LastClickTime > 0.0 ? FPlatformTime::Seconds() - LastClickTime : 10.0;
	const float Pulse = FMath::Exp(-static_cast<float>(Since) * 9.0f);
	const bool bAccent = ClicksPlayed > 0 && (ClicksPlayed - 1) % 4 == 0;
	const float Radius = 70.0f + 26.0f * Pulse;
	TArray<FVector2D> Ring;
	for (int32 Index = 0; Index <= 64; ++Index)
	{
		const float Angle = Index * 2.0f * PI / 64.0f;
		Ring.Add(Center + FVector2D(FMath::Cos(Angle), FMath::Sin(Angle)) * Radius);
	}
	FLinearColor RingColor = FMath::Lerp(Lavender, bAccent ? Rose : Cyan, Pulse);
	UWidgetBlueprintLibrary::DrawLines(Context, Ring, RingColor, true, 2.0f + 4.0f * Pulse);

	auto Text = [&](const FString& Line, float Y, int32 SizePx, const FLinearColor& Color)
	{
		const float ApproxWidth = Line.Len() * SizePx * 0.5f;
		UWidgetBlueprintLibrary::DrawTextFormatted(Context, FText::FromString(Line),
			FVector2D(Center.X - ApproxWidth * 0.5f, Y), Font, SizePx, NAME_None, Color);
	};
	Text(TEXT("TIMING CALIBRATION"), Size.Y * 0.14f, 14, Rose);
	if (State == EState::Running)
	{
		Text(TEXT("Tap SPACE on every click"), Size.Y * 0.20f, 30, Pearl);
		const int32 Measured = FMath::Max(0, ClicksPlayed - WarmupClicks);
		Text(ClicksPlayed <= WarmupClicks ? FString(TEXT("listen...")) : FString::Printf(TEXT("%d / %d"), Measured, ClickCount - WarmupClicks),
			Size.Y * 0.66f, 18, Lavender);
	}
	else if (TapLagsMs.Num() >= MinimumTaps)
	{
		Text(FString::Printf(TEXT("You land %.0f ms %s"), FMath::Abs(MeasuredOffsetMs), MeasuredOffsetMs >= 0.0f ? TEXT("late") : TEXT("early")),
			Size.Y * 0.20f, 30, Pearl);
		Text(TEXT("ENTER  apply      R  retry      ESC  cancel"), Size.Y * 0.66f, 16, Lavender);
	}
	else
	{
		Text(TEXT("Not enough taps to measure"), Size.Y * 0.20f, 30, Pearl);
		Text(TEXT("R  retry      ESC  cancel"), Size.Y * 0.66f, 16, Lavender);
	}
	return Context.MaxLayer;
}
