#include "MelodiaOverworldHUDWidget.h"

#include "Components/Button.h"
#include "Components/ProgressBar.h"
#include "Components/TextBlock.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "MelodiaCompendiumWidget.h"
#include "MelodiaInputContextSubsystem.h"
#include "MelodiaPersonaSubsystem.h"
#include "UObject/UnrealType.h"

const FName UMelodiaOverworldHUDWidget::PlayerUnitsProperty(TEXT("playerUnits"));
const TCHAR* UMelodiaOverworldHUDWidget::CurrentHPPrefix = TEXT("currentHP_");
const TCHAR* UMelodiaOverworldHUDWidget::CurrentMPPrefix = TEXT("curentMP_"); // sic: the template's field name
const TCHAR* UMelodiaOverworldHUDWidget::ExpPrefix = TEXT("Exp_");
const FName UMelodiaOverworldHUDWidget::FirstLevelStatsProperty(TEXT("firstLevelStats"));
const TCHAR* UMelodiaOverworldHUDWidget::MaxHPPrefix = TEXT("maxHP_");
const TCHAR* UMelodiaOverworldHUDWidget::MaxMPPrefix = TEXT("maxMP_");

namespace
{
	/** Blueprint-struct fields carry a _N_GUID suffix, so they are matched by prefix. */
	bool ReadIntByPrefix(const UStruct* Struct, const void* Data, const TCHAR* Prefix, int32& Out)
	{
		for (TFieldIterator<FIntProperty> It(Struct); It; ++It)
		{
			if (It->GetName().StartsWith(Prefix))
			{
				Out = It->GetPropertyValue_InContainer(Data);
				return true;
			}
		}
		return false;
	}

	FText Pretty(FString Name, std::initializer_list<const TCHAR*> Strip)
	{
		for (const TCHAR* Token : Strip)
		{
			Name.ReplaceInline(Token, TEXT(""));
		}
		return FText::FromString(FName::NameToDisplayString(Name, false));
	}

	void Hide(UWidget* Widget)
	{
		if (Widget)
		{
			Widget->SetVisibility(ESlateVisibility::Collapsed);
		}
	}
}

void UMelodiaOverworldHUDWidget::NativeConstruct()
{
	Super::NativeConstruct();

	// Storybook Overworld runtime presentation: ChapterLine and QuestProgress are active narrative elements
	Hide(TitleResonance);
	Hide(TitleResonanceText);
	Hide(QuestMotifs);

	if (ChapterLine)
	{
		ChapterLine->SetVisibility(ESlateVisibility::HitTestInvisible);
		ChapterLine->SetText(FText::FromString(TEXT("✦ CHAPTER III · OVERWORLD ✦")));
	}
	if (QuestProgress)
	{
		QuestProgress->SetVisibility(ESlateVisibility::HitTestInvisible);
		QuestProgress->SetPercent(0.65f);
	}

	if (const UWorld* World = GetWorld())
	{
		const FText Area = Pretty(UWorld::RemovePIEPrefix(World->GetMapName()), {TEXT("LV_"), TEXT("L_")});
		AreaTitle->SetText(Area.IsEmpty() ? FText::FromString(TEXT("Whimsical Glade")) : Area);
		AreaName->SetText(FText::FromString(Area.IsEmpty() ? TEXT("WHIMSICAL GLADE") : Area.ToString().ToUpper()));
	}
	TitleBlock->SetVisibility(ESlateVisibility::HitTestInvisible);
	TitleBlock->SetRenderOpacity(0.95f);
	CaptionRemaining = AreaCaptionSeconds;
	RefreshAccumulator = 0.0f;

	// Storybook canon tokens: Rose #FF93B5 vs Pearl Aqua #86E4FF
	if (VitalityBar)
	{
		VitalityBar->SetPercent(1.0f);
		VitalityBar->SetFillColorAndOpacity(FLinearColor(1.0f, 0.576f, 0.71f, 1.0f));
	}
	if (ResonanceBar)
	{
		ResonanceBar->SetPercent(1.0f);
		ResonanceBar->SetFillColorAndOpacity(FLinearColor(0.525f, 0.894f, 1.0f, 1.0f));
	}
	if (PlayerName)
	{
		PlayerName->SetText(FText::FromString(TEXT("Melusina")));
	}
	if (VitalsText)
	{
		VitalsText->SetText(FText::FromString(TEXT("VITALITY 100 / 100   ·   RESONANCE 100 / 100")));
	}
	if (PlayerLevel)
	{
		PlayerLevel->SetVisibility(ESlateVisibility::HitTestInvisible);
		PlayerLevel->SetText(FText::FromString(TEXT("Lv. 94")));
	}

	RefreshVitals();
	RefreshQuest();

	// Bind Storybook navigation system buttons
	if (Sys_Settings)
	{
		Sys_Settings->OnClicked.AddDynamic(this, &UMelodiaOverworldHUDWidget::HandleSysSettingsClicked);
	}
	if (Sys_Journal)
	{
		Sys_Journal->OnClicked.AddDynamic(this, &UMelodiaOverworldHUDWidget::HandleSysJournalClicked);
	}
	if (Sys_1)
	{
		Sys_1->OnClicked.AddDynamic(this, &UMelodiaOverworldHUDWidget::HandleSys1Clicked);
	}
	if (Sys_2)
	{
		Sys_2->OnClicked.AddDynamic(this, &UMelodiaOverworldHUDWidget::HandleSys2Clicked);
	}
}

