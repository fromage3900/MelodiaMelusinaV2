#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Components/Button.h"
#include "MelodiaPersonaTypes.h"
#include "MelodiaCompendiumWidget.generated.h"

class UPanelWidget;
class UTextBlock;
class UMelodiaCompendiumWidget;

/** A thread tab or entry row. Carries its payload so one handler serves every button. */
UCLASS()
class BS_GODFILE_API UMelodiaCompendiumChoice final : public UButton
{
	GENERATED_BODY()

public:
	void Init(UMelodiaCompendiumWidget* InOwner, bool bInIsCategory, EMelodiaCompendiumCategory InCategory, FName InEntryId);

private:
	UFUNCTION()
	void HandleClicked();

	TWeakObjectPtr<UMelodiaCompendiumWidget> Owner;
	bool bIsCategory = false;
	EMelodiaCompendiumCategory Category = EMelodiaCompendiumCategory::Character;
	FName EntryId;
};

/**
 * The Enchanted Compendium (Figma Storybook "02.1 Archive Index" + entry prototypes). Reads
 * UMelodiaPersonaSubsystem's Compendium only; owns no unlock state. Opens with the Motion Grammar
 * (Unseal the page, Bloom the entry). Layout comes from WBP_MelodiaCompendium via BindWidget.
 */
UCLASS(Abstract)
class BS_GODFILE_API UMelodiaCompendiumWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	/** Creates WBP_MelodiaCompendium for the first local player, focuses it, and returns it. */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Compendium", meta = (WorldContext = "WorldContextObject"))
	static UMelodiaCompendiumWidget* Open(UObject* WorldContextObject);

	UFUNCTION(BlueprintCallable, Category = "Melodia|Compendium")
	void Close();

	UFUNCTION(BlueprintCallable, Category = "Melodia|Compendium")
	void SelectCategory(EMelodiaCompendiumCategory Category);

	UFUNCTION(BlueprintCallable, Category = "Melodia|Compendium")
	void SelectEntry(FName EntryId);

	UFUNCTION(BlueprintPure, Category = "Melodia|Compendium")
	FName GetSelectedEntryId() const { return SelectedEntryId; }

	UFUNCTION(BlueprintPure, Category = "Melodia|Compendium")
	int32 GetListedEntryCount() const { return ListedEntries; }

protected:
	virtual void NativeConstruct() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;
	virtual FReply NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent) override;

	UPROPERTY(meta = (BindWidget)) TObjectPtr<UPanelWidget> ThreadRow;
	UPROPERTY(meta = (BindWidget)) TObjectPtr<UPanelWidget> EntryList;
	UPROPERTY(meta = (BindWidget)) TObjectPtr<UWidget> EntryPage;
	UPROPERTY(meta = (BindWidget)) TObjectPtr<UTextBlock> EntryKicker;
	UPROPERTY(meta = (BindWidget)) TObjectPtr<UTextBlock> EntryTitle;
	UPROPERTY(meta = (BindWidget)) TObjectPtr<UTextBlock> EntrySubtitle;
	UPROPERTY(meta = (BindWidget)) TObjectPtr<UTextBlock> EntrySummary;
	UPROPERTY(meta = (BindWidget)) TObjectPtr<UTextBlock> EntryMusical;
	UPROPERTY(meta = (BindWidget)) TObjectPtr<UTextBlock> EntryFieldNote;
	UPROPERTY(meta = (BindWidget)) TObjectPtr<UButton> BtnClose;

	UPROPERTY(EditAnywhere, Category = "Melodia|Compendium")
	float BPM = 128.0f;

private:
	UFUNCTION()
	void HandleCloseClicked();

	UMelodiaCompendiumChoice* MakeChoice(UPanelWidget* Parent, const FText& Label, int32 FontSize, const FLinearColor& Color, bool bEnabled);

	FName SelectedEntryId;
	EMelodiaCompendiumCategory SelectedCategory = EMelodiaCompendiumCategory::Character;
	int32 ListedEntries = 0;
	float OpenedAt = 0.0f;
	float EntryShownAt = 0.0f;
};
