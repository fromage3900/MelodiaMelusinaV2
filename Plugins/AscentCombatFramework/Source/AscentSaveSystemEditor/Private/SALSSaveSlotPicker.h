// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/Input/SComboBox.h"

/**
 * Data held for each entry in the PIE save-slot combo-box.
 *
 * SlotName    – the actual .sav file name used by the save system at runtime.
 * DisplayText – human-readable label built from FALSSaveMetadata (description,
 *               map, date, playtime).  Falls back to SlotName when no metadata
 *               is available.
 * TooltipText – full detail line shown on mouse hover.
 */
struct FALSPIESlotEntry
{
	FString SlotName;
	FString DisplayText;
	FString TooltipText;
};

/**
 * Toolbar combo-box that lets the developer choose which ACF save slot
 * (or "New Game") should be loaded automatically at the next PIE session.
 *
 * Meaningful labels are built from FALSSaveMetadata: description, map name,
 * date/time and playtime.  The selection is persisted to GEditorPerProjectIni
 * (per-machine, not committed to VCS).
 */
class SALSSaveSlotPicker : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SALSSaveSlotPicker) {}
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);

	/** Rescans Saved/SaveGames and reloads metadata to rebuild the option list. */
	void RefreshSlotList();

	/** Reads the persisted selection from the editor config and syncs the combo. */
	void LoadCurrentSelection();

private:
	using FSlotEntry  = TSharedPtr<FALSPIESlotEntry>;
	using FSlotCombo  = SComboBox<FSlotEntry>;

	/** Returns the entry whose SlotName matches the given string, or nullptr. */
	FSlotEntry FindEntryBySlotName(const FString& SlotName) const;

	/** Refreshes list + restores selection just before the drop-down opens. */
	void OnComboBoxOpening();

	/** Persists the new selection to config when the user picks an entry. */
	void OnSelectionChanged(FSlotEntry NewItem, ESelectInfo::Type SelectInfo);

	/** Builds the row widget shown for each entry in the open drop-down. */
	TSharedRef<SWidget> GenerateSlotWidget(FSlotEntry Item) const;

	FReply OnRefreshClicked();

	/** Collapsed-button text (display name of the current selection). */
	FText GetSelectedText() const;

	/** Builds a display string + tooltip from metadata fields. */
	static void BuildDisplayStrings(
		const FString&  SlotName,
		const FString&  Description,
		const FString&  MapToLoad,
		const FDateTime& SaveDate,
		int32            PlayTimeSecs,
		FString&         OutDisplay,
		FString&         OutTooltip);

	/** Extracts the short asset name from a full UE asset path or plain name. */
	static FString ShortMapName(const FString& FullPath);

	/** Formats playtime seconds as "Xh YYm". */
	static FString FormatPlayTime(int32 Seconds);

	TArray<FSlotEntry> SlotOptions;
	FSlotEntry         SelectedEntry;

	TSharedPtr<FSlotCombo> ComboBox;

	static const TCHAR*  ConfigSection;
	static const FString NewGameSentinel;
};