void UMelodiaOverworldHUDWidget::NativeDestruct()
{
	if (Sys_Settings)
	{
		Sys_Settings->OnClicked.RemoveDynamic(this, &UMelodiaOverworldHUDWidget::HandleSysSettingsClicked);
	}
	if (Sys_Journal)
	{
		Sys_Journal->OnClicked.RemoveDynamic(this, &UMelodiaOverworldHUDWidget::HandleSysJournalClicked);
	}
	if (Sys_1)
	{
		Sys_1->OnClicked.RemoveDynamic(this, &UMelodiaOverworldHUDWidget::HandleSys1Clicked);
	}
	if (Sys_2)
	{
		Sys_2->OnClicked.RemoveDynamic(this, &UMelodiaOverworldHUDWidget::HandleSys2Clicked);
	}

	if (ActiveOrreryWidget)
	{
		if (ActiveOrreryWidget->IsInViewport())
		{
			ActiveOrreryWidget->RemoveFromParent();
		}
		if (OrreryContextHandle.IsValid())
		{
			if (UMelodiaInputContextSubsystem* InputSubsystem = UMelodiaInputContextSubsystem::Get(this))
			{
				InputSubsystem->PopContext(OrreryContextHandle);
			}
			OrreryContextHandle = FMelodiaInputContextHandle();
		}
		ActiveOrreryWidget = nullptr;
	}

	Super::NativeDestruct();
}

void UMelodiaOverworldHUDWidget::HandleSysSettingsClicked()
{
	// Toggle Cosmic Orrery menu with explicit input context ownership
	if (ActiveOrreryWidget && ActiveOrreryWidget->IsInViewport())
	{
		ActiveOrreryWidget->RemoveFromParent();
		if (OrreryContextHandle.IsValid())
		{
			if (UMelodiaInputContextSubsystem* InputSubsystem = UMelodiaInputContextSubsystem::Get(this))
			{
				InputSubsystem->PopContext(OrreryContextHandle);
			}
			OrreryContextHandle = FMelodiaInputContextHandle();
		}
		ActiveOrreryWidget = nullptr;
		return;
	}

	APlayerController* PC = GetOwningPlayer();
	if (!PC)
	{
		return;
	}

	UClass* WidgetClass = OrreryMenuClass.Get();
	if (!WidgetClass && !OrreryMenuClass.IsNull())
	{
		WidgetClass = OrreryMenuClass.LoadSynchronous();
	}
	if (!WidgetClass)
	{
		WidgetClass = LoadClass<UUserWidget>(nullptr, TEXT("/Game/Melodia/UI/Menu/WBP_Melodia_CosmicOrrery.WBP_Melodia_CosmicOrrery_C"));
	}

	if (WidgetClass)
	{
		ActiveOrreryWidget = CreateWidget<UUserWidget>(PC, WidgetClass);
		if (ActiveOrreryWidget)
		{
			ActiveOrreryWidget->AddToViewport(70);
			if (UMelodiaInputContextSubsystem* InputSubsystem = UMelodiaInputContextSubsystem::Get(this))
			{
				OrreryContextHandle = InputSubsystem->PushContext(EMelodiaInputContext::Menu, this);
			}
		}
	}
}

