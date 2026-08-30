#pragma once

#include "CoreMinimal.h"
#include "Widgets/BackgroundBox.h"
#include "Widgets/DialogBox.h"
#include "Widgets/SelectionBox.h"
#include "MelodiaInputContextSubsystem.h"
#include "MelodiaQuillPresentationWidgets.generated.h"

class UButton;
class UImage;
class UTextBlock;
class UVerticalBox;
class UMelodiaQuillSelectionWidget;

/** Native Quill dialogue adapter. Visual composition remains in its child WBP. */
UCLASS(Blueprintable)
class BS_GODFILE_API UMelodiaQuillDialogWidget : public UDialogBox
{
	GENERATED_BODY()

public:
	virtual void Play_Implementation(
		const FString& Speaker,
		const FText& Text,
		const TArray<FString>& Tags) override;

protected:
	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;
	virtual FReply NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent) override;
	virtual FReply NativeOnMouseButtonDown(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent) override;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional), Category = "Melodia|Quill")
	TObjectPtr<UTextBlock> SpeakerText;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional), Category = "Melodia|Quill")
	TObjectPtr<UTextBlock> BodyText;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional), Category = "Melodia|Quill")
	TObjectPtr<UButton> AdvanceButton;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Quill")
	TArray<FString> ActiveTags;

private:
	UFUNCTION()
	void HandleAdvanceClicked();

	void TryAdvance();
	void EnsureDialogueContext();
	void ReleaseDialogueContext();
	bool bAdvanceConsumed = false;
	FMelodiaInputContextHandle DialogueContextHandle;
};

/** One dynamically-created option row. Its child WBP supplies the SoftMG skin. */
UCLASS(Blueprintable)
class BS_GODFILE_API UMelodiaQuillChoiceEntryWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	void InitializeOption(
		UMelodiaQuillSelectionWidget* InOwner,
		int32 InOptionIndex,
		const FEvaluatedOption& InOption);

	UFUNCTION(BlueprintPure, Category = "Melodia|Quill")
	bool IsOptionEnabled() const { return bOptionEnabled; }

	/** Places keyboard/gamepad focus on the actual interactive button. */
	void FocusOption();

protected:
	virtual void NativeConstruct() override;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional), Category = "Melodia|Quill")
	TObjectPtr<UButton> ChoiceButton;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional), Category = "Melodia|Quill")
	TObjectPtr<UTextBlock> ChoiceText;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Quill")
	TArray<FString> OptionTags;

private:
	UFUNCTION()
	void HandleClicked();

	void ApplyOptionState();

	UPROPERTY(Transient)
	TObjectPtr<UMelodiaQuillSelectionWidget> OwnerSelection;

	int32 OptionIndex = INDEX_NONE;
	bool bOptionEnabled = false;
	FText OptionText;
};

/** Native Quill selection adapter that always returns the original FStatement. */
UCLASS(Blueprintable)
class BS_GODFILE_API UMelodiaQuillSelectionWidget : public USelectionBox
{
	GENERATED_BODY()

public:
	virtual void Play_Implementation(const TArray<FEvaluatedOption>& Options) override;

	void SelectOption(int32 OptionIndex);

protected:
	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;
	virtual FReply NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent) override;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional), Category = "Melodia|Quill")
	TObjectPtr<UVerticalBox> OptionsBox;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Melodia|Quill")
	TSubclassOf<UMelodiaQuillChoiceEntryWidget> ChoiceEntryClass;

private:
	void EnsureDialogueContext();
	void ReleaseDialogueContext();
	bool FocusOptionAt(int32 OptionIndex);
	bool MoveChoiceFocus(int32 Direction);

	UPROPERTY(Transient)
	TArray<FEvaluatedOption> ActiveOptions;

	UPROPERTY(Transient)
	TMap<int32, TObjectPtr<UMelodiaQuillChoiceEntryWidget>> CreatedEntries;

	int32 FocusedOptionIndex = INDEX_NONE;
	bool bSelectionConsumed = false;
	FMelodiaInputContextHandle DialogueContextHandle;
};

/** Native Quill background adapter that bypasses the plugin's viewport-condition bug. */
UCLASS(Blueprintable)
class BS_GODFILE_API UMelodiaQuillBackgroundWidget : public UBackgroundBox
{
	GENERATED_BODY()

public:
	virtual void Play_Implementation(
		const UTexture* NewImage,
		const FString& Transition,
		float Duration) override;

protected:
	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional), Category = "Melodia|Quill")
	TObjectPtr<UImage> BackgroundImage;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Quill")
	FString ActiveTransition;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Quill")
	float ActiveTransitionDuration = 0.0f;

private:
	UPROPERTY(Transient)
	TObjectPtr<UTexture> PresentedImage;
};
