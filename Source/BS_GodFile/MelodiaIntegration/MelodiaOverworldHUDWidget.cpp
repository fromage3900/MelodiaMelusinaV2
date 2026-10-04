#include "MelodiaOverworldHUDWidget.h"

#include "Components/ProgressBar.h"
#include "Components/TextBlock.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
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

	// No authority yet for chapter line, title resonance or motif progress: hide, don't fake.
	Hide(ChapterLine);
	Hide(TitleResonance);
	Hide(TitleResonanceText);
	Hide(QuestMotifs);
	Hide(QuestProgress);

	if (const UWorld* World = GetWorld())
	{
		const FText Area = Pretty(UWorld::RemovePIEPrefix(World->GetMapName()), {TEXT("LV_"), TEXT("L_")});
		AreaTitle->SetText(Area);
		AreaName->SetText(FText::FromString(Area.ToString().ToUpper()));
	}
	TitleBlock->SetVisibility(ESlateVisibility::HitTestInvisible);
	CaptionRemaining = AreaCaptionSeconds;
	RefreshAccumulator = 0.0f;

	// Bar fills: default fill was plain white; tint to the parchment/coral vs pearl-blue token pair.
	if (VitalityBar)
	{
		VitalityBar->SetFillColorAndOpacity(FLinearColor(0.90f, 0.42f, 0.44f, 1.0f));
	}
	if (ResonanceBar)
	{
		ResonanceBar->SetFillColorAndOpacity(FLinearColor(0.49f, 0.62f, 0.92f, 1.0f));
	}
}

void UMelodiaOverworldHUDWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);

	if (CaptionRemaining > 0.0f)
	{
		CaptionRemaining -= InDeltaTime;
		TitleBlock->SetRenderOpacity(FMath::Clamp(CaptionRemaining / 0.469f, 0.0f, 1.0f)); // fades over one beat
		if (CaptionRemaining <= 0.0f)
		{
			Hide(TitleBlock);
		}
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
	if (!KeyProp || !ValueProp)
	{
		return;
	}
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
			PlayerName->SetText(Pretty(UnitClass->GetName(), {TEXT("BP_"), TEXT("PlayerUnit"), TEXT("_C")}));
		}
	MaxHP = FMath::Max(MaxHP, HP);
	MaxMP = FMath::Max(MaxMP, MP);
	// Eased bars: interpolate from the currently displayed fill so hits and
	// heals glide instead of snapping. No extra state needed — the bar itself
	// is the memory. RefreshSeconds doubles as the interp delta.
	const float VitalityTarget = MaxHP > 0 ? static_cast<float>(HP) / MaxHP : 0.0f;
	const float ResonanceTarget = MaxMP > 0 ? static_cast<float>(MP) / MaxMP : 0.0f;
	VitalityBar->SetPercent(FMath::FInterpTo(VitalityBar->GetPercent(), VitalityTarget, RefreshSeconds, 4.0f));
	ResonanceBar->SetPercent(FMath::FInterpTo(ResonanceBar->GetPercent(), ResonanceTarget, RefreshSeconds, 4.0f));
		VitalsText->SetText(FText::FromString(FString::Printf(TEXT("VITALITY %d / %d   ·   RESONANCE %d / %d"), HP, MaxHP, MP, MaxMP)));
		// The template's EXP curve isn't data-visible; only claim a level when it is unambiguous.
		PlayerLevel->SetVisibility(Exp == 0 ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
		PlayerLevel->SetText(FText::FromString(TEXT("LEVEL 1")));
		break; // party leader only
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
		Hide(QuestCard);
		return;
	}
	QuestCard->SetVisibility(ESlateVisibility::HitTestInvisible);
	QuestHeader->SetText(FText::FromString(bActive ? TEXT("ACTIVE SCORE") : TEXT("NEW SCORE")));
	QuestTitle->SetText(Shown->DisplayName);
	QuestBody->SetText(Shown->Objective);
}
