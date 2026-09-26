#include "MelodiaCompendiumWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Components/PanelWidget.h"
#include "Components/TextBlock.h"
#include "Engine/Font.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "MelodiaMotionGrammar.h"
#include "MelodiaPersonaSubsystem.h"

namespace
{
	const TCHAR* WidgetClassPath = TEXT("/Game/Melodia/UI/Compendium/WBP_MelodiaCompendium.WBP_MelodiaCompendium_C");
	const TCHAR* FontPath = TEXT("/Game/Melodia/UI/Fonts/F_Melodia_UI.F_Melodia_UI");
	const FLinearColor CompendiumPearl(0.96f, 0.93f, 0.90f, 1.0f);
	const FLinearColor CompendiumGold(0.79f, 0.66f, 0.42f, 1.0f);
	const FLinearColor CompendiumCyan(0.62f, 0.91f, 0.97f, 1.0f);
	const FLinearColor CompendiumMute(0.55f, 0.60f, 0.72f, 0.8f);

	// Archive Index order and labels (Figma 02.1): three main threads, then the rest.
	const EMelodiaCompendiumCategory ThreadOrder[] = {
		EMelodiaCompendiumCategory::Character, EMelodiaCompendiumCategory::Place, EMelodiaCompendiumCategory::Instrument,
		EMelodiaCompendiumCategory::Relic, EMelodiaCompendiumCategory::Song, EMelodiaCompendiumCategory::MotifCreature,
		EMelodiaCompendiumCategory::Phenomenon};

	FText ThreadLabel(const EMelodiaCompendiumCategory Category)
	{
		switch (Category)
		{
		case EMelodiaCompendiumCategory::Character: return FText::FromString(TEXT("CHARACTERS"));
		case EMelodiaCompendiumCategory::Place: return FText::FromString(TEXT("WORLDS"));
		case EMelodiaCompendiumCategory::Instrument: return FText::FromString(TEXT("INSTRUMENTS"));
		case EMelodiaCompendiumCategory::Relic: return FText::FromString(TEXT("RELICS"));
		case EMelodiaCompendiumCategory::Song: return FText::FromString(TEXT("SONGS"));
		case EMelodiaCompendiumCategory::MotifCreature: return FText::FromString(TEXT("CREATURES"));
		default: return FText::FromString(TEXT("PHENOMENA"));
		}
	}

	FText EntryKickerText(const EMelodiaCompendiumCategory Category)
	{
		switch (Category)
		{
		case EMelodiaCompendiumCategory::Character: return FText::FromString(TEXT("CHARACTER ENTRY"));
		case EMelodiaCompendiumCategory::Place: return FText::FromString(TEXT("WORLD ENTRY"));
		case EMelodiaCompendiumCategory::Instrument: return FText::FromString(TEXT("INSTRUMENT ENTRY"));
		default: return FText::FromString(ThreadLabel(Category).ToString() + TEXT(" ENTRY"));
		}
	}

	float Now(const UObject* Context)
	{
		const UWorld* World = Context ? Context->GetWorld() : nullptr;
		return World ? World->GetRealTimeSeconds() : 0.0f;
	}
}

void UMelodiaCompendiumChoice::Init(UMelodiaCompendiumWidget* InOwner, const bool bInIsCategory, const EMelodiaCompendiumCategory InCategory, const FName InEntryId)
{
	Owner = InOwner;
	bIsCategory = bInIsCategory;
	Category = InCategory;
	EntryId = InEntryId;
	OnClicked.AddUniqueDynamic(this, &UMelodiaCompendiumChoice::HandleClicked);
}

void UMelodiaCompendiumChoice::HandleClicked()
{
	if (UMelodiaCompendiumWidget* Widget = Owner.Get())
	{
		if (bIsCategory)
		{
			Widget->SelectCategory(Category);
		}
		else
		{
			Widget->SelectEntry(EntryId);
		}
	}
}

UMelodiaCompendiumWidget* UMelodiaCompendiumWidget::Open(UObject* WorldContextObject)
{
	APlayerController* PC = UGameplayStatics::GetPlayerController(WorldContextObject, 0);
	UClass* WidgetClass = LoadClass<UMelodiaCompendiumWidget>(nullptr, WidgetClassPath);
	if (!PC || !WidgetClass)
	{
		UE_LOG(LogTemp, Warning, TEXT("MELODIA_COMPENDIUM cannot open (pc=%d class=%d)"), PC != nullptr, WidgetClass != nullptr);
		return nullptr;
	}
	UMelodiaCompendiumWidget* Widget = CreateWidget<UMelodiaCompendiumWidget>(PC, WidgetClass);
	if (Widget)
	{
		Widget->AddToViewport(60);
		FInputModeGameAndUI Mode;
		Mode.SetWidgetToFocus(Widget->TakeWidget());
		PC->SetInputMode(Mode);
		PC->SetShowMouseCursor(true);
		Widget->SetKeyboardFocus();
	}
	return Widget;
}

void UMelodiaCompendiumWidget::Close()
{
	if (APlayerController* PC = GetOwningPlayer())
	{
		PC->SetInputMode(FInputModeGameOnly());
		PC->SetShowMouseCursor(false);
	}
	RemoveFromParent();
}

void UMelodiaCompendiumWidget::HandleCloseClicked()
{
	Close();
}

