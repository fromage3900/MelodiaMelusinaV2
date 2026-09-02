#include "MelodiaReactiveCursorWidget.h"

void UMelodiaReactiveCursorWidget::NativeConstruct()
{
	Super::NativeConstruct();
	SetVisibility(ESlateVisibility::HitTestInvisible);
	InputContext = UMelodiaInputContextSubsystem::Get(this);
	if (InputContext.IsValid())
	{
		InputContext->OnCursorVisualStateChanged.AddUniqueDynamic(this, &ThisClass::HandleVisualStateChanged);
		HandleVisualStateChanged(InputContext->GetCursorVisualState());
	}
}

void UMelodiaReactiveCursorWidget::NativeDestruct()
{
	if (InputContext.IsValid())
	{
		InputContext->OnCursorVisualStateChanged.RemoveDynamic(this, &ThisClass::HandleVisualStateChanged);
	}
	InputContext.Reset();
	Super::NativeDestruct();
}

void UMelodiaReactiveCursorWidget::HandleVisualStateChanged(const FMelodiaCursorVisualState& VisualState)
{
	ApplyCursorVisualState(VisualState);
}
