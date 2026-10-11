#include "MelodiaOverworldHUDWidget.h"

#include "Camera/PlayerCameraManager.h"
#include "Components/Button.h"
#include "Components/Image.h"
#include "Components/ProgressBar.h"
#include "Components/TextBlock.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "MelodiaCompendiumWidget.h"
#include "MelodiaCosmicOrreryWidget.h"
#include "MelodiaInputContextSubsystem.h"
#include "MelodiaMusicClockSubsystem.h"
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

	SetIsFocusable(true);

	// Storybook Overworld runtime presentation: ChapterLine and QuestProgress are active narrative elements
	Hide(TitleResonance);
	Hide(TitleResonanceText);
	Hide(QuestMotifs);

	if (ChapterLine)
	{
		ChapterLine->SetVisibility(ESlateVisibility::HitTestInvisible);
		ChapterLine->SetText(FText::FromString(TEXT("\u25C6 CHAPTER III \u00B7 OVERWORLD \u25C6")));
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
		Sys_Settings->OnHovered.AddDynamic(this, &UMelodiaOverworldHUDWidget::HandleSysSettingsHovered);
		Sys_Settings->OnUnhovered.AddDynamic(this, &UMelodiaOverworldHUDWidget::HandleSysSettingsUnhovered);
		Sys_Settings->SetRenderTransformPivot(FVector2D(0.5f, 0.5f));
	}
	if (Sys_Journal)
	{
		Sys_Journal->OnClicked.AddDynamic(this, &UMelodiaOverworldHUDWidget::HandleSysJournalClicked);
		Sys_Journal->OnHovered.AddDynamic(this, &UMelodiaOverworldHUDWidget::HandleSysJournalHovered);
		Sys_Journal->OnUnhovered.AddDynamic(this, &UMelodiaOverworldHUDWidget::HandleSysJournalUnhovered);
		Sys_Journal->SetRenderTransformPivot(FVector2D(0.5f, 0.5f));
	}
	if (Sys_1)
	{
		Sys_1->OnClicked.AddDynamic(this, &UMelodiaOverworldHUDWidget::HandleSys1Clicked);
		Sys_1->OnHovered.AddDynamic(this, &UMelodiaOverworldHUDWidget::HandleSys1Hovered);
		Sys_1->OnUnhovered.AddDynamic(this, &UMelodiaOverworldHUDWidget::HandleSys1Unhovered);
		Sys_1->SetRenderTransformPivot(FVector2D(0.5f, 0.5f));
	}
	if (Sys_2)
	{
		Sys_2->OnClicked.AddDynamic(this, &UMelodiaOverworldHUDWidget::HandleSys2Clicked);
		Sys_2->OnHovered.AddDynamic(this, &UMelodiaOverworldHUDWidget::HandleSys2Hovered);
		Sys_2->OnUnhovered.AddDynamic(this, &UMelodiaOverworldHUDWidget::HandleSys2Unhovered);
		Sys_2->SetRenderTransformPivot(FVector2D(0.5f, 0.5f));
	}

	if (Minimap_NorthStar)
	{
		Minimap_NorthStar->SetRenderTransformPivot(FVector2D(0.5f, 0.5f));
	}
}