UMelodiaCompendiumChoice* UMelodiaCompendiumWidget::MakeChoice(UPanelWidget* Parent, const FText& Label, const int32 FontSize,
	const FLinearColor& Color, const bool bEnabled)
{
	UMelodiaCompendiumChoice* Choice = WidgetTree->ConstructWidget<UMelodiaCompendiumChoice>();
	FButtonStyle Style = Choice->GetStyle();
	Style.Normal.TintColor = FSlateColor(FLinearColor(0.08f, 0.10f, 0.20f, 0.0f));
	Style.Hovered.TintColor = FSlateColor(FLinearColor(0.62f, 0.91f, 0.97f, 0.12f));
	Style.Pressed.TintColor = FSlateColor(FLinearColor(0.62f, 0.91f, 0.97f, 0.22f));
	Style.Disabled.TintColor = FSlateColor(FLinearColor(0.0f, 0.0f, 0.0f, 0.0f));
	Choice->SetStyle(Style);
	Choice->SetIsEnabled(bEnabled);

	UTextBlock* Text = WidgetTree->ConstructWidget<UTextBlock>();
	Text->SetText(Label);
	FSlateFontInfo Font = Text->GetFont();
	if (UFont* UIFont = LoadObject<UFont>(nullptr, FontPath))
	{
		Font.FontObject = UIFont;
	}
	Font.Size = FontSize;
	Text->SetFont(Font);
	Text->SetColorAndOpacity(FSlateColor(bEnabled ? Color : CompendiumMute));
	Choice->AddChild(Text);
	Parent->AddChild(Choice);
	return Choice;
}

void UMelodiaCompendiumWidget::NativeConstruct()
{
	Super::NativeConstruct();
	SetIsFocusable(true);
	BtnClose->OnClicked.AddUniqueDynamic(this, &UMelodiaCompendiumWidget::HandleCloseClicked);
	OpenedAt = Now(this);

	const UMelodiaPersonaSubsystem* Persona = UMelodiaPersonaSubsystem::Get(this);
	ThreadRow->ClearChildren();
	bool bSelected = false;
	for (const EMelodiaCompendiumCategory Category : ThreadOrder)
	{
		const int32 Count = Persona ? Persona->GetCompendiumEntriesByCategory(Category, false).Num() : 0;
		MakeChoice(ThreadRow, ThreadLabel(Category), 13, CompendiumGold, Count > 0)->Init(this, true, Category, NAME_None);
		if (!bSelected && Count > 0)
		{
			bSelected = true;
			SelectCategory(Category);
		}
	}
	if (!bSelected)
	{
		EntryPage->SetVisibility(ESlateVisibility::Hidden);
	}
	UE_LOG(LogTemp, Log, TEXT("MELODIA_COMPENDIUM opened entries=%d"), Persona ? Persona->GetCompendiumEntries(false).Num() : 0);
}

void UMelodiaCompendiumWidget::SelectCategory(const EMelodiaCompendiumCategory Category)
{
	SelectedCategory = Category;
	EntryList->ClearChildren();
	ListedEntries = 0;
	const UMelodiaPersonaSubsystem* Persona = UMelodiaPersonaSubsystem::Get(this);
	if (!Persona)
	{
		return;
	}
	FName First;
	for (const FMelodiaCompendiumEntry& Entry : Persona->GetCompendiumEntriesByCategory(Category, false))
	{
		const bool bUnlocked = Persona->IsCompendiumEntryUnlocked(Entry.EntryId);
		// Locked entries stay visible as a silhouette -- the archive promises what it holds.
		MakeChoice(EntryList, bUnlocked ? Entry.DisplayName : FText::FromString(TEXT("✧  · · ·")), 20, CompendiumPearl, bUnlocked)
			->Init(this, false, Category, Entry.EntryId);
		++ListedEntries;
		if (First.IsNone() && bUnlocked)
		{
			First = Entry.EntryId;
		}
	}
	if (!First.IsNone())
	{
		SelectEntry(First);
	}
}

void UMelodiaCompendiumWidget::SelectEntry(const FName EntryId)
{
	const UMelodiaPersonaSubsystem* Persona = UMelodiaPersonaSubsystem::Get(this);
	FMelodiaCompendiumEntry Entry;
	if (!Persona || !Persona->GetCompendiumEntry(EntryId, Entry) || !Persona->IsCompendiumEntryUnlocked(EntryId))
	{
		return;
	}
	SelectedEntryId = EntryId;
	EntryPage->SetVisibility(ESlateVisibility::SelfHitTestInvisible);
	EntryKicker->SetText(EntryKickerText(Entry.Category));
	EntryTitle->SetText(Entry.DisplayName);
	EntrySubtitle->SetText(Entry.Subtitle);
	EntrySummary->SetText(Entry.Summary);
	EntryMusical->SetText(Entry.MusicalIdentity);
	EntryFieldNote->SetText(Entry.FieldNote.IsEmpty() ? FText::GetEmpty()
		: FText::FromString(FString::Printf(TEXT("“%s”"), *Entry.FieldNote.ToString())));
	EntryShownAt = Now(this);
}

void UMelodiaCompendiumWidget::NativeTick(const FGeometry& MyGeometry, const float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);
	const float T = Now(this);
	// The book unseals as a whole; each entry page blooms on its own when chosen.
	SetRenderOpacity(UMelodiaMotionGrammarLibrary::GetStageProgress(EMelodiaMotionStage::Unseal, T - OpenedAt, BPM));
	const float Bloom = UMelodiaMotionGrammarLibrary::GetStageProgress(EMelodiaMotionStage::Bloom, T - EntryShownAt, BPM);
	EntryPage->SetRenderOpacity(FMath::Clamp(Bloom, 0.0f, 1.0f));
	EntryPage->SetRenderScale(FVector2D(0.94f + 0.06f * Bloom));
}

FReply UMelodiaCompendiumWidget::NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent)
{
	if (InKeyEvent.GetKey() == EKeys::Escape || InKeyEvent.GetKey() == EKeys::Gamepad_FaceButton_Right)
	{
		Close();
		return FReply::Handled();
	}
	return Super::NativeOnKeyDown(InGeometry, InKeyEvent);
}