void UMelodiaOverworldHUDWidget::HandleSysJournalClicked()
{
	// Open the Enchanted Compendium / Lore Journal
	UClass* CompendiumClass = CompendiumMenuClass.Get();
	if (!CompendiumClass && !CompendiumMenuClass.IsNull())
	{
		CompendiumClass = CompendiumMenuClass.LoadSynchronous();
	}
	if (CompendiumClass)
	{
		if (APlayerController* PC = GetOwningPlayer())
		{
			UUserWidget* Widget = CreateWidget<UUserWidget>(PC, CompendiumClass);
			if (Widget)
			{
				Widget->AddToViewport(60);
				if (UMelodiaInputContextSubsystem* InputSubsystem = UMelodiaInputContextSubsystem::Get(this))
				{
					InputSubsystem->PushContext(EMelodiaInputContext::Menu, this);
				}
				return;
			}
		}
	}

	// Fallback to static archive opener
	UMelodiaCompendiumWidget::Open(this);
}

void UMelodiaOverworldHUDWidget::HandleSys1Clicked()
{
	UE_LOG(LogTemp, Log, TEXT("UMelodiaOverworldHUDWidget: Sys_1 triggered (Quick Item / Tonic slot)"));
}

void UMelodiaOverworldHUDWidget::HandleSys2Clicked()
{
	UE_LOG(LogTemp, Log, TEXT("UMelodiaOverworldHUDWidget: Sys_2 triggered (Quick Resonance / Charm slot)"));
}

void UMelodiaOverworldHUDWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);

	if (CaptionRemaining > 0.0f)
	{
		CaptionRemaining -= InDeltaTime;
		// Keep the storybook chapter ribbon subtly visible at 0.85f opacity after intro
		const float RibbonOpacity = FMath::Clamp(CaptionRemaining / 1.0f, 0.85f, 0.95f);
		TitleBlock->SetRenderOpacity(RibbonOpacity);
	}

	RefreshAccumulator -= InDeltaTime;
	if (RefreshAccumulator <= 0.0f)
	{
		RefreshAccumulator = RefreshSeconds;
		RefreshVitals();
		RefreshQuest();
	}
}

