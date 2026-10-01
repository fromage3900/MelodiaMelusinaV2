// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "SALSSaveSlotPicker.h"

#include "ALSSaveGameSettings.h"
#include "ALSSaveInfo.h"
#include "HAL/FileManager.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/ConfigCacheIni.h"
#include "Misc/Paths.h"
#include "UnrealEdGlobals.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Text/STextBlock.h"

#define LOCTEXT_NAMESPACE "SALSSaveSlotPicker"

const TCHAR*  SALSSaveSlotPicker::ConfigSection   = TEXT("AscentSaveSystem.PIEOverride");
const FString SALSSaveSlotPicker::NewGameSentinel = TEXT("__ACF_NEW_GAME__");

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

FString SALSSaveSlotPicker::ShortMapName(const FString& FullPath)
{
	if (FullPath.IsEmpty())
	{
		return FString();
	}
	// Strip everything up to the last '/' or '.' to get the bare asset name.
	FString Result = FullPath;
	int32 Idx;
	if (Result.FindLastChar(TEXT('/'), Idx))
	{
		Result = Result.RightChop(Idx + 1);
	}
	if (Result.FindLastChar(TEXT('.'), Idx))
	{
		Result = Result.Left(Idx);
	}
	return Result;
}

FString SALSSaveSlotPicker::FormatPlayTime(int32 Seconds)
{
	if (Seconds <= 0)
	{
		return FString();
	}
	const int32 Hours   = Seconds / 3600;
	const int32 Minutes = (Seconds % 3600) / 60;
	if (Hours > 0)
	{
		return FString::Printf(TEXT("%dh %02dm"), Hours, Minutes);
	}
	return FString::Printf(TEXT("%dm"), Minutes);
}

void SALSSaveSlotPicker::BuildDisplayStrings(
	const FString&   SlotName,
	const FString&   Description,
	const FString&   MapToLoad,
	const FDateTime& SaveDate,
	int32            PlayTimeSecs,
	FString&         OutDisplay,
	FString&         OutTooltip)
{
	const FString Title     = Description.IsEmpty() ? SlotName : Description;
	const FString MapShort  = ShortMapName(MapToLoad);
	const FString DateShort = SaveDate.ToString(TEXT("%d/%m/%y  %H:%M"));
	const FString PlayStr   = FormatPlayTime(PlayTimeSecs);

	// Single-line display: "Title  •  MapName  •  DD/MM/YY HH:MM"
	TArray<FString> Parts;
	Parts.Add(Title);
	if (!MapShort.IsEmpty())  Parts.Add(MapShort);
	Parts.Add(DateShort);

	OutDisplay = FString::Join(Parts, TEXT("  \u2022  "));   // bullet separator

	// Full tooltip with all available info
	OutTooltip = FString::Printf(
		TEXT("Slot:  %s\nMap:  %s\nDate:  %s"),
		*SlotName,
		*(!MapToLoad.IsEmpty() ? MapToLoad : TEXT("-")),
		*SaveDate.ToString(TEXT("%A %d %B %Y,  %H:%M:%S")));

	if (!Description.IsEmpty())
	{
		OutTooltip = FString::Printf(TEXT("Description:  %s\n"), *Description) + OutTooltip;
	}
	if (!PlayStr.IsEmpty())
	{
		OutTooltip += FString::Printf(TEXT("\nPlay time:  %s"), *PlayStr);
	}
}

// ─────────────────────────────────────────────────────────────────────────────
// Widget construction
// ─────────────────────────────────────────────────────────────────────────────

