#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "MelodiaInputContextSubsystem.h"
#include "MelodiaReactiveCursorWidget.generated.h"

/** Presentation-only base for every software cursor WBP. */
UCLASS(Abstract, Blueprintable)
class BS_GODFILE_API UMelodiaReactiveCursorWidget : public UUserWidget
{
	GENERATED_BODY()

protected:
	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;

	UFUNCTION(BlueprintImplementableEvent, Category = "Melodia|Cursor")
	void ApplyCursorVisualState(const FMelodiaCursorVisualState& VisualState);

private:
	UFUNCTION() void HandleVisualStateChanged(const FMelodiaCursorVisualState& VisualState);
	TWeakObjectPtr<UMelodiaInputContextSubsystem> InputContext;
};