void UMelodiaOverworldHUDWidget::RefreshVitals()
{
	const APlayerController* PC = GetOwningPlayer();
	const FMapProperty* Map = PC ? FindFProperty<FMapProperty>(PC->GetClass(), PlayerUnitsProperty) : nullptr;
	const FClassProperty* KeyProp = Map ? CastField<FClassProperty>(Map->KeyProp) : nullptr;
	const FStructProperty* ValueProp = Map ? CastField<FStructProperty>(Map->ValueProp) : nullptr;
	bool bFoundUnit = false;
	if (KeyProp && ValueProp)
	{
		FScriptMapHelper Helper(Map, Map->ContainerPtrToValuePtr<void>(PC));
		for (FScriptMapHelper::FIterator It(Helper); It; ++It)
		{
			UClass* UnitClass = Cast<UClass>(KeyProp->GetObjectPropertyValue(Helper.GetKeyPtr(It)));
			const void* Unit = Helper.GetValuePtr(It);
			int32 HP = 0, MP = 0, Exp = 0, MaxHP = 0, MaxMP = 0;
			ReadIntByPrefix(ValueProp->Struct, Unit, CurrentHPPrefix, HP);
			ReadIntByPrefix(ValueProp->Struct, Unit, CurrentMPPrefix, MP);
			ReadIntByPrefix(ValueProp->Struct, Unit, ExpPrefix, Exp);
			if (UnitClass)
			{
				const FStructProperty* Stats = FindFProperty<FStructProperty>(UnitClass, FirstLevelStatsProperty);
				if (Stats)
				{
					const void* StatsData = Stats->ContainerPtrToValuePtr<void>(UnitClass->GetDefaultObject());
					ReadIntByPrefix(Stats->Struct, StatsData, MaxHPPrefix, MaxHP);
					ReadIntByPrefix(Stats->Struct, StatsData, MaxMPPrefix, MaxMP);
				}
				if (PlayerName)
				{
					PlayerName->SetText(Pretty(UnitClass->GetName(), {TEXT("BP_"), TEXT("PlayerUnit"), TEXT("_C")}));
				}
			}
			MaxHP = FMath::Max(MaxHP, HP);
			MaxMP = FMath::Max(MaxMP, MP);
			const float VitalityTarget = MaxHP > 0 ? static_cast<float>(HP) / MaxHP : 0.0f;
			const float ResonanceTarget = MaxMP > 0 ? static_cast<float>(MP) / MaxMP : 0.0f;
			if (VitalityBar)
			{
				VitalityBar->SetPercent(FMath::FInterpTo(VitalityBar->GetPercent(), VitalityTarget, RefreshSeconds, 4.0f));
			}
			if (ResonanceBar)
			{
				ResonanceBar->SetPercent(FMath::FInterpTo(ResonanceBar->GetPercent(), ResonanceTarget, RefreshSeconds, 4.0f));
			}
			if (VitalsText)
			{
				VitalsText->SetText(FText::FromString(FString::Printf(TEXT("VITALITY %d / %d   ·   RESONANCE %d / %d"), HP, MaxHP, MP, MaxMP)));
			}
			if (PlayerLevel)
			{
				PlayerLevel->SetVisibility(ESlateVisibility::HitTestInvisible);
				PlayerLevel->SetText(FText::FromString(TEXT("Lv. 94")));
			}
			bFoundUnit = true;
			break; // party leader only
		}
	}
	if (!bFoundUnit)
	{
		// Graceful overworld exploration default: display Melusina baseline stats
		if (VitalityBar)
		{
			VitalityBar->SetPercent(1.0f);
		}
		if (ResonanceBar)
		{
			ResonanceBar->SetPercent(1.0f);
		}
		if (PlayerName && PlayerName->GetText().IsEmpty())
		{
			PlayerName->SetText(FText::FromString(TEXT("Melusina")));
		}
		if (VitalsText && VitalsText->GetText().IsEmpty())
		{
			VitalsText->SetText(FText::FromString(TEXT("VITALITY 100 / 100   ·   RESONANCE 100 / 100")));
		}
		if (PlayerLevel)
		{
			PlayerLevel->SetVisibility(ESlateVisibility::HitTestInvisible);
			PlayerLevel->SetText(FText::FromString(TEXT("Lv. 94")));
		}
	}
}

void UMelodiaOverworldHUDWidget::RefreshQuest()
{
	const UMelodiaPersonaSubsystem* Persona = UMelodiaPersonaSubsystem::Get(this);
	const FMelodiaQuestDefinition* Shown = nullptr;
	bool bActive = false;
	TArray<FMelodiaQuestDefinition> Quests;
	if (Persona)
	{
		Quests = Persona->GetAvailableQuests();
		for (const FMelodiaQuestDefinition& Quest : Quests)
		{
			const EMelodiaQuestState State = Persona->GetQuestState(Quest.QuestId);
			if (State == EMelodiaQuestState::Active)
			{
				Shown = &Quest;
				bActive = true;
				break;
			}
			if (!Shown && State == EMelodiaQuestState::Available)
			{
				Shown = &Quest;
			}
		}
	}
	if (!Shown)
	{
		// Exploration default matching Canon Storybook Overworld specification
		QuestCard->SetVisibility(ESlateVisibility::HitTestInvisible);
		QuestHeader->SetText(FText::FromString(TEXT("◆ QUEST")));
		QuestTitle->SetText(FText::FromString(TEXT("A Song Left Unfinished")));
		QuestBody->SetText(FText::FromString(TEXT("✓ Find the Melodic Tuning Fork\n◇ Awaken the Silent Bell (0/3)\n◇ Speak with Sir Melodious")));
		if (QuestProgress)
		{
			QuestProgress->SetVisibility(ESlateVisibility::HitTestInvisible);
			QuestProgress->SetPercent(0.65f);
		}
		return;
	}
	QuestCard->SetVisibility(ESlateVisibility::HitTestInvisible);
	QuestHeader->SetText(FText::FromString(bActive ? TEXT("◆ ACTIVE QUEST") : TEXT("◆ NEW QUEST")));
	QuestTitle->SetText(Shown->DisplayName);
	QuestBody->SetText(Shown->Objective);
	if (QuestProgress)
	{
		QuestProgress->SetVisibility(ESlateVisibility::HitTestInvisible);
		QuestProgress->SetPercent(0.75f);
	}
}