void SALSSaveSlotPicker::Construct(const FArguments& InArgs)
{
	RefreshSlotList();
	LoadCurrentSelection();

	ChildSlot
	[
		SNew(SHorizontalBox)

		// ACF label
		+ SHorizontalBox::Slot()
		.AutoWidth()
		.VAlign(VAlign_Center)
		.Padding(FMargin(6.f, 0.f, 4.f, 0.f))
		[
			SNew(STextBlock)
			.Text(LOCTEXT("Label", "ACF Save Slot:"))
			.ToolTipText(LOCTEXT("LabelTooltip",
				"ACF Save System — choose which save slot to load at the next Play In Editor.\n"
				"\"New Game\" starts a fresh session with no data loaded."))
		]

		// Combo-box
		+ SHorizontalBox::Slot()
		.AutoWidth()
		.VAlign(VAlign_Center)
		[
			SNew(SBox)
			.MinDesiredWidth(200.f)
			[
				SAssignNew(ComboBox, FSlotCombo)
				.OptionsSource(&SlotOptions)
				.OnSelectionChanged(this, &SALSSaveSlotPicker::OnSelectionChanged)
				.OnGenerateWidget(this, &SALSSaveSlotPicker::GenerateSlotWidget)
				.OnComboBoxOpening(this, &SALSSaveSlotPicker::OnComboBoxOpening)
				.ContentPadding(FMargin(4.f, 2.f))
				[
					SNew(STextBlock)
					.Text(this, &SALSSaveSlotPicker::GetSelectedText)
				]
			]
		]

		// Refresh button
		+ SHorizontalBox::Slot()
		.AutoWidth()
		.VAlign(VAlign_Center)
		.Padding(FMargin(2.f, 0.f, 4.f, 0.f))
		[
			SNew(SButton)
			.ButtonStyle(FAppStyle::Get(), "SimpleButton")
			.ContentPadding(FMargin(4.f, 2.f))
			.ToolTipText(LOCTEXT("RefreshTooltip", "Rescan Saved/SaveGames and reload save metadata."))
			.OnClicked(this, &SALSSaveSlotPicker::OnRefreshClicked)
			[
				SNew(STextBlock)
				.Text(FText::FromString(TEXT("\u21BA")))   // ↺
			]
		]
	];
}

// ─────────────────────────────────────────────────────────────────────────────
// Slot scanning + metadata loading
// ─────────────────────────────────────────────────────────────────────────────

void SALSSaveSlotPicker::RefreshSlotList()
{
	SlotOptions.Reset();

	// First entry is always "New Game"
	{
		TSharedPtr<FALSPIESlotEntry> NewGame = MakeShared<FALSPIESlotEntry>();
		NewGame->SlotName    = NewGameSentinel;
		NewGame->DisplayText = TEXT("New Game");
		NewGame->TooltipText = TEXT("Start a fresh PIE session without loading any save file.");
		SlotOptions.Add(NewGame);
	}

	const UALSSaveGameSettings* SaveSettings = GetDefault<UALSSaveGameSettings>();
	const FString MetaSlot   = SaveSettings ? SaveSettings->GetSaveMetadataName() : TEXT("SaveMetadata");
	const FString TravelSlot = SaveSettings ? SaveSettings->GetTravelSaveName()   : TEXT("TempSave");

	// Load the metadata index from disk (no world context needed for this call).
	const UALSSaveInfo* SaveInfo = Cast<UALSSaveInfo>(
		UGameplayStatics::LoadGameFromSlot(MetaSlot, 0));

	// Enumerate .sav files
	const FString SaveDir = FPaths::ProjectSavedDir() / TEXT("SaveGames");
	TArray<FString> Files;
	IFileManager::Get().FindFiles(Files, *(SaveDir / TEXT("*.sav")), true, false);
	Files.Sort();

	for (const FString& File : Files)
	{
		const FString SlotName = FPaths::GetBaseFilename(File);
		if (SlotName == MetaSlot || SlotName == TravelSlot)
		{
			continue;
		}

		TSharedPtr<FALSPIESlotEntry> Entry = MakeShared<FALSPIESlotEntry>();
		Entry->SlotName = SlotName;

		// Try to enrich with metadata
		FALSSaveMetadata Meta;
		if (SaveInfo && SaveInfo->TryGetSaveSlotData(SlotName, Meta))
		{
			BuildDisplayStrings(
				SlotName,
				Meta.SaveDescription,
				Meta.MapToLoad,
				Meta.Data,
				Meta.PlayTime,
				Entry->DisplayText,
				Entry->TooltipText);
		}
		else
		{
			// No metadata on record – at least show the slot name clearly
			Entry->DisplayText = SlotName;
			Entry->TooltipText = FString::Printf(TEXT("Slot: %s\n(no metadata found)"), *SlotName);
		}

		SlotOptions.Add(Entry);
	}
}