void UMelodiaOverworldHUDWidget::NativeDestruct()
{
	if (Sys_Settings)
	{
		Sys_Settings->OnClicked.RemoveDynamic(this, &UMelodiaOverworldHUDWidget::HandleSysSettingsClicked);
		Sys_Settings->OnHovered.RemoveDynamic(this, &UMelodiaOverworldHUDWidget::HandleSysSettingsHovered);
		Sys_Settings->OnUnhovered.RemoveDynamic(this, &UMelodiaOverworldHUDWidget::HandleSysSettingsUnhovered);
	}
	if (Sys_Journal)
	{
		Sys_Journal->OnClicked.RemoveDynamic(this, &UMelodiaOverworldHUDWidget::HandleSysJournalClicked);
		Sys_Journal->OnHovered.RemoveDynamic(this, &UMelodiaOverworldHUDWidget::HandleSysJournalHovered);
		Sys_Journal->OnUnhovered.RemoveDynamic(this, &UMelodiaOverworldHUDWidget::HandleSysJournalUnhovered);
	}
	if (Sys_1)
	{
		Sys_1->OnClicked.RemoveDynamic(this, &UMelodiaOverworldHUDWidget::HandleSys1Clicked);
		Sys_1->OnHovered.RemoveDynamic(this, &UMelodiaOverworldHUDWidget::HandleSys1Hovered);
		Sys_1->OnUnhovered.RemoveDynamic(this, &UMelodiaOverworldHUDWidget::HandleSys1Unhovered);
	}
	if (Sys_2)
	{
		Sys_2->OnClicked.RemoveDynamic(this, &UMelodiaOverworldHUDWidget::HandleSys2Clicked);
		Sys_2->OnHovered.RemoveDynamic(this, &UMelodiaOverworldHUDWidget::HandleSys2Hovered);
		Sys_2->OnUnhovered.RemoveDynamic(this, &UMelodiaOverworldHUDWidget::HandleSys2Unhovered);
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

void UMelodiaOverworldHUDWidget::OpenOrreryWithArchetype(int32 ArchetypeIndex)
{
	if (ActiveOrreryWidget && ActiveOrreryWidget->IsInViewport())
	{
		if (UMelodiaCosmicOrreryWidget* Orrery = Cast<UMelodiaCosmicOrreryWidget>(ActiveOrreryWidget))
		{
			if (Orrery->GetFocusedArchetypeIndex() == ArchetypeIndex)
			{
				if (MenuCloseSound)
				{
					UGameplayStatics::PlaySound2D(this, MenuCloseSound);
				}
				Orrery->CloseOrrery();
				ActiveOrreryWidget = nullptr;
				return;
			}
			Orrery->SetFocusedArchetypeIndex(ArchetypeIndex);
			return;
		}
	}

	if (ButtonClickSound)
	{
		UGameplayStatics::PlaySound2D(this, ButtonClickSound);
	}
	if (MenuOpenSound)
	{
		UGameplayStatics::PlaySound2D(this, MenuOpenSound);
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
	if (!WidgetClass)
	{
		WidgetClass = UMelodiaCosmicOrreryWidget::StaticClass();
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
				if (UMelodiaCosmicOrreryWidget* Orrery = Cast<UMelodiaCosmicOrreryWidget>(ActiveOrreryWidget))
				{
					Orrery->SetContextHandle(OrreryContextHandle);
					Orrery->SetFocusedArchetypeIndex(ArchetypeIndex);
					Orrery->OnOrreryClosed.AddDynamic(this, &UMelodiaOverworldHUDWidget::HandleOrreryClosed);
				}
			}
		}
	}
}

void UMelodiaOverworldHUDWidget::HandleOrreryClosed()
{
	ActiveOrreryWidget = nullptr;
	OrreryContextHandle = FMelodiaInputContextHandle();
}

FReply UMelodiaOverworldHUDWidget::NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent)
{
	const FKey Key = InKeyEvent.GetKey();
	if (Key == EKeys::M)
	{
		OpenOrreryWithArchetype(4); // Map
		return FReply::Handled();
	}
	if (Key == EKeys::J)
	{
		OpenOrreryWithArchetype(3); // Journal
		return FReply::Handled();
	}
	if (Key == EKeys::P || Key == EKeys::C)
	{
		OpenOrreryWithArchetype(0); // Party
		return FReply::Handled();
	}
	if (Key == EKeys::Tab)
	{
		OpenOrreryWithArchetype(6); // Settings / Orrery
		return FReply::Handled();
	}

	return Super::NativeOnKeyDown(InGeometry, InKeyEvent);
}

void UMelodiaOverworldHUDWidget::HandleSysSettingsClicked()
{
	OpenOrreryWithArchetype(6);
}

void UMelodiaOverworldHUDWidget::HandleSysJournalClicked()
{
	OpenOrreryWithArchetype(3);
}

void UMelodiaOverworldHUDWidget::HandleSys1Clicked()
{
	OpenOrreryWithArchetype(0);
}

void UMelodiaOverworldHUDWidget::HandleSys2Clicked()
{
	OpenOrreryWithArchetype(4);
}

void UMelodiaOverworldHUDWidget::HandleSysSettingsHovered()
{
	bSysSettingsHovered = true;
	if (ButtonHoverSound)
	{
		UGameplayStatics::PlaySound2D(this, ButtonHoverSound);
	}
}

void UMelodiaOverworldHUDWidget::HandleSysSettingsUnhovered()
{
	bSysSettingsHovered = false;
}

void UMelodiaOverworldHUDWidget::HandleSysJournalHovered()
{
	bSysJournalHovered = true;
	if (ButtonHoverSound)
	{
		UGameplayStatics::PlaySound2D(this, ButtonHoverSound);
	}
}

void UMelodiaOverworldHUDWidget::HandleSysJournalUnhovered()
{
	bSysJournalHovered = false;
}

void UMelodiaOverworldHUDWidget::HandleSys1Hovered()
{
	bSys1Hovered = true;
	if (ButtonHoverSound)
	{
		UGameplayStatics::PlaySound2D(this, ButtonHoverSound);
	}
}

void UMelodiaOverworldHUDWidget::HandleSys1Unhovered()
{
	bSys1Hovered = false;
}

void UMelodiaOverworldHUDWidget::HandleSys2Hovered()
{
	bSys2Hovered = true;
	if (ButtonHoverSound)
	{
		UGameplayStatics::PlaySound2D(this, ButtonHoverSound);
	}
}

void UMelodiaOverworldHUDWidget::HandleSys2Unhovered()
{
	bSys2Hovered = false;
}

void UMelodiaOverworldHUDWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);

	RunningTime += InDeltaTime;

	// Query ambient musical pulse from Music Clock
	float MusicPulse = 0.0f;
	if (UMelodiaMusicClockSubsystem* Clock = UMelodiaMusicClockSubsystem::Get(this))
	{
		MusicPulse = UMelodiaMusicClockSubsystem::GetMusicPulse(this);
	}

	// 1. Dynamic Minimap Compass Orientation & Starlight Twinkle
	if (Minimap_NorthStar)
	{
		float CamYaw = 0.0f;
		if (const APlayerController* PC = GetOwningPlayer())
		{
			if (PC->PlayerCameraManager)
			{
				CamYaw = PC->PlayerCameraManager->GetCameraRotation().Yaw;
			}
			else
			{
				CamYaw = PC->GetControlRotation().Yaw;
			}
		}
		// Rotate North Star so it points to true North in camera-relative space
		Minimap_NorthStar->SetRenderTransformAngle(-CamYaw);

		// Starlight shimmer (subtle sine oscillation layered with musical pulse)
		const float TwinkleSine = FMath::Sin(RunningTime * 2.8f) * 0.15f + 0.85f;
		const float TwinkleOpacity = FMath::Clamp(TwinkleSine + 0.2f * MusicPulse, 0.7f, 1.0f);
		Minimap_NorthStar->SetRenderOpacity(TwinkleOpacity);
	}

	// 2. Minimap Bezel gentle breathing emissive / opacity modulation
	if (Minimap_Bezel)
	{
		const float BezelPulse = FMath::Sin(RunningTime * 1.5f) * 0.06f + 0.94f;
		const float BezelOpacity = FMath::Clamp(BezelPulse + 0.12f * MusicPulse, 0.85f, 1.0f);
		Minimap_Bezel->SetRenderOpacity(BezelOpacity);
	}

	// 3. Buoyant world-prompt hovering
	if (InteractPrompt && InteractPrompt->GetVisibility() != ESlateVisibility::Collapsed && InteractPrompt->GetVisibility() != ESlateVisibility::Hidden)
	{
		FWidgetTransform Transform = InteractPrompt->GetRenderTransform();
		Transform.Translation.Y = FMath::Sin(RunningTime * 3.2f) * 3.5f;
		InteractPrompt->SetRenderTransform(Transform);
	}

	// 4. Smooth Button Hover Scaling (1.08x)
	auto UpdateButtonScale = [InDeltaTime](UButton* Btn, bool bHovered, float& HoverAlpha)
	{
		if (!Btn) return;
		const float TargetAlpha = bHovered ? 1.0f : 0.0f;
		HoverAlpha = FMath::FInterpTo(HoverAlpha, TargetAlpha, InDeltaTime, 12.0f);
		const float Scale = FMath::Lerp(1.0f, 1.08f, HoverAlpha);
		FWidgetTransform Xform = Btn->GetRenderTransform();
		Xform.Scale = FVector2D(Scale, Scale);
		Btn->SetRenderTransform(Xform);
	};
	UpdateButtonScale(Sys_Settings, bSysSettingsHovered, SysSettingsHoverAlpha);
	UpdateButtonScale(Sys_Journal, bSysJournalHovered, SysJournalHoverAlpha);
	UpdateButtonScale(Sys_1, bSys1Hovered, Sys1HoverAlpha);
	UpdateButtonScale(Sys_2, bSys2Hovered, Sys2HoverAlpha);

	// 5. Low-Vitality Rose Heartbeat Pulse (when HP < 35%)
	if (CachedVitalityPercent < 0.35f && VitalityBar)
	{
		const float HeartbeatFreq = 5.0f;
		const float Lub = FMath::Max(0.0f, FMath::Sin(RunningTime * HeartbeatFreq));
		const float Dub = FMath::Max(0.0f, FMath::Sin((RunningTime - 0.18f) * HeartbeatFreq));
		const float Pulse = Lub * 0.6f + Dub * 0.4f;
		VitalityBar->SetRenderOpacity(0.85f + 0.35f * Pulse);
	}
	else if (VitalityBar)
	{
		VitalityBar->SetRenderOpacity(1.0f);
	}

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
			CachedVitalityPercent = VitalityTarget;
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
		CachedVitalityPercent = 1.0f;
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
		QuestHeader->SetText(FText::FromString(TEXT("\u25C6 QUEST")));
		QuestTitle->SetText(FText::FromString(TEXT("A Song Left Unfinished")));
		QuestBody->SetText(FText::FromString(TEXT("\u2713 Find the Melodic Tuning Fork\n\u25C7 Awaken the Silent Bell (0/3)\n\u25C7 Speak with Sir Melodious")));
		if (QuestProgress)
		{
			QuestProgress->SetVisibility(ESlateVisibility::HitTestInvisible);
			QuestProgress->SetPercent(0.65f);
		}
		return;
	}
	QuestCard->SetVisibility(ESlateVisibility::HitTestInvisible);
	QuestHeader->SetText(FText::FromString(bActive ? TEXT("\u25C6 ACTIVE QUEST") : TEXT("\u25C6 NEW QUEST")));
	QuestTitle->SetText(Shown->DisplayName);
	QuestBody->SetText(Shown->Objective);
	if (QuestProgress)
	{
		QuestProgress->SetVisibility(ESlateVisibility::HitTestInvisible);
		QuestProgress->SetPercent(0.75f);
	}
}