void SALSSaveSlotPicker::LoadCurrentSelection()
{
	bool    bNewGame = true;
	FString SavedSlot;

	GConfig->GetBool(ConfigSection,   TEXT("PIENewGame"),   bNewGame,  GEditorPerProjectIni);
	GConfig->GetString(ConfigSection, TEXT("PIESlotName"),  SavedSlot, GEditorPerProjectIni);

	const FString TargetSlot = (bNewGame || SavedSlot.IsEmpty()) ? NewGameSentinel : SavedSlot;
	SelectedEntry = FindEntryBySlotName(TargetSlot);

	// Fall back to "New Game" if the saved slot no longer exists on disk
	if (!SelectedEntry.IsValid() && SlotOptions.Num() > 0)
	{
		SelectedEntry = SlotOptions[0];
	}

	if (ComboBox.IsValid())
	{
		ComboBox->SetSelectedItem(SelectedEntry);
	}
}

SALSSaveSlotPicker::FSlotEntry SALSSaveSlotPicker::FindEntryBySlotName(const FString& SlotName) const
{
	for (const FSlotEntry& Entry : SlotOptions)
	{
		if (Entry.IsValid() && Entry->SlotName == SlotName)
		{
			return Entry;
		}
	}
	return nullptr;
}

// ─────────────────────────────────────────────────────────────────────────────
// Combo-box callbacks
// ─────────────────────────────────────────────────────────────────────────────

void SALSSaveSlotPicker::OnComboBoxOpening()
{
	RefreshSlotList();

	if (ComboBox.IsValid())
	{
		ComboBox->RefreshOptions();

		// Keep the previous selection if still available
		const FString PrevSlot = SelectedEntry.IsValid() ? SelectedEntry->SlotName : NewGameSentinel;
		SelectedEntry = FindEntryBySlotName(PrevSlot);
		if (!SelectedEntry.IsValid() && SlotOptions.Num() > 0)
		{
			SelectedEntry = SlotOptions[0];
		}
		ComboBox->SetSelectedItem(SelectedEntry);
	}
}

void SALSSaveSlotPicker::OnSelectionChanged(FSlotEntry NewItem, ESelectInfo::Type /*SelectInfo*/)
{
	if (!NewItem.IsValid())
	{
		return;
	}

	SelectedEntry = NewItem;
	const bool bNewGame = (NewItem->SlotName == NewGameSentinel);

	GConfig->SetBool(ConfigSection,   TEXT("PIENewGame"),  bNewGame, GEditorPerProjectIni);
	GConfig->SetString(ConfigSection, TEXT("PIESlotName"), bNewGame ? TEXT("") : *NewItem->SlotName,
	                                                                   GEditorPerProjectIni);
	GConfig->Flush(false, GEditorPerProjectIni);
}

TSharedRef<SWidget> SALSSaveSlotPicker::GenerateSlotWidget(FSlotEntry Item) const
{
	if (!Item.IsValid())
	{
		return SNew(STextBlock).Text(FText::GetEmpty());
	}

	return SNew(STextBlock)
		.Text(FText::FromString(Item->DisplayText))
		.ToolTipText(FText::FromString(Item->TooltipText));
}

FReply SALSSaveSlotPicker::OnRefreshClicked()
{
	RefreshSlotList();
	LoadCurrentSelection();
	return FReply::Handled();
}

FText SALSSaveSlotPicker::GetSelectedText() const
{
	if (SelectedEntry.IsValid())
	{
		return FText::FromString(SelectedEntry->DisplayText);
	}
	return LOCTEXT("NoSelection", "New Game");
}

#undef LOCTEXT_NAMESPACE
